from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

import pandas as pd


CODE_RE = re.compile(r"^\d+(?:\.\d+)*$")


def _read_text_with_fallback(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="replace")


def _is_noise_line(line: str) -> bool:
    raw = line.strip()
    if not raw:
        return True
    upper = raw.upper()
    noise_tokens = (
        "R.SOCIAL",
        "RELA",
        "PÁGINA",
        "PбGINA",
        "WWW.SYGECOM",
        "RELATORIOS\\",
        "CÓDIGO",
        "CуDIGO",
        "DESCRI",
        "TIPO;",
        "Nº TOTAL",
        "DATA. :",
    )
    if any(token in upper for token in noise_tokens):
        return True
    if set(raw) <= {";", "-", " "}:
        return True
    return False


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip(" ;")


def _code_sort_key(code: str) -> tuple[int, ...]:
    return tuple(int(x) for x in code.split("."))


def _extract_first_matching(values: Iterable[str], predicate) -> str | None:
    for value in values:
        candidate = _clean_text(value)
        if candidate and predicate(candidate):
            return candidate
    return None


def _logical_level(code: str) -> int:
    # O primeiro bloco (1/2) indica natureza; níveis lógicos começam no segundo bloco.
    return max(0, len(code.split(".")) - 1)


def parse_plano_contas(path: Path) -> pd.DataFrame:
    rows: list[dict[str, str | int]] = []
    for line in _read_text_with_fallback(path).splitlines():
        if _is_noise_line(line):
            continue
        parts = [p for p in line.split(";")]
        code = _extract_first_matching(parts, lambda x: bool(CODE_RE.match(x)))
        if not code:
            continue

        code_idx = next(i for i, p in enumerate(parts) if _clean_text(p) == code)
        trailing = parts[code_idx + 1 :]
        descricao = _extract_first_matching(
            trailing,
            lambda x: x not in {"D", "R"} and not re.fullmatch(r"\d+,\d+", x),
        )
        natureza = _extract_first_matching(trailing, lambda x: x in {"D", "R"})
        rows.append(
            {
                "codigo": code,
                "descricao": descricao or "",
                "natureza": natureza or "",
            }
        )

    df = pd.DataFrame(rows).drop_duplicates(subset=["codigo"]).copy()
    df["natureza_codigo"] = df["codigo"].str.split(".").str[0]
    df["nivel"] = df["codigo"].apply(_logical_level)
    df["codigo_pai"] = df["codigo"].apply(lambda c: ".".join(c.split(".")[:-1]) if "." in c else "")
    descricao_map = dict(zip(df["codigo"], df["descricao"]))
    df["descricao_pai"] = df["codigo_pai"].map(descricao_map).fillna("")
    df = df.sort_values(by="codigo", key=lambda s: s.map(_code_sort_key)).reset_index(drop=True)
    return df


def parse_centro_custo(path: Path) -> pd.DataFrame:
    rows: list[dict[str, str | int]] = []
    for line in _read_text_with_fallback(path).splitlines():
        if _is_noise_line(line):
            continue

        parts = [p for p in line.split(";")]
        code = _extract_first_matching(parts, lambda x: bool(CODE_RE.match(x)))
        if not code:
            continue

        code_idx = next(i for i, p in enumerate(parts) if _clean_text(p) == code)
        trailing = parts[code_idx + 1 :]
        classificacao = _extract_first_matching(
            trailing, lambda x: "ANAL" in x.upper() or "SINT" in x.upper()
        )
        descricao = _extract_first_matching(
            trailing,
            lambda x: x != classificacao and "ANAL" not in x.upper() and "SINT" not in x.upper(),
        )

        rows.append(
            {
                "codigo": code,
                "descricao": descricao or "",
                "classificacao": classificacao or "",
            }
        )

    df = pd.DataFrame(rows).drop_duplicates(subset=["codigo"]).copy()
    df["natureza_codigo"] = df["codigo"].str.split(".").str[0]
    df["nivel"] = df["codigo"].apply(_logical_level)
    df["codigo_pai"] = df["codigo"].apply(lambda c: ".".join(c.split(".")[:-1]) if "." in c else "")
    descricao_map = dict(zip(df["codigo"], df["descricao"]))
    df["descricao_pai"] = df["codigo_pai"].map(descricao_map).fillna("")
    df = df.sort_values(by="codigo", key=lambda s: s.map(_code_sort_key)).reset_index(drop=True)
    return df


