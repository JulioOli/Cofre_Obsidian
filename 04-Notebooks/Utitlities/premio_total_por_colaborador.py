"""Consolida Prêmio Total (seguro de vida) por colaborador com Centro de Custo da CARGA FOPA."""
from __future__ import annotations

import difflib
import re
import unicodedata
from pathlib import Path

import pandas as pd
import pdfplumber

ROOT = Path(__file__).resolve().parent.parent.parent
FOPA_DIR = ROOT / "02-Referencias" / "FOPA"
PDF_DIR = FOPA_DIR / "relacao_colaboladores"
CARGA_PATH = FOPA_DIR / "CARGA FOPA - MAI2026.xlsx"
OUTPUT_PATH = FOPA_DIR / "premio_total_por_colaborador_MAI2026.xlsx"

FUZZY_CUTOFF = 0.88
TOKEN_MATCH_MIN = 3


DOCUMENT_ID_PATTERNS: list[tuple[str, str]] = [
    (r"FATURA\s*[:\-]\s*([A-Z0-9./-]+)", "fatura"),
    (r"T[IÍ]TULO\s*[:\-]\s*([A-Z0-9./-]+)", "titulo"),
    (r"BOLETO\s*[:\-]\s*([A-Z0-9./-]+)", "boleto"),
    (r"NOSSO\s+N[UÚ]MERO\s*[:\-]\s*([A-Z0-9./-]+)", "nosso_numero"),
    (r"N[UÚ]MERO\s+DO\s+DOCUMENTO\s*[:\-]\s*([A-Z0-9./-]+)", "documento"),
]


def normalize_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.upper().split())


def reverse_name_tokens(lines: list[str]) -> str:
    words: list[str] = []
    for line in lines:
        for token in line.split():
            words.append(token[::-1])
    words.reverse()
    return " ".join(words)


