"""Remove prefixo duplicado do nivel 3 em n4_centro_custo e recalcula n4_CC (planilhas exportadas do ODBC)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

# Ultimo trecho apos " / " quando parece placa/codigo de ativo (ex.: "SC / EHH0044" -> "EHH0044")
_ID_TAIL = re.compile(
    r"^([A-Z]{3}\d{4}|[A-Z]{3}\d[A-Z0-9]{3}|[A-Z0-9]{5,8}\s*\([^)]+\))$",
    re.IGNORECASE,
)


def strip_n3_prefix_from_n4(n3, n4) -> str:
    n3s = str(n3).strip() if pd.notna(n3) else ""
    n4s = str(n4).strip() if pd.notna(n4) else ""
    if not n3s or not n4s:
        return n4s
    prefix = n3s + " / "
    if n4s.startswith(prefix):
        return n4s[len(prefix) :].strip()
    return n4s


def strip_residual_state_prefix(n4) -> str:
    """Quando o ODBC quebra nivel 3 (ex.: 'TUPY - JOINVILLE' sem '/SC'), n4 pode ficar 'SC / EHH0044'."""
    n4s = str(n4).strip() if pd.notna(n4) else ""
    if " / " not in n4s:
        return n4s
    tail = n4s.split(" / ")[-1].strip()
    if _ID_TAIL.match(tail):
        return tail
    return n4s


def fix_operadores_centro_label(n4) -> str:
    """Caso raro do descen ARCELOR (pool operadores) sem placa no texto de n4."""
    n4s = str(n4).strip() if pd.notna(n4) else ""
    if " / " not in n4s:
        return n4s
    if "operadores" in n4s.lower() and "arcelor" in n4s.lower():
        return "ARCELOR RESENDE - OPERADORES"
    return n4s


def rebuild_n4_cc(cod, centro) -> str:
    c = str(cod).strip() if pd.notna(cod) else ""
    t = str(centro).strip() if pd.notna(centro) else ""
    return (c + " " + t).strip()


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "xlsx",
        nargs="?",
        default="02-Referencias/Correcao_Manutencao_marco-e-abril.xlsx",
    )
    p.add_argument("--sheet", default="Geral")
    p.add_argument("--year", type=int, default=2026)
    p.add_argument("--months", default="3,4", help="Meses afetados, ex.: 3,4")
    args = p.parse_args()
    path = Path(args.xlsx)
    if not path.is_file():
        print(f"Arquivo nao encontrado: {path.resolve()}", file=sys.stderr)
        sys.exit(1)

    months = {int(x.strip()) for x in args.months.split(",") if x.strip()}

    df = pd.read_excel(path, sheet_name=args.sheet)
    if "data_nf" not in df.columns or "n3_centro_custo" not in df.columns:
        print("Colunas esperadas ausentes (data_nf, n3_centro_custo).", file=sys.stderr)
        sys.exit(1)

    dt = pd.to_datetime(df["data_nf"], errors="coerce")
    mask = (dt.dt.year == args.year) & (dt.dt.month.isin(months))
    n3 = df.loc[mask, "n3_centro_custo"]
    n4_old = df.loc[mask, "n4_centro_custo"]
    n4_new = [strip_n3_prefix_from_n4(a, b) for a, b in zip(n3, n4_old)]
    n4_new = [strip_residual_state_prefix(x) for x in n4_new]
    n4_new = [fix_operadores_centro_label(x) for x in n4_new]
    changed = sum(
        1
        for a, b in zip(n4_old.astype(str), n4_new)
        if str(a).strip() != str(b).strip()
    )
    df.loc[mask, "n4_centro_custo"] = n4_new
    df.loc[mask, "n4_CC"] = [
        rebuild_n4_cc(c, t)
        for c, t in zip(df.loc[mask, "n4_cod_centro_custo"], df.loc[mask, "n4_centro_custo"])
    ]

    with pd.ExcelWriter(path, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
        df.to_excel(w, sheet_name=args.sheet, index=False)

    print(f"Linhas no periodo: {int(mask.sum())} | n4_centro_custo alteradas: {changed}")
    print(f"Gravado: {path.resolve()}")


if __name__ == "__main__":
    main()
