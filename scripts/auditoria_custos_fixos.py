"""Auditoria de custos fixos administrativos a partir do pivot Excel.

Lê o arquivo `Detalhamento Custos com 2.1.1 - <periodo>.xlsx` (estrutura de pivot
hierárquico do Excel: Plano -> Credor -> Documento -> Histórico) e gera um
relatório multi-aba destacando divergências entre os meses.

Uso típico:
    python scripts/auditoria_custos_fixos.py
"""

from __future__ import annotations


import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


# ─── Configuração padrão ────────────────────────────────────────────────────

DEFAULT_SRC = Path("02-Referencias/Detalhamento Custos com 2.1.1 - 01_2026 a 04_2026.xlsx")
DEFAULT_DST = Path("02-Referencias/auditoria_custos_fixos_2026.xlsx")

# Limiares (ajustáveis via CLI)
LIMIAR_VARIACAO_PCT = 0.30          # 30% de variação vs. mediana de referência
LIMIAR_VALOR_MINIMO = 100.0          # Ignora variações de centavos / valores irrelevantes
LIMIAR_ZSCORE_LANCAMENTO = 2.0       # |z| ≥ 2 sinaliza lançamento atípico

# Cabeçalhos do pivot Excel → nomes internos (espaços à esquerda conforme o Excel exporta).
COLS_VALOR_ORIG = {
    "JAN/2026": "jan",
    " FEV/2026": "fev",
    "  MAR/2026": "mar",
    "   ABR/2026": "abr",
}
MESES = ["jan", "fev", "mar", "abr"]
# Janeiro e fevereiro tratados como baseline auditado; MAR/ABR são contrastados no relatório de parâmetros.
MES_REFERENCIA = ["jan", "fev"]
MESES_AUDITAR = ["mar", "abr"]
MES_LABEL = {
    "jan": "JAN/2026",
    "fev": "FEV/2026",
    "mar": "MAR/2026",
    "abr": "ABR/2026",
}
MEDIANA_COL = "mediana_abs_meses"
MEDIANA_EXCEL_NOME = "Mediana |4m|"


# ─── Cores para formatação condicional do Excel ─────────────────────────────

FILL_CABECALHO = PatternFill("solid", fgColor="305496")
FONT_CABECALHO = Font(bold=True, color="FFFFFF")
FILL_ALTA = PatternFill("solid", fgColor="F8CBAD")     # vermelho-claro
FILL_MEDIA = PatternFill("solid", fgColor="FFE699")    # amarelo
FILL_BAIXA = PatternFill("solid", fgColor="C6EFCE")    # verde

SEVERIDADE_ORDEM = {"ALTA": 0, "MEDIA": 1, "BAIXA": 2}


# ─── Estruturas auxiliares ──────────────────────────────────────────────────


@dataclass
class Parametros:
    src: Path
    dst: Path
    limiar_pct: float
    valor_minimo: float
    zscore_lancamento: float


# ─── Etapa 1 — Parsing e achatamento do pivot ───────────────────────────────


def _strip_total(valor) -> object:
    if isinstance(valor, str) and valor.endswith(" Total"):
        return valor[: -len(" Total")]
    return valor


def carregar_pivot(src: Path) -> pd.DataFrame:
    """Lê o Excel e devolve o dataframe com colunas renomeadas."""
    df = pd.read_excel(src)
    rename = {
        "Unnamed: 0": "plano",
        "Unnamed: 1": "credor",
        "Unnamed: 2": "documento",
        "Unnamed: 3": "historico",
        "Grande Total": "total",
        **COLS_VALOR_ORIG,
    }
    faltando = [c for c in rename if c not in df.columns]
    if faltando:
        raise ValueError(
            "Estrutura do pivot diferente do esperado; colunas ausentes: "
            f"{faltando}. Colunas presentes: {list(df.columns)}"
        )
    return df.rename(columns=rename)