def parse_annex_page(lines: list[str]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    seen: set[tuple[str, float, str | None]] = set()
    index = 0

    while index < len(lines):
        line = lines[index]
        if (
            line == "00,0"
            and index + 1 < len(lines)
            and re.fullmatch(r"\d{2},\d{2}", lines[index + 1])
        ):
            premio = float(lines[index + 1][::-1].replace(",", "."))
            cursor = index + 2
            dates: list[str] = []
            name_lines: list[str] = []
            proposal: str | None = None

            while cursor < len(lines):
                current = lines[cursor]
                if re.fullmatch(r"\d{4}/\d{2}/\d{2}", current):
                    dates.append(current)
                elif len(dates) >= 2 and re.fullmatch(r"\d{10,}.*", current):
                    proposal = current.split()[0]
                    break
                elif len(dates) >= 2:
                    if current != "-" and not re.fullmatch(r"[\d.,]+", current):
                        name_lines.append(current)
                elif current == "00,0":
                    break
                cursor += 1

            if name_lines:
                name = reverse_name_tokens(name_lines).upper()
                key = (normalize_name(name), premio, proposal)
                if key not in seen:
                    seen.add(key)
                    records.append(
                        {
                            "nome": name,
                            "premio_total": premio,
                            "proposta": proposal,
                        }
                    )
            index = cursor
        elif "latoT" in line:
            break
        else:
            index += 1

    return records


def parse_premios_pdf(pdf_path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []

    with pdfplumber.open(pdf_path) as document:
        for page in document.pages:
            lines = [
                line.strip()
                for line in (page.extract_text() or "").split("\n")
                if line.strip()
            ]
            if "LATOT" in "".join(lines[:80]) or "latoT" in "".join(lines):
                records.extend(parse_annex_page(lines))

    deduped: dict[str, dict[str, object]] = {}
    for record in records:
        deduped[normalize_name(str(record["nome"]))] = record
    return list(deduped.values())


def extract_document_id(pdf_path: Path) -> tuple[str | None, str | None]:
    with pdfplumber.open(pdf_path) as document:
        for page in document.pages:
            lines = (page.extract_text() or "").split("\n")
            for raw_line in lines:
                line = normalize_name(raw_line)
                if "FATURA" in line:
                    match = re.search(
                        r"FATURA\s*[:\-]\s*([A-Z0-9./-]+)",
                        line,
                        flags=re.IGNORECASE,
                    )
                    if match:
                        return match.group(1).strip(), "fatura"
                for pattern, source in DOCUMENT_ID_PATTERNS:
                    match = re.search(pattern, line, flags=re.IGNORECASE)
                    if match:
                        return match.group(1).strip(), source
    return None, None


def load_premios_from_pdfs(pdf_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for pdf_path in sorted(pdf_dir.glob("*.PDF")):
        doc_id, doc_id_source = extract_document_id(pdf_path)
        for record in parse_premios_pdf(pdf_path):
            rows.append(
                {
                    **record,
                    "fatura_numero": doc_id,
                    "fatura_fonte": doc_id_source,
                    "arquivo_origem": pdf_path.name,
                    "nome_norm": normalize_name(str(record["nome"])),
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "nome",
                "premio_total",
                "proposta",
                "fatura_numero",
                "fatura_fonte",
                "arquivo_origem",
                "nome_norm",
            ]
        )

    frame = pd.DataFrame(rows)
    frame = frame.sort_values(["nome_norm", "premio_total"]).drop_duplicates(
        subset=["nome_norm"], keep="first"
    )
    return frame.reset_index(drop=True)


def split_centro_custo(value: str) -> tuple[str, str]:
    text = str(value).strip()
    match = re.match(r"^(\d+(?:\.\d+)*)\.?\s+(.*)$", text)
    if not match:
        return "", text
    return match.group(1), match.group(2).strip()


def load_centro_custo(carga_path: Path) -> pd.DataFrame:
    frame = pd.read_excel(carga_path, sheet_name="Planilha1", header=0)
    frame.columns = ["centro_custo", "funcionario"]
    frame["funcionario"] = frame["funcionario"].astype(str).str.strip().str.upper()
    frame["nome_norm"] = frame["funcionario"].map(normalize_name)
    frame[["cc_codigo", "cc_descricao"]] = frame["centro_custo"].apply(
        lambda value: pd.Series(split_centro_custo(value))
    )
    return frame


def token_overlap_score(left: str, right: str) -> int:
    left_tokens = set(normalize_name(left).split())
    right_tokens = set(normalize_name(right).split())
    return len(left_tokens & right_tokens)


def find_best_match(
    nome_norm: str, candidatos: pd.DataFrame, usados: set[str]
) -> tuple[str | None, str, float]:
    if nome_norm in candidatos["nome_norm"].values:
        return nome_norm, "exato", 1.0

    opcoes = candidatos[~candidatos["nome_norm"].isin(usados)]["nome_norm"].tolist()
    fuzzy = difflib.get_close_matches(nome_norm, opcoes, n=1, cutoff=FUZZY_CUTOFF)
    if fuzzy:
        score = difflib.SequenceMatcher(None, nome_norm, fuzzy[0]).ratio()
        return fuzzy[0], "fuzzy", score

    melhor: tuple[str | None, str, float] = (None, "sem_match", 0.0)
    for candidato in opcoes:
        overlap = token_overlap_score(nome_norm, candidato)
        if overlap >= TOKEN_MATCH_MIN:
            score = overlap / max(len(nome_norm.split()), len(candidato.split()))
            if score > melhor[2]:
                melhor = (candidato, "tokens", score)
    return melhor


def consolidar(premios: pd.DataFrame, carga: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    usados: set[str] = set()
    consolidado_rows: list[dict[str, object]] = []
    sem_cc_rows: list[dict[str, object]] = []

    for _, row in premios.iterrows():
        match_norm, metodo, score = find_best_match(
            str(row["nome_norm"]), carga, usados
        )
        if match_norm is None:
            sem_cc_rows.append(
                {
                    "nome": row["nome"],
                    "premio_total": row["premio_total"],
                    "fatura_numero": row.get("fatura_numero"),
                    "fatura_fonte": row.get("fatura_fonte"),
                    "arquivo_origem": row["arquivo_origem"],
                    "motivo": "sem correspondência na CARGA",
                }
            )
            continue

        carga_row = carga.loc[carga["nome_norm"] == match_norm].iloc[0]
        usados.add(match_norm)
        consolidado_rows.append(
            {
                "nome": row["nome"],
                "nome_carga": carga_row["funcionario"],
                "premio_total": row["premio_total"],
                "fatura_numero": row.get("fatura_numero"),
                "fatura_fonte": row.get("fatura_fonte"),
                "centro_custo": carga_row["centro_custo"],
                "cc_codigo": carga_row["cc_codigo"],
                "cc_descricao": carga_row["cc_descricao"],
                "metodo_match": metodo,
                "score_match": round(score, 4),
                "arquivo_origem": row["arquivo_origem"],
            }
        )

    consolidado = pd.DataFrame(consolidado_rows)
    sem_cc = pd.DataFrame(sem_cc_rows)
    sem_premio = carga[~carga["nome_norm"].isin(usados)][
        ["funcionario", "centro_custo", "cc_codigo", "cc_descricao"]
    ].copy()
    sem_premio = sem_premio.rename(columns={"funcionario": "nome"})
    return consolidado, sem_cc, sem_premio


def build_resumo(
    premios: pd.DataFrame,
    carga: pd.DataFrame,
    consolidado: pd.DataFrame,
    sem_cc: pd.DataFrame,
    sem_premio: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"metrica": "Colaboradores com prêmio (PDFs)", "valor": len(premios)},
            {"metrica": "Colaboradores na CARGA Planilha1", "valor": len(carga)},
            {"metrica": "Matches consolidados", "valor": len(consolidado)},
            {"metrica": "Prêmio sem Centro de Custo", "valor": len(sem_cc)},
            {"metrica": "CC sem prêmio", "valor": len(sem_premio)},
            {
                "metrica": "Soma Prêmio Total consolidado (R$)",
                "valor": round(consolidado["premio_total"].sum(), 2),
            },
            {
                "metrica": "Soma Prêmio Total extraído (R$)",
                "valor": round(premios["premio_total"].sum(), 2),
            },
        ]
    )


def main() -> None:
    if not PDF_DIR.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {PDF_DIR}")
    if not CARGA_PATH.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {CARGA_PATH}")

    premios = load_premios_from_pdfs(PDF_DIR)
    carga = load_centro_custo(CARGA_PATH)
    consolidado, sem_cc, sem_premio = consolidar(premios, carga)
    resumo = build_resumo(premios, carga, consolidado, sem_cc, sem_premio)

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        consolidado.sort_values("nome").to_excel(
            writer, sheet_name="Consolidado", index=False
        )
        sem_cc.sort_values("nome").to_excel(writer, sheet_name="Sem CC", index=False)
        sem_premio.sort_values("nome").to_excel(
            writer, sheet_name="Sem Premio", index=False
        )
        resumo.to_excel(writer, sheet_name="Resumo", index=False)

    print(f"Arquivo gerado: {OUTPUT_PATH}")
    print(resumo.to_string(index=False))
    if not sem_cc.empty:
        print("\nPrêmio sem CC:")
        print(sem_cc[["nome", "premio_total"]].to_string(index=False))


if __name__ == "__main__":
    main()
