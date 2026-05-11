"""Atualiza valor_conta na aba MARCO_E_ABRIL a partir da aba Fechamento (mesmo arquivo xlsx)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def to_float_br(v):
    if pd.isna(v):
        return np.nan
    s = str(v).strip()
    if s == "":
        return np.nan
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return np.nan


def norm_date(v):
    dt = pd.to_datetime(v, dayfirst=True, errors="coerce")
    if pd.isna(dt):
        return ""
    return dt.strftime("%Y-%m-%d")


def enrich(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["_titulo"] = d["titulo"].astype(str).str.strip()
    d["_filial"] = d["filial"].astype(str).str.strip()
    d["_cod"] = d["cod_conta"].astype(str).str.strip()
    d["_vn"] = d["valor_nf"].apply(to_float_br)
    d["_dt"] = d["data_nf"].map(norm_date)
    d["_vp"] = d["valor_pago"].apply(to_float_br)
    d["_cred"] = d["credor_forn_cli_func"].astype(str).str.strip()
    d["id_s"] = d["id"].astype(str).str.strip()
    return d


def pick_vc(row: pd.Series, f: pd.DataFrame):
    mask = (
        (f["_titulo"] == row["_titulo"])
        & (f["_filial"] == row["_filial"])
        & (f["_cod"] == row["_cod"])
        & (f["_vn"] == row["_vn"])
        & (f["_dt"] == row["_dt"])
        & (f["_vp"] == row["_vp"])
        & (f["_cred"] == row["_cred"])
    )
    cand = f.loc[mask]
    if len(cand) == 1:
        return cand["valor_conta"].iloc[0]
    if len(cand) > 1:
        c2 = cand[cand["id_s"] == row["id_s"]]
        if len(c2) == 1:
            return c2["valor_conta"].iloc[0]
        return np.nan
    c3 = f[f["id_s"] == row["id_s"]]
    if len(c3) != 1:
        return np.nan
    fr = c3.iloc[0]
    if (
        fr["_titulo"] == row["_titulo"]
        and fr["_filial"] == row["_filial"]
        and fr["_cod"] == row["_cod"]
        and fr["_vn"] == row["_vn"]
    ):
        return fr["valor_conta"]
    return np.nan


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "xlsx",
        nargs="?",
        default="02-Referencias/FECHAMENTO_ODBC_2026_04.xlsx",
        help="Caminho do Excel com abas MARCO_E_ABRIL e Fechamento",
    )
    args = p.parse_args()
    path = Path(args.xlsx)
    if not path.is_file():
        print(f"Arquivo nao encontrado: {path.resolve()}", file=sys.stderr)
        sys.exit(1)

    marco = pd.read_excel(path, sheet_name="MARCO_E_ABRIL")
    fech = pd.read_excel(path, sheet_name="Fechamento")

    m = enrich(marco)
    f = enrich(fech)

    new_vc = pd.Series([pick_vc(m.loc[i], f) for i in m.index], index=m.index)
    updated = marco.copy()
    mask = new_vc.notna()
    # Fechamento traz valor_conta como texto (ex.: '-179,93'); evita conflito com float na aba MARCO
    updated["valor_conta"] = updated["valor_conta"].astype(object)
    updated.loc[mask, "valor_conta"] = new_vc[mask].astype(object).values

    print(f"Linhas atualizadas em valor_conta: {int(mask.sum())} / {len(updated)}")

    with pd.ExcelWriter(path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        updated.to_excel(writer, sheet_name="MARCO_E_ABRIL", index=False)

    print(f"Gravado: {path.resolve()}")


if __name__ == "__main__":
    main()
