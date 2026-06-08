"""
Converte 02-Referencias/Folha-R/R_FOPA.xlsx (n4_CC, Data nf, Valor plano) para o layout
de fechamento (mesma estrutura de FECHAMENTO_ODBC / base_R_fechamento_folha).

Diferenças em relação a base_r_para_fechamento_folha.py:
- Entrada em Excel (não CSV); coluna de valor = Valor plano.
- data_nf e titulo (FOPA_MM_AAAA) vêm da coluna Data nf por linha.
- data_pagamento padrão: dia 8 do mês seguinte à data_nf (ex.: 30/04 -> 08/05).
- descrições e hierarquia de CC vêm do SAGI (rótulos truncados do Excel são substituídos; typos de código FOPA corrigidos).
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from fechamento_excel import gravar_fechamento_excel
from base_r_para_fechamento_folha import (
    LAYOUT_CORRETO,
    ParametrosFolha,
    REFS,
    TEMPLATE_FECHAMENTO_ODBC,
    _colunas_layout,
    carregar_mapa_cc_sagi,
    montar_linha_fechamento,
    parse_valor_br,
)

DEFAULT_INPUT = REFS / "Folha-R" / "R_FOPA.xlsx"
DEFAULT_OUTPUT = REFS / "Folha-R" / "R_FOPA_fechamento.xlsx"


def _parse_data(val) -> date:
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    s = str(val).strip()
    if not s or s.lower() == "nan":
        raise ValueError(f"Data inválida: {val!r}")
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s[:10], fmt[: len(fmt)]).date()
        except ValueError:
            continue
    try:
        return pd.to_datetime(val).date()
    except Exception as exc:
        raise ValueError(f"Data inválida: {val!r}") from exc


def data_pagamento_padrao(data_nf: date) -> date:
    """Dia 8 do mês seguinte (padrão folha: NF fim do mês, pagamento ~8 do mês seguinte)."""
    if data_nf.month == 12:
        return date(data_nf.year + 1, 1, 8)
    return date(data_nf.year, data_nf.month + 1, 8)


def titulo_fopa(data_nf: date) -> str:
    return f"FOPA_{data_nf.month:02d}_{data_nf.year}"


def observacao_folha(data_nf: date) -> str:
    return f"Processamento de Folha {data_nf.strftime('%d/%m/%Y')}"


def carregar_r_fopa(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=0, dtype=object)
    df = df.loc[:, [c for c in df.columns if str(c).strip() and not str(c).startswith("Unnamed")]]

    col_cc = next((c for c in df.columns if "n4" in str(c).lower() and "cc" in str(c).lower()), None)
    col_data = next((c for c in df.columns if "data" in str(c).lower()), None)
    col_valor = next(
        (c for c in df.columns if "valor" in str(c).lower() or "plano" in str(c).lower()),
        None,
    )
    if col_cc is None or col_data is None or col_valor is None:
        raise KeyError(
            f"Colunas esperadas (n4_CC, Data nf, Valor plano). Encontradas: {list(df.columns)}"
        )
    out = df.rename(columns={col_cc: "n4_CC", col_data: "Data nf", col_valor: "Valor plano"})
    return out


def _valor_numerico(val) -> float | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, (int, float)) and not pd.isna(val):
        return float(val)
    s = str(val).strip()
    if not s or s.lower() == "nan":
        return None
    if any(ch in s for ch in ",."):
        return parse_valor_br(s)
    try:
        return float(s)
    except ValueError:
        return parse_valor_br(s)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="R_FOPA.xlsx -> Excel no layout de fechamento (conta 7.3.1 SALÁRIOS)."
    )
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--cc-sagi", type=Path, default=REFS / "SAGI" / "sagi_rel_centro_custo.csv")
    ap.add_argument(
        "--layout",
        type=Path,
        default=None,
        help="Excel só para ordem das colunas. Padrão: layout corrigido da folha ou FECHAMENTO_ODBC.",
    )
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--sheet-out", default="Fechamento")
    ap.add_argument(
        "--mes",
        default=None,
        help="Filtra uma competência (YYYY-MM ou YYYY-MM-DD). Ex.: 2026-04",
    )
    ap.add_argument("--credor", default="PROCESSAMENTO DE FOLHA")
    ap.add_argument("--origem", default="Saída (Aplicações)")
    ap.add_argument("--sistema", default="FOPA")
    ap.add_argument("--dados-auxiliares", default="Processamento de folha")
    ap.add_argument(
        "--data-pagamento",
        default=None,
        help="Fixa data_pagamento para todas as linhas (YYYY-MM-DD). Padrão: dia 8 do mês seguinte à data_nf.",
    )
    ap.add_argument(
        "--multiplicador-valor",
        type=float,
        default=-1.0,
        help="Por padrão -1 (despesa/saída negativa, como no fechamento de folha).",
    )
    ap.add_argument(
        "--incluir-zerados",
        action="store_true",
        help="Inclui linhas com Valor plano = 0 (por padrão são ignoradas).",
    )
    args = ap.parse_args()

    layout = args.layout
    if layout is None:
        layout = LAYOUT_CORRETO if LAYOUT_CORRETO.exists() else TEMPLATE_FECHAMENTO_ODBC
    if not layout.exists():
        raise FileNotFoundError(f"Arquivo de layout não encontrado: {layout.resolve()}")
    if not args.input.exists():
        raise FileNotFoundError(args.input.resolve())
    if not args.cc_sagi.exists():
        raise FileNotFoundError(args.cc_sagi.resolve())

    data_pagamento_fixa = (
        _parse_data(args.data_pagamento) if args.data_pagamento is not None else None
    )

    filtro_mes: tuple[int, int] | None = None
    if args.mes:
        partes = args.mes.strip().split("-")
        if len(partes) < 2:
            raise ValueError(f"--mes inválido: {args.mes!r}")
        filtro_mes = (int(partes[0]), int(partes[1]))

    mapa_cc = carregar_mapa_cc_sagi(args.cc_sagi)
    df_in = carregar_r_fopa(args.input)

    linhas: list[dict[str, object]] = []
    ignoradas = 0

    for _, row in df_in.iterrows():
        rot = str(row["n4_CC"]).strip()
        if not rot or rot.lower() == "nan":
            ignoradas += 1
            continue

        vl = _valor_numerico(row["Valor plano"])
        if vl is None:
            ignoradas += 1
            continue
        if vl == 0.0 and not args.incluir_zerados:
            ignoradas += 1
            continue

        data_nf = _parse_data(row["Data nf"])
        if filtro_mes and (data_nf.year, data_nf.month) != filtro_mes:
            continue

        data_pagamento = data_pagamento_fixa or data_pagamento_padrao(data_nf)
        folha = ParametrosFolha(
            titulo=titulo_fopa(data_nf),
            observacao=observacao_folha(data_nf),
            credor=args.credor,
            origem=args.origem,
            sistema=args.sistema,
            dados_auxiliares=args.dados_auxiliares,
            data_nf=data_nf,
            data_pagamento=data_pagamento,
            multiplicador_valor=args.multiplicador_valor,
        )
        linhas.append(
            montar_linha_fechamento(len(linhas) + 1, rot, vl, mapa_cc, folha)
        )

    if not linhas:
        raise ValueError(
            "Nenhuma linha gerada. Verifique --mes, valores em branco ou o arquivo de entrada."
        )

    out_df = pd.DataFrame(linhas)
    cols = _colunas_layout(layout)
    for c in cols:
        if c not in out_df.columns:
            out_df[c] = pd.NA
    out_df = out_df[cols]

    gravar_fechamento_excel(out_df, args.output, sheet_name=args.sheet_out)
    print(
        f"Gravado: {args.output.resolve()} ({len(out_df)} linhas, {ignoradas} ignoradas). "
        f"Layout: {layout.name}"
    )


if __name__ == "__main__":
    main()