def achatar_pivot(df: pd.DataFrame) -> pd.DataFrame:
    """Identifica linhas-folha (lançamentos) e propaga os níveis hierárquicos.

    Regras do pivot:
      - Linhas com sufixo " Total" em qualquer coluna categórica são subtotais.
      - A linha "Grande Total" é o totalizador geral.
      - Linhas-folha são as que têm pelo menos um valor mensal preenchido e
        nenhum sufixo " Total" nas colunas categóricas.
    """
    cat_cols = ["plano", "credor", "documento", "historico"]
    val_cols = MESES

    is_subtotal = pd.concat(
        [df[c].astype(str).str.endswith(" Total") for c in cat_cols], axis=1
    ).any(axis=1)
    is_grand = df["plano"].astype(str).eq("Grande Total")
    has_value = df[val_cols].notna().any(axis=1)

    df_ff = df.copy()
    for col in ["plano", "credor", "documento"]:
        df_ff[col] = df_ff[col].apply(_strip_total).ffill()

    folhas = df_ff.loc[~is_subtotal & ~is_grand & has_value].copy()
    folhas[val_cols] = folhas[val_cols].fillna(0.0)
    folhas["historico"] = folhas["historico"].fillna("(sem histórico)")
    folhas["documento"] = folhas["documento"].fillna("(sem documento)")
    folhas["credor"] = folhas["credor"].fillna("(sem credor)")
    folhas["historico_curto"] = (
        folhas["historico"].astype(str).str.replace(r"\s+", " ", regex=True).str.slice(0, 200)
    )
    folhas["plano_codigo"] = folhas["plano"].astype(str).str.split(" - ").str[0]
    return folhas[
        [
            "plano",
            "plano_codigo",
            "credor",
            "documento",
            "historico",
            "historico_curto",
            *val_cols,
        ]
    ].reset_index(drop=True)


# ─── Etapa 2 — Análises de divergência ──────────────────────────────────────


def _formatar_pct(v: float | None) -> str:
    if v is None or pd.isna(v):
        return ""
    return f"{v * 100:+.1f}%"


def _classificar_severidade(variacao_pct: float, limiar: float) -> str:
    if pd.isna(variacao_pct):
        return ""
    abs_var = abs(variacao_pct)
    if abs_var >= 2 * limiar:
        return "ALTA"
    if abs_var >= limiar:
        return "MEDIA"
    return "BAIXA"


def analisar_plano(folhas: pd.DataFrame, params: Parametros) -> pd.DataFrame:
    """Totais por plano e por mês com flags de variação."""
    grupo = (
        folhas.groupby(["plano_codigo", "plano"], dropna=False)[MESES]
        .sum()
        .reset_index()
    )

    valores = grupo[MESES].to_numpy(dtype=float)
    ref = np.where(valores != 0, valores, np.nan)
    mediana_ref = np.nanmedian(np.abs(ref), axis=1)
    grupo[MEDIANA_COL] = mediana_ref

    flags_por_linha: list[list[str]] = []
    for idx, row in grupo.iterrows():
        flags: list[str] = []
        valores_meses = {m: row[m] for m in MESES}
        zerados = [m for m, v in valores_meses.items() if v == 0]
        com_valor = [m for m, v in valores_meses.items() if v != 0]

        if len(com_valor) == 1:
            mes_unico = com_valor[0]
            if abs(valores_meses[mes_unico]) >= params.valor_minimo:
                flags.append(f"MES_UNICO:{mes_unico.upper()}")

        if 0 < len(zerados) < len(MESES):
            for m in zerados:
                if mediana_ref[idx] >= params.valor_minimo:
                    flags.append(f"MES_ZERADO:{m.upper()}")

        for m in MESES:
            valor = valores_meses[m]
            ref_outros = [
                valores_meses[mm] for mm in MESES if mm != m and valores_meses[mm] != 0
            ]
            if not ref_outros or valor == 0:
                continue
            ref_med = float(np.median(np.abs(ref_outros)))
            if ref_med < params.valor_minimo:
                continue
            var = (abs(valor) - ref_med) / ref_med
            if abs(var) >= params.limiar_pct:
                flags.append(
                    f"VARIACAO_{_classificar_severidade(var, params.limiar_pct)}:"
                    f"{m.upper()}({_formatar_pct(var)})"
                )

        flags_por_linha.append(flags)

    grupo["flags"] = ["; ".join(f) for f in flags_por_linha]
    grupo["qtd_flags"] = [len(f) for f in flags_por_linha]
    grupo["severidade"] = grupo["flags"].apply(_severidade_de_flags)
    grupo = grupo.sort_values(
        by=["severidade", "qtd_flags"],
        key=lambda s: s.map(SEVERIDADE_ORDEM) if s.name == "severidade" else s,
        ascending=[True, False],
    )
    return grupo


def _severidade_de_flags(flags_str: str) -> str:
    if "ALTA" in flags_str or "MES_UNICO" in flags_str:
        return "ALTA"
    if "MEDIA" in flags_str or "MES_ZERADO" in flags_str:
        return "MEDIA"
    if flags_str:
        return "BAIXA"
    return ""