def _format_worksheet(worksheet) -> None:
    worksheet.auto_filter.ref = worksheet.dimensions
    worksheet.freeze_panes = "A2"
    for column_cells in worksheet.columns:
        col_letter = column_cells[0].column_letter
        max_len = max(len(str(cell.value or "")) for cell in column_cells)
        worksheet.column_dimensions[col_letter].width = min(max(12, max_len + 2), 60)


def _build_hierarchy_view(df: pd.DataFrame, tipo: str) -> pd.DataFrame:
    max_nivel = 3
    descricao_map = dict(zip(df["codigo"], df["descricao"]))
    rows: list[dict[str, str | int]] = []

    for row in df.itertuples(index=False):
        codigo = row.codigo
        partes = codigo.split(".")
        partes_logicas = partes[1:]
        base = {
            "tipo_estrutura": tipo,
            "codigo": codigo,
            "descricao": row.descricao,
            "natureza_codigo": row.natureza_codigo,
            "nivel": row.nivel,
            "codigo_pai": row.codigo_pai,
            "descricao_pai": row.descricao_pai,
        }
        for idx in range(1, max_nivel + 1):
            if idx <= len(partes_logicas):
                codigo_nivel = ".".join([partes[0], *partes_logicas[:idx]])
                base[f"nivel_{idx}_codigo"] = codigo_nivel
                base[f"nivel_{idx}_descricao"] = descricao_map.get(codigo_nivel, "")
            else:
                base[f"nivel_{idx}_codigo"] = ""
                base[f"nivel_{idx}_descricao"] = ""
        rows.append(base)

    return pd.DataFrame(rows)


def save_excel(plano_df: pd.DataFrame, centro_df: pd.DataFrame, output_path: Path) -> None:
    resumo_plano_nivel = plano_df.groupby("nivel", as_index=False).size()
    resumo_plano_natureza = plano_df.groupby("natureza", as_index=False).size()
    resumo_centro_nivel = centro_df.groupby("nivel", as_index=False).size()
    resumo_centro_classificacao = centro_df.groupby("classificacao", as_index=False).size()
    hierarquia_plano = _build_hierarchy_view(plano_df, "Plano de Contas")
    hierarquia_centro = _build_hierarchy_view(centro_df, "Centro de Custo")
    hierarquia_df = pd.concat([hierarquia_plano, hierarquia_centro], ignore_index=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        plano_df.to_excel(writer, sheet_name="Plano_Contas", index=False)
        centro_df.to_excel(writer, sheet_name="Centros_Custo", index=False)
        hierarquia_df.to_excel(writer, sheet_name="Hierarquia", index=False)
        resumo_plano_nivel.to_excel(writer, sheet_name="Resumo", index=False, startrow=0)
        resumo_plano_natureza.to_excel(writer, sheet_name="Resumo", index=False, startrow=6)
        resumo_centro_nivel.to_excel(writer, sheet_name="Resumo", index=False, startrow=12)
        resumo_centro_classificacao.to_excel(writer, sheet_name="Resumo", index=False, startrow=18)

        workbook = writer.book
        for sheet_name in ("Plano_Contas", "Centros_Custo", "Hierarquia", "Resumo"):
            _format_worksheet(workbook[sheet_name])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Converte relatórios SAGI de plano de contas e centro de custo para Excel organizado."
    )
    parser.add_argument(
        "--plano",
        type=Path,
        default=Path("02-Referencias/sagi_rel_plano_conta.csv"),
        help="Caminho do CSV de plano de contas.",
    )
    parser.add_argument(
        "--centro",
        type=Path,
        default=Path("02-Referencias/sagi_rel_centro_custo.csv"),
        help="Caminho do CSV de centros de custo.",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("02-Referencias/sagi_estrutura_financeira.xlsx"),
        help="Caminho do arquivo Excel de saída.",
    )
    args = parser.parse_args()

    plano_df = parse_plano_contas(args.plano)
    centro_df = parse_centro_custo(args.centro)
    save_excel(plano_df, centro_df, args.saida)

    print(f"Arquivo gerado com sucesso: {args.saida}")
    print(f"Plano de contas: {len(plano_df)} linhas")
    print(f"Centros de custo: {len(centro_df)} linhas")


if __name__ == "__main__":
    main()
