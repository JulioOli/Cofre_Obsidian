"""Consolida gastos do relatório Mutirão Exames por credor e Centro de Custo (CARGA FOPA)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import pdfplumber

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT / "04-Notebooks" / "Utitlities") not in sys.path:
    sys.path.insert(0, str(ROOT / "04-Notebooks" / "Utitlities"))

from premio_total_por_colaborador import (  # noqa: E402
    find_best_match,
    load_centro_custo,
    normalize_name,
)

PDF_PATH = ROOT / "02-Referencias" / "RELATORIO G3S COMERCIO E INDUSTRIA MUTIRÃO EXAMES.pdf"
CARGA_PATH = ROOT / "02-Referencias" / "FOPA" / "CARGA FOPA - MAI2026.xlsx"
OUTPUT_PATH = ROOT / "02-Referencias" / "mutirao_exames_por_credor_cc_MAI2026.xlsx"

CREDOR = "MUTIRÃO EXAMES"
CONTA_SUGERIDA = "7.3.4"
CONTA_DESCRICAO = "EXAMES MÉDICOS"

FILIAL_CNPJ_RE = re.compile(
    r"Funcion[aá]rios e Exames da Unidade:.*\(CNPJ:\s*([\d./-]+)\)",
    flags=re.IGNORECASE,
)
TOTAL_FUNC_RE = re.compile(
    r"Valor Total do Funcion[aá]rio:\s+(.+?)\s+([\d.,]+)$",
    flags=re.IGNORECASE,
)


def parse_brl(value: str) -> float:
    text = str(value).strip()
    if "," in text:
        return float(text.replace(".", "").replace(",", "."))
    return float(text)


def load_exames_pdf(pdf_path: Path) -> pd.DataFrame:
    lines: list[str] = []
    with pdfplumber.open(pdf_path) as document:
        for page in document.pages:
            lines.extend((page.extract_text() or "").split("\n"))

    current_cnpj: str | None = None
    rows: list[dict[str, object]] = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        filial_match = FILIAL_CNPJ_RE.search(line)
        if filial_match:
            current_cnpj = filial_match.group(1)
            continue

        total_match = TOTAL_FUNC_RE.match(line)
        if total_match:
            nome = total_match.group(1).strip().upper()
            valor = parse_brl(total_match.group(2))
            rows.append(
                {
                    "nome": nome,
                    "valor_total": valor,
                    "cnpj_filial": current_cnpj,
                    "credor": CREDOR,
                    "nome_norm": normalize_name(nome),
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=["nome", "valor_total", "cnpj_filial", "credor", "nome_norm"]
        )

    frame = pd.DataFrame(rows)
    return frame.sort_values(["nome_norm", "valor_total"]).drop_duplicates(
        subset=["nome_norm"], keep="first"
    ).reset_index(drop=True)


def consolidar(exames: pd.DataFrame, carga: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    usados: set[str] = set()
    consolidado_rows: list[dict[str, object]] = []
    sem_cc_rows: list[dict[str, object]] = []

    for _, row in exames.iterrows():
        match_norm, metodo, score = find_best_match(
            str(row["nome_norm"]), carga, usados
        )
        if match_norm is None:
            sem_cc_rows.append(
                {
                    "credor": row["credor"],
                    "nome": row["nome"],
                    "valor_total": row["valor_total"],
                    "cnpj_filial": row["cnpj_filial"],
                    "conta_sugerida": CONTA_SUGERIDA,
                    "conta_descricao": CONTA_DESCRICAO,
                    "motivo": "sem correspondência na CARGA",
                }
            )
            continue

        carga_row = carga.loc[carga["nome_norm"] == match_norm].iloc[0]
        usados.add(match_norm)
        consolidado_rows.append(
            {
                "credor": row["credor"],
                "nome": row["nome"],
                "nome_carga": carga_row["funcionario"],
                "valor_total": row["valor_total"],
                "centro_custo": carga_row["centro_custo"],
                "cc_codigo": carga_row["cc_codigo"],
                "cc_descricao": carga_row["cc_descricao"],
                "conta_sugerida": CONTA_SUGERIDA,
                "conta_descricao": CONTA_DESCRICAO,
                "cnpj_filial": row["cnpj_filial"],
                "metodo_match": metodo,
                "score_match": round(score, 4),
            }
        )

    consolidado = pd.DataFrame(consolidado_rows)
    sem_cc = pd.DataFrame(sem_cc_rows)
    return consolidado, sem_cc, usados


def build_por_credor_cc(consolidado: pd.DataFrame) -> pd.DataFrame:
    if consolidado.empty:
        return pd.DataFrame(
            columns=[
                "credor",
                "cc_codigo",
                "cc_descricao",
                "centro_custo",
                "qtd_colaboradores",
                "valor_total",
                "conta_sugerida",
                "conta_descricao",
            ]
        )

    grouped = (
        consolidado.groupby(
            ["credor", "cc_codigo", "cc_descricao", "centro_custo"],
            dropna=False,
            as_index=False,
        )
        .agg(
            qtd_colaboradores=("nome", "count"),
            valor_total=("valor_total", "sum"),
        )
        .sort_values(["credor", "cc_codigo"])
    )
    grouped["conta_sugerida"] = CONTA_SUGERIDA
    grouped["conta_descricao"] = CONTA_DESCRICAO
    grouped["valor_total"] = grouped["valor_total"].round(2)
    return grouped[
        [
            "credor",
            "cc_codigo",
            "cc_descricao",
            "centro_custo",
            "qtd_colaboradores",
            "valor_total",
            "conta_sugerida",
            "conta_descricao",
        ]
    ]


def build_resumo(
    exames: pd.DataFrame,
    consolidado: pd.DataFrame,
    sem_cc: pd.DataFrame,
    por_credor_cc: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"metrica": "Colaboradores no relatório PDF", "valor": len(exames)},
            {"metrica": "Matches com Centro de Custo", "valor": len(consolidado)},
            {"metrica": "Sem Centro de Custo", "valor": len(sem_cc)},
            {
                "metrica": "Linhas agregadas (Credor x CC)",
                "valor": len(por_credor_cc),
            },
            {
                "metrica": "Soma valor consolidado (R$)",
                "valor": round(consolidado["valor_total"].sum(), 2),
            },
            {
                "metrica": "Soma valor extraído PDF (R$)",
                "valor": round(exames["valor_total"].sum(), 2),
            },
            {"metrica": "Credor", "valor": CREDOR},
            {"metrica": "Conta sugerida", "valor": f"{CONTA_SUGERIDA} - {CONTA_DESCRICAO}"},
        ]
    )


def main() -> None:
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF não encontrado: {PDF_PATH}")
    if not CARGA_PATH.exists():
        raise FileNotFoundError(f"CARGA não encontrada: {CARGA_PATH}")

    exames = load_exames_pdf(PDF_PATH)
    carga = load_centro_custo(CARGA_PATH)
    consolidado, sem_cc, _ = consolidar(exames, carga)
    por_credor_cc = build_por_credor_cc(consolidado)
    resumo = build_resumo(exames, consolidado, sem_cc, por_credor_cc)

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        por_credor_cc.to_excel(writer, sheet_name="Por Credor e CC", index=False)
        consolidado.sort_values(["cc_codigo", "nome"]).to_excel(
            writer, sheet_name="Consolidado", index=False
        )
        sem_cc.sort_values("nome").to_excel(writer, sheet_name="Sem CC", index=False)
        resumo.to_excel(writer, sheet_name="Resumo", index=False)

    print(f"Arquivo gerado: {OUTPUT_PATH}")
    print(resumo.to_string(index=False))


if __name__ == "__main__":
    main()