def analisar_credor_plano(folhas: pd.DataFrame, params: Parametros) -> pd.DataFrame:
    """Cruzamento credor × plano: detecta credores avulsos e mudança de plano."""
    grupo = (
        folhas.groupby(["credor", "plano_codigo", "plano"], dropna=False)[MESES]
        .sum()
        .reset_index()
    )
    grupo["meses_presentes"] = (grupo[MESES] != 0).sum(axis=1)
    grupo[MEDIANA_COL] = grupo[MESES].abs().replace(0, np.nan).median(axis=1)

    # Mudança de plano de contas para o mesmo credor
    planos_por_credor = (
        grupo.groupby("credor")["plano_codigo"].nunique().rename("qtd_planos_distintos")
    )
    grupo = grupo.merge(planos_por_credor, on="credor", how="left")

    flags: list[list[str]] = []
    for _, row in grupo.iterrows():
        f: list[str] = []
        med = row[MEDIANA_COL]
        if not pd.isna(med) and med >= params.valor_minimo:
            if row["meses_presentes"] == 1:
                mes = next(m for m in MESES if row[m] != 0)
                f.append(f"CREDOR_AVULSO:{mes.upper()}")
            elif row["meses_presentes"] < len(MESES):
                # Credor presente em mais de um mês mas não em todos — lista cada mês zerado.
                for mz in MESES:
                    if row[mz] == 0:
                        f.append(f"FALTA_NO_MES:{mz.upper()}")

            valores_nao_zero = [row[m] for m in MESES if row[m] != 0]
            if len(valores_nao_zero) >= 2:
                v_max = max(abs(v) for v in valores_nao_zero)
                v_min = min(abs(v) for v in valores_nao_zero)
                if v_min > 0 and (v_max - v_min) / v_min >= params.limiar_pct:
                    sev = _classificar_severidade(
                        (v_max - v_min) / v_min, params.limiar_pct
                    )
                    f.append(
                        f"VARIACAO_CREDOR_{sev}:{_formatar_pct((v_max - v_min) / v_min)}"
                    )

        if row["qtd_planos_distintos"] > 1:
            f.append(f"MUDANCA_DE_PLANO({int(row['qtd_planos_distintos'])})")

        flags.append(f)

    grupo["flags"] = ["; ".join(f) for f in flags]
    grupo["qtd_flags"] = [len(f) for f in flags]
    grupo["severidade"] = grupo["flags"].apply(_severidade_de_flags)
    grupo = grupo[grupo["qtd_flags"] > 0].copy()
    grupo = grupo.sort_values(
        by=["severidade", "qtd_flags"],
        key=lambda s: s.map(SEVERIDADE_ORDEM) if s.name == "severidade" else s,
        ascending=[True, False],
    )
    return grupo


