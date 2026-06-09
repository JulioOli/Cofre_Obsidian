"""
Formatação padronizada de colunas financeiras e datas em arquivos de fechamento.

Regras:
- valor_nf, valor_pago, valor_conta, Valor Oficial: numérico no Excel, formato pt-BR (#.##0,00).
- valor_pago e valor_conta: sempre negativos.
- data_nf e data_pagamento: tipo data no Excel, exibição DD/MM/YYYY.
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Union

import pandas as pd

PathLike = Union[str, Path]

COLS_VALOR = ("valor_nf", "valor_pago", "valor_conta")
COL_VALOR_OFICIAL = "Valor Oficial"
COLS_VALOR_TODAS = (*COLS_VALOR, COL_VALOR_OFICIAL)
COLS_DATA = ("data_nf", "data_pagamento")

FMT_NUMERICO_PTBR = "#.##0,00"
FMT_DATA_PTBR = "DD/MM/YYYY"

# Compatibilidade com scripts legados
_COLS_VALOR_NUMERICO = COLS_VALOR_TODAS
_FMT_MOEDA_EXCEL = FMT_NUMERICO_PTBR


def _col_por_nome(columns, nome: str) -> str | None:
    alvo = nome.strip()
    if alvo in columns:
        return alvo
    for c in columns:
        if str(c).strip() == alvo:
            return c
    return None


def parse_valor_fechamento(v) -> float | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)) and not pd.isna(v):
        return float(v)
    s = str(v).strip().replace("R$", "").replace(" ", "")
    if not s or s.lower() in {"nan", "none"}:
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def parse_data_fechamento(v):
    if v is None or pd.isna(v):
        return pd.NaT
    if isinstance(v, (datetime, date)):
        ts = pd.Timestamp(v)
        if pd.isna(ts):
            return pd.NaT
        return ts.normalize()
    s = str(v).strip()
    if not s or s.lower() in {"nan", "nat", "none"}:
        return pd.NaT
    dt = pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
    if pd.isna(dt):
        dt = pd.to_datetime(s, errors="coerce")
    return dt


def preparar_dataframe_fechamento(
    df: pd.DataFrame,
    *,
    colunas_preservar_sinal: tuple[str, ...] = (),
) -> pd.DataFrame:
    """Normaliza tipos e sinais antes de gravar Excel de fechamento."""
    out = df.copy()
    preservar = {str(c).strip() for c in colunas_preservar_sinal}

    for nome in COLS_VALOR_TODAS:
        col = _col_por_nome(out.columns, nome)
        if col:
            out[col] = out[col].map(parse_valor_fechamento)

    for nome in ("valor_pago", "valor_conta"):
        if nome in preservar:
            continue
        col = _col_por_nome(out.columns, nome)
        if col:
            nums = pd.to_numeric(out[col], errors="coerce")
            mask = nums.notna()
            nums.loc[mask] = -nums.loc[mask].abs()
            out[col] = nums

    for nome in COLS_DATA:
        col = _col_por_nome(out.columns, nome)
        if col:
            if pd.api.types.is_datetime64_any_dtype(out[col]):
                out[col] = pd.to_datetime(out[col], errors="coerce")
            else:
                out[col] = out[col].map(parse_data_fechamento)

    return out


def aplicar_formato_fechamento_ws(ws) -> None:
    """Aplica number_format pt-BR nas colunas financeiras e de data."""
    for j in range(1, ws.max_column + 1):
        raw = ws.cell(row=1, column=j).value
        if raw is None:
            continue
        nome = str(raw).strip()
        if nome in COLS_VALOR or nome == COL_VALOR_OFICIAL:
            fmt = FMT_NUMERICO_PTBR
        elif nome in COLS_DATA:
            fmt = FMT_DATA_PTBR
        else:
            continue
        for r in range(2, ws.max_row + 1):
            cell = ws.cell(row=r, column=j)
            if cell.value is None or cell.value == "":
                continue
            cell.number_format = fmt


def gravar_fechamento_excel(
    df: pd.DataFrame,
    caminho: PathLike,
    sheet_name: str = "base",
    *,
    bold_header: bool = True,
    colunas_preservar_sinal: tuple[str, ...] = (),
) -> Path:
    """Grava DataFrame no layout de fechamento com formatação padronizada."""
    from openpyxl.styles import Font

    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    preparado = preparar_dataframe_fechamento(
        df, colunas_preservar_sinal=colunas_preservar_sinal
    )

    with pd.ExcelWriter(destino, engine="openpyxl") as writer:
        preparado.to_excel(writer, sheet_name=sheet_name, index=False)
        ws = writer.sheets[sheet_name]
        if bold_header:
            bold = Font(bold=True)
            for cell in ws[1]:
                cell.font = bold
        aplicar_formato_fechamento_ws(ws)

    return destino