def analisar_lancamentos(folhas: pd.DataFrame, params: Parametros) -> pd.DataFrame:
    """Z-score por (plano, credor) entre meses + detecção de estornos."""
    df = folhas.copy()

    grupo_keys = ["plano_codigo", "credor"]
    valores_long = df.melt(
        id_vars=grupo_keys + ["documento", "historico_curto"],
        value_vars=MESES,
        var_name="mes",
        value_name="valor",
    )
    valores_long = valores_long[valores_long["valor"] != 0]

    stats = (
        valores_long.groupby(grupo_keys)["valor"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(columns={"mean": "media_grupo", "std": "desvio_grupo", "count": "n_grupo"})
    )

    valores_long = valores_long.merge(stats, on=grupo_keys, how="left")
    valores_long["zscore"] = np.where(
        (valores_long["desvio_grupo"].fillna(0) > 0) & (valores_long["n_grupo"] >= 3),
        (valores_long["valor"] - valores_long["media_grupo"]) / valores_long["desvio_grupo"],
        np.nan,
    )

    flags: list[list[str]] = []
    for _, row in valores_long.iterrows():
        f: list[str] = []
        if abs(row["valor"]) < params.valor_minimo:
            flags.append(f)
            continue
        if row["valor"] > 0 and row["media_grupo"] is not None and row["media_grupo"] < 0:
            f.append("POSSIVEL_ESTORNO")
        if not pd.isna(row["zscore"]) and abs(row["zscore"]) >= params.zscore_lancamento:
            sev = "ALTA" if abs(row["zscore"]) >= params.zscore_lancamento + 1 else "MEDIA"
            f.append(f"VALOR_FOGE_PADRAO_{sev}(z={row['zscore']:+.2f})")
        flags.append(f)

    valores_long["flags"] = ["; ".join(f) for f in flags]
    valores_long["severidade"] = valores_long["flags"].apply(_severidade_de_flags)
    valores_long = valores_long[valores_long["flags"] != ""].copy()
    valores_long = valores_long.sort_values(
        by=["severidade", "valor"],
        key=lambda s: s.map(SEVERIDADE_ORDEM) if s.name == "severidade" else s.abs(),
        ascending=[True, False],
    )
    valores_long["mes"] = valores_long["mes"].map(MES_LABEL)
    return valores_long.reset_index(drop=True)


# ─── Etapa 3 — Geração do Excel ─────────────────────────────────────────────


def _aplicar_cabecalho(ws) -> None:
    for cell in ws[1]:
        cell.fill = FILL_CABECALHO
        cell.font = FONT_CABECALHO
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _ajustar_colunas(ws, max_width: int = 50) -> None:
    for col in ws.columns:
        col_letter = col[0].column_letter
        max_len = 0
        for cell in col:
            valor = cell.value
            if valor is None:
                continue
            txt = str(valor)
            comprimento = len(txt.split("\n", 1)[0])
            if comprimento > max_len:
                max_len = comprimento
        ws.column_dimensions[col_letter].width = min(max(12, max_len + 2), max_width)


def _aplicar_formato_contabil(ws, colunas: Iterable[int]) -> None:
    for col_idx in colunas:
        for cell in ws.iter_cols(min_col=col_idx, max_col=col_idx, min_row=2):
            for c in cell:
                c.number_format = '_-"R$" * #,##0.00_-;[Red]-"R$" * #,##0.00_-;_-"R$" * "-"??_-;_-@_-'


def _colorir_severidade(ws, coluna_severidade: int, primeira_data: int = 2) -> None:
    max_row = ws.max_row
    if max_row < primeira_data:
        return
    rng = (
        f"A{primeira_data}:"
        f"{get_column_letter(ws.max_column)}{max_row}"
    )
    cond_alta = CellIsRule(operator="equal", formula=['"ALTA"'], fill=FILL_ALTA)
    cond_media = CellIsRule(operator="equal", formula=['"MEDIA"'], fill=FILL_MEDIA)
    cond_baixa = CellIsRule(operator="equal", formula=['"BAIXA"'], fill=FILL_BAIXA)
    sev_letra = get_column_letter(coluna_severidade)
    for rule in (cond_alta, cond_media, cond_baixa):
        ws.conditional_formatting.add(
            f"{sev_letra}{primeira_data}:{sev_letra}{max_row}", rule
        )


def construir_resumo(plano_df: pd.DataFrame, credor_df: pd.DataFrame, lanc_df: pd.DataFrame) -> pd.DataFrame:
    contagem = []
    for sev in ("ALTA", "MEDIA", "BAIXA"):
        contagem.append(
            {
                "Severidade": sev,
                "Planos com flag": int((plano_df["severidade"] == sev).sum()),
                "Credores com flag": int((credor_df["severidade"] == sev).sum()),
                "Lançamentos com flag": int((lanc_df["severidade"] == sev).sum()),
            }
        )
    return pd.DataFrame(contagem)


def gerar_excel(
    folhas: pd.DataFrame,
    plano_df: pd.DataFrame,
    credor_df: pd.DataFrame,
    lanc_df: pd.DataFrame,
    params: Parametros,
) -> None:
    resumo = construir_resumo(plano_df, credor_df, lanc_df)

    mes_rename = {m: MES_LABEL[m] for m in MESES}
    plano_export = plano_df.rename(
        columns={
            "plano_codigo": "Código",
            "plano": "Plano de Contas",
            **mes_rename,
            MEDIANA_COL: MEDIANA_EXCEL_NOME,
            "flags": "Flags",
            "qtd_flags": "Qtd Flags",
            "severidade": "Severidade",
        }
    )

    credor_export = credor_df.rename(
        columns={
            "credor": "Credor",
            "plano_codigo": "Código Plano",
            "plano": "Plano de Contas",
            **mes_rename,
            "meses_presentes": "Meses Presentes",
            MEDIANA_COL: MEDIANA_EXCEL_NOME,
            "qtd_planos_distintos": "Qtd Planos Distintos",
            "flags": "Flags",
            "qtd_flags": "Qtd Flags",
            "severidade": "Severidade",
        }
    )

    lanc_export = lanc_df.rename(
        columns={
            "plano_codigo": "Código Plano",
            "credor": "Credor",
            "documento": "Documento",
            "historico_curto": "Histórico (resumido)",
            "mes": "Mês",
            "valor": "Valor",
            "media_grupo": "Média Grupo",
            "desvio_grupo": "Desvio Grupo",
            "n_grupo": "n",
            "zscore": "Z-Score",
            "flags": "Flags",
            "severidade": "Severidade",
        }
    )

    folhas_export = folhas.rename(
        columns={
            "plano_codigo": "Código Plano",
            "plano": "Plano de Contas",
            "credor": "Credor",
            "documento": "Documento",
            "historico_curto": "Histórico (resumido)",
            "historico": "Histórico (completo)",
            **mes_rename,
        }
    )

    totais_rows = [
        (f"Total {MES_LABEL[m]}", f"R$ {folhas[m].sum():,.2f}") for m in MESES
    ]
    parametros_df = pd.DataFrame(
        {
            "Parâmetro": [
                "Arquivo de origem",
                "Limiar de variação",
                "Valor mínimo relevante",
                "Z-Score mínimo",
                "Meses de referência (baseline)",
                "Meses sob auditoria (contraste)",
                "Lançamentos processados",
                *[p for p, _ in totais_rows],
            ],
            "Valor": [
                str(params.src),
                f"{params.limiar_pct * 100:.1f}%",
                f"R$ {params.valor_minimo:,.2f}",
                f"{params.zscore_lancamento:.2f}",
                ", ".join(MES_LABEL[m] for m in MES_REFERENCIA),
                ", ".join(MES_LABEL[m] for m in MESES_AUDITAR),
                len(folhas),
                *[v for _, v in totais_rows],
            ],
        }
    )

    params.dst.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(params.dst, engine="openpyxl") as writer:
        resumo.to_excel(writer, sheet_name="00 - Resumo", index=False)
        plano_export.to_excel(writer, sheet_name="01 - Plano por Mes", index=False)
        credor_export.to_excel(writer, sheet_name="02 - Credor x Plano", index=False)
        lanc_export.to_excel(writer, sheet_name="03 - Lancamentos Suspeitos", index=False)
        folhas_export.to_excel(writer, sheet_name="04 - Dados Achatados", index=False)
        parametros_df.to_excel(writer, sheet_name="05 - Parametros", index=False)

        wb = writer.book
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            _aplicar_cabecalho(ws)
            _ajustar_colunas(ws)

        # Formatação condicional por severidade
        mapping_sev = {
            "00 - Resumo": None,
            "01 - Plano por Mes": "Severidade",
            "02 - Credor x Plano": "Severidade",
            "03 - Lancamentos Suspeitos": "Severidade",
            "04 - Dados Achatados": None,
            "05 - Parametros": None,
        }
        for sheet, col_name in mapping_sev.items():
            if col_name is None:
                continue
            ws = wb[sheet]
            cabecalho = [c.value for c in ws[1]]
            if col_name in cabecalho:
                idx = cabecalho.index(col_name) + 1
                _colorir_severidade(ws, idx)

        # Formato contábil nas colunas monetárias
        colunas_monetarias = list(MES_LABEL.values()) + [MEDIANA_EXCEL_NOME]

        ws_plano = wb["01 - Plano por Mes"]
        cabecalho = [c.value for c in ws_plano[1]]
        cols_money = [
            cabecalho.index(c) + 1 for c in colunas_monetarias if c in cabecalho
        ]
        _aplicar_formato_contabil(ws_plano, cols_money)

        ws_credor = wb["02 - Credor x Plano"]
        cabecalho = [c.value for c in ws_credor[1]]
        cols_money = [
            cabecalho.index(c) + 1 for c in colunas_monetarias if c in cabecalho
        ]
        _aplicar_formato_contabil(ws_credor, cols_money)

        ws_lanc = wb["03 - Lancamentos Suspeitos"]
        cabecalho = [c.value for c in ws_lanc[1]]
        cols_money = [
            cabecalho.index(c) + 1
            for c in ("Valor", "Média Grupo", "Desvio Grupo")
            if c in cabecalho
        ]
        _aplicar_formato_contabil(ws_lanc, cols_money)

        ws_folhas = wb["04 - Dados Achatados"]
        cabecalho = [c.value for c in ws_folhas[1]]
        cols_money = [
            cabecalho.index(c) + 1
            for c in MES_LABEL.values()
            if c in cabecalho
        ]
        _aplicar_formato_contabil(ws_folhas, cols_money)


# ─── Validação e impressão de resumo ────────────────────────────────────────


def validar_integridade(df_original: pd.DataFrame, folhas: pd.DataFrame) -> dict[str, float]:
    """Confere se a soma das folhas reconcilia com o Grande Total do pivot."""
    grand_total_row = df_original[df_original["plano"].astype(str).eq("Grande Total")]
    if grand_total_row.empty:
        raise ValueError("Linha 'Grande Total' não encontrada no pivot original.")
    grand = grand_total_row.iloc[0]
    diffs = {}
    for m in MESES:
        soma_folhas = folhas[m].sum()
        esperado = grand[m] if not pd.isna(grand[m]) else 0.0
        diffs[m] = float(soma_folhas - esperado)
    return diffs


def imprimir_resumo(
    folhas: pd.DataFrame,
    plano_df: pd.DataFrame,
    credor_df: pd.DataFrame,
    lanc_df: pd.DataFrame,
    diffs: dict[str, float],
    params: Parametros,
) -> None:
    print()
    print("=" * 72)
    print("AUDITORIA DE CUSTOS FIXOS ADMINISTRATIVOS — Resumo")
    print("=" * 72)
    print(f"Origem  : {params.src}")
    print(f"Saída   : {params.dst}")
    print(f"Folhas  : {len(folhas)} lançamentos")
    print()
    print("Reconciliação (folhas vs. Grande Total):")
    for m in MESES:
        sinal = "OK " if abs(diffs[m]) < 0.01 else "!! "
        print(f"  {sinal}{MES_LABEL[m]:<10} diferença = R$ {diffs[m]:+,.2f}")
    print()

    print("Top 5 planos com mais flags:")
    if plano_df.empty:
        print("  (nenhum)")
    else:
        for _, row in plano_df.head(5).iterrows():
            print(
                f"  [{row['severidade']:<5}] {row['plano']}: {row['flags']}"
                if row["flags"]
                else f"  [---] {row['plano']}: (sem divergências)"
            )
    print()

    print("Top 5 credores com mais flags:")
    if credor_df.empty:
        print("  (nenhum)")
    else:
        for _, row in credor_df.head(5).iterrows():
            print(
                f"  [{row['severidade']:<5}] {row['credor']} ({row['plano_codigo']}): {row['flags']}"
            )
    print()

    print("Top 5 lançamentos suspeitos:")
    if lanc_df.empty:
        print("  (nenhum)")
    else:
        for _, row in lanc_df.head(5).iterrows():
            print(
                f"  [{row['severidade']:<5}] {row['mes']} | {row['plano_codigo']} | "
                f"{row['credor']} | R$ {row['valor']:,.2f} | {row['flags']}"
            )
    print("=" * 72)


# ─── Entry point ────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Audita custos fixos administrativos detectando divergências "
            "entre os meses no pivot do Excel."
        )
    )
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC)
    parser.add_argument("--dst", type=Path, default=DEFAULT_DST)
    parser.add_argument("--limiar-pct", type=float, default=LIMIAR_VARIACAO_PCT)
    parser.add_argument("--valor-minimo", type=float, default=LIMIAR_VALOR_MINIMO)
    parser.add_argument("--zscore", type=float, default=LIMIAR_ZSCORE_LANCAMENTO)
    args = parser.parse_args()

    params = Parametros(
        src=args.src,
        dst=args.dst,
        limiar_pct=args.limiar_pct,
        valor_minimo=args.valor_minimo,
        zscore_lancamento=args.zscore,
    )

    if not params.src.exists():
        raise FileNotFoundError(f"Arquivo de origem não encontrado: {params.src}")

    df_original = carregar_pivot(params.src)
    folhas = achatar_pivot(df_original)
    diffs = validar_integridade(df_original, folhas)

    plano_df = analisar_plano(folhas, params)
    credor_df = analisar_credor_plano(folhas, params)
    lanc_df = analisar_lancamentos(folhas, params)

    gerar_excel(folhas, plano_df, credor_df, lanc_df, params)
    imprimir_resumo(folhas, plano_df, credor_df, lanc_df, diffs, params)


if __name__ == "__main__":
    main()
