"""
Gera dashboard Excel para apresentação executiva (reunião ~10 min).

Saída: outputs/tabelas/dashboard_liebherr_hyundai.xlsx

Abas:
  - Apresentação: KPIs + gráficos-chave
  - Mix por conta: gráficos nativos (% volume e R$/máquina, rótulos nas barras)
  - Gasto por Local: hierarquia Local → Marca → Máquina (expandir/recolher)
  - Fonte_Dados: tabela plana para Tabela Dinâmica no Excel
  - Gráficos: figuras do notebook
  - Como usar: instruções de filtro / pivot / slicer

CLI:
  --mix-only   atualiza só a aba Mix por conta (preserva edições manuais)
  --preservar  alias de preservar_abas_existentes na exportação completa
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "02-Referencias" / "Custos-Maquinas" / "relatorio_marcas_maquinas_base.xlsx"
OUT = ROOT / "outputs" / "tabelas" / "dashboard_liebherr_hyundai.xlsx"
FIG_DIR = ROOT / "outputs" / "figuras" / "liebherr_hyundai"

MARCAS = ["LIEBHERR", "HYUNDAI"]
CORES_MARCA = {"HYUNDAI": "004B8D", "LIEBHERR": "F4C430"}
PARQUE = {
    "LIEBHERR": ["EHL0013", "EHL0014", "EHL0028", "EHL0041", "EHL0042", "EHL0043", "EHL0070"],
    "HYUNDAI": [
        "EHH0002", "EHH0003", "EHH0004", "EHH0006", "EHH0007", "EHH0008", "EHH0009",
        "EHH0015", "EHH0019", "EHH0036", "EHH0037", "EHH0038", "EHH0039", "EHH0040",
        "EHH0044", "EHH0046",
    ],
}
QTD_PARQUE = {m: len(v) for m, v in PARQUE.items()}
LOCAL_POR_MAQUINA = {
    "EHH0006": "Prudente", "EHH0009": "Prudente", "EHH0002": "Maringá", "EHH0004": "Maringá",
    "EHH0039": "Maringá", "EHH0008": "Londrina", "EHH0040": "Londrina", "EHH0036": "Dourados",
    "EHH0044": "Dourados", "EHH0038": "Campo Grande", "EHH0046": "Campo Grande",
    "EHH0015": "Ambar", "EHH0019": "Ambar", "EHH0003": "Tupy", "EHH0007": "Matheus",
    "EHH0037": "Multi Aço", "EHL0028": "Prudente", "EHL0043": "Maringá", "EHL0070": "Maringá",
    "EHL0042": "Dourados", "EHL0041": "Tupy", "EHL0013": "Pátio de Manutenção",
    "EHL0014": "Pátio de Manutenção",
}
ORDEM_LOCAIS = [
    "Prudente", "Maringá", "Londrina", "Dourados", "Campo Grande",
    "Ambar", "Tupy", "Pátio de Manutenção", "Matheus", "Multi Aço",
]
CONTAS_EXCLUIR = frozenset({"7.4.5"})
SHEET_MIX_CONTAS = "Mix por conta"
ROTULOS_CONTA = {
    "7.1.1": "7.1.1 Peças de manutenção",
    "7.1.18": "7.1.18 Fretes e carretos",
    "7.1.2": "7.1.2 Manutenção veíc./máq.",
    "7.1.22": "7.1.22 Diesel (interno)",
    "7.1.4": "7.1.4 Diesel (posto)",
}

FIGURAS_APRESENTACAO = [
    "01_volume_por_ano.png",
    "04_serie_mensal_2025.png",
    "04_serie_mensal_2026.png",
    "03_volume_por_conta.png",
]
FIGURAS_TODAS = [
    "01_volume_por_ano.png", "02_mix_contas_pct.png", "03_volume_por_conta.png",
    "04_serie_mensal_2025.png", "04_serie_mensal_2026.png", "05_top_maquinas.png",
    "05_top_maquinas_2025.png", "05_top_maquinas_2026.png",
    "09_mes_maquinas_liebherr.png", "09_mes_maquinas_hyundai.png",
]


def extrair_id_maquina(valor) -> str | None:
    s = re.sub(r"\s+", "", str(valor).strip().upper())
    m = re.match(r"^(EHL\d+|EHH\d+)", s)
    return m.group(1) if m else None


def carregar_df_maq() -> pd.DataFrame:
    raw = pd.read_excel(BASE, sheet_name="base_maquinas_2025_2026")
    raw["valor_conta_num"] = pd.to_numeric(raw["valor_conta"], errors="coerce")
    raw["gasto_abs"] = raw["valor_conta_num"].abs()
    raw["data_nf"] = pd.to_datetime(raw["data_nf"], errors="coerce", dayfirst=True)
    raw["MARCA"] = raw["MARCA"].astype(str).str.strip().str.upper()
    raw["ano_nf"] = raw["data_nf"].dt.year
    raw["mes_nf"] = raw["data_nf"].dt.to_period("M").astype(str)
    raw["maq_id"] = raw["n4_centro_custo"].map(extrair_id_maquina)
    raw["no_parque"] = raw.apply(
        lambda r: r["maq_id"] in PARQUE.get(r["MARCA"], []) if pd.notna(r["maq_id"]) else False,
        axis=1,
    )
    df = raw[raw["no_parque"] & raw["MARCA"].isin(MARCAS)].copy()
    cod = df["cod_conta"].astype(str).str.strip()
    df = df[~cod.isin(CONTAS_EXCLUIR)].copy()
    df["local_operacao"] = df["maq_id"].map(LOCAL_POR_MAQUINA)
    return df


def montar_fonte_dados(df: pd.DataFrame) -> pd.DataFrame:
    return df[
        [
            "ano_nf", "mes_nf", "local_operacao", "MARCA", "maq_id", "Divisao", "filial",
            "cod_conta", "conta", "gasto_abs", "valor_conta_num",
        ]
    ].rename(columns={
        "ano_nf": "Ano",
        "mes_nf": "Mês",
        "local_operacao": "Local",
        "MARCA": "Marca",
        "maq_id": "Máquina",
        "Divisao": "Divisão",
        "filial": "Filial_SAGI",
        "cod_conta": "Conta_Código",
        "conta": "Conta",
        "gasto_abs": "Gasto_Abs",
        "valor_conta_num": "Valor_Conta",
    }).sort_values(["Local", "Marca", "Máquina", "Ano", "Mês"])


def media_mensal_grupo(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    agg = (
        df.groupby(group_cols + ["ano_nf"], observed=True)
        .agg(
            gasto_total=("gasto_abs", "sum"),
            meses_com_gasto=("mes_nf", "nunique"),
        )
        .reset_index()
    )
    agg["media_mensal"] = agg["gasto_total"] / agg["meses_com_gasto"].clip(lower=1)
    return agg


def montar_hierarquia_local(df: pd.DataFrame) -> tuple[pd.DataFrame, list[int]]:
    """Retorna tabela hierárquica e níveis de outline (0=local, 1=marca, 2=máquina)."""
    anos = sorted(int(a) for a in df["ano_nf"].dropna().unique())
    col_media = [f"Média mensal {a}" for a in anos]
    col_gasto = [f"Gasto total {a}" for a in anos]
    col_meses = [f"Meses c/ gasto {a}" for a in anos]
    cols = ["Local", "Nível", "Marca", "Máquina", *col_gasto, *col_meses, *col_media]

    maq_agg = media_mensal_grupo(df, ["local_operacao", "MARCA", "maq_id"])
    loc_marca_agg = media_mensal_grupo(df, ["local_operacao", "MARCA"])
    loc_agg = media_mensal_grupo(df, ["local_operacao"])

    def linha_valores(agg: pd.DataFrame, filt: dict, ano: int) -> tuple[float, int, float]:
        sub = agg
        for k, v in filt.items():
            sub = sub[sub[k] == v]
        sub = sub[sub["ano_nf"] == ano]
        if sub.empty:
            return 0.0, 0, 0.0
        r = sub.iloc[0]
        return float(r["gasto_total"]), int(r["meses_com_gasto"]), float(r["media_mensal"])

    rows: list[dict] = []
    levels: list[int] = []
    ordem = {loc: i for i, loc in enumerate(ORDEM_LOCAIS)}

    for local in sorted(df["local_operacao"].dropna().unique(), key=lambda x: ordem.get(x, 99)):
        row_local: dict = {"Local": local, "Nível": "LOCAL", "Marca": "", "Máquina": ""}
        for i, ano in enumerate(anos):
            g, m, med = linha_valores(loc_agg, {"local_operacao": local}, ano)
            row_local[col_gasto[i]] = g
            row_local[col_meses[i]] = m
            row_local[col_media[i]] = med
        rows.append(row_local)
        levels.append(0)

        for marca in MARCAS:
            sub_m = maq_agg[(maq_agg["local_operacao"] == local) & (maq_agg["MARCA"] == marca)]
            if sub_m.empty:
                continue
            row_m: dict = {"Local": local, "Nível": "MARCA", "Marca": marca, "Máquina": ""}
            for i, ano in enumerate(anos):
                g, m, med = linha_valores(loc_marca_agg, {"local_operacao": local, "MARCA": marca}, ano)
                row_m[col_gasto[i]] = g
                row_m[col_meses[i]] = m
                row_m[col_media[i]] = med
            rows.append(row_m)
            levels.append(1)

            for mid in sorted(sub_m["maq_id"].unique()):
                row_q: dict = {"Local": local, "Nível": "MÁQUINA", "Marca": marca, "Máquina": mid}
                for i, ano in enumerate(anos):
                    g, m, med = linha_valores(
                        maq_agg,
                        {"local_operacao": local, "MARCA": marca, "maq_id": mid},
                        ano,
                    )
                    row_q[col_gasto[i]] = g
                    row_q[col_meses[i]] = m
                    row_q[col_media[i]] = med
                rows.append(row_q)
                levels.append(2)

    return pd.DataFrame(rows, columns=cols), levels


def montar_pivot_local_ano(df: pd.DataFrame) -> pd.DataFrame:
    """Visão larga: Local × (Ano, Marca) = média mensal — estilo pivot da imagem."""
    maq = media_mensal_grupo(df, ["local_operacao", "MARCA", "maq_id"])
    loc_marca = media_mensal_grupo(df, ["local_operacao", "MARCA"])
    anos = sorted(int(a) for a in df["ano_nf"].dropna().unique())
    ordem = {loc: i for i, loc in enumerate(ORDEM_LOCAIS)}

    linhas: list[dict] = []
    for local in sorted(df["local_operacao"].dropna().unique(), key=lambda x: ordem.get(x, 99)):
        for marca in MARCAS:
            sub = loc_marca[(loc_marca["local_operacao"] == local) & (loc_marca["MARCA"] == marca)]
            if sub.empty:
                continue
            row = {"Local": local, "Marca": marca, "Máquinas": int(
                maq[(maq["local_operacao"] == local) & (maq["MARCA"] == marca)]["maq_id"].nunique()
            )}
            for ano in anos:
                s = sub[sub["ano_nf"] == ano]
                row[f"Média mensal {ano}"] = float(s["media_mensal"].iloc[0]) if len(s) else 0.0
                row[f"Gasto total {ano}"] = float(s["gasto_total"].iloc[0]) if len(s) else 0.0
            linhas.append(row)
    return pd.DataFrame(linhas)


def rotulo_conta_grafico(cod: str, conta: str) -> str:
    cod = str(cod).strip()
    if cod in ROTULOS_CONTA:
        return ROTULOS_CONTA[cod]
    return f"{cod} {str(conta)[:35]}"


def montar_dados_mix_contas(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Top 6 rubricas: % do volume da marca e R$ médio/máquina (parque)."""
    por_conta = (
        df.groupby(["MARCA", "cod_conta", "conta"], observed=True)["gasto_abs"]
        .sum()
        .reset_index(name="volume")
    )
    por_conta["volume_por_maq"] = por_conta["volume"] / por_conta["MARCA"].map(QTD_PARQUE)

    top_contas = (
        por_conta.groupby("conta", observed=True)["volume"].sum().nlargest(6).index.tolist()
    )
    comp = por_conta[por_conta["conta"].isin(top_contas)].copy()
    comp["conta_curta"] = comp.apply(
        lambda r: rotulo_conta_grafico(r["cod_conta"], r["conta"]), axis=1
    )

    ordem = (
        comp.groupby("conta_curta", observed=True)["volume"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )

    pivot_vol = comp.pivot(index="conta_curta", columns="MARCA", values="volume_por_maq").fillna(0)
    pivot_vol = pivot_vol.reindex(ordem).reindex(columns=MARCAS, fill_value=0)

    pivot_comp = comp.pivot(index="conta_curta", columns="MARCA", values="volume").fillna(0)
    pivot_comp = pivot_comp.reindex(ordem).reindex(columns=MARCAS, fill_value=0)
    pivot_pct = pivot_comp.div(pivot_comp.sum(axis=0), axis=1) * 100

    pct_out = pivot_pct.reset_index().rename(columns={"conta_curta": "Conta"})
    vol_out = pivot_vol.reset_index().rename(columns={"conta_curta": "Conta"})
    return pct_out, vol_out


def _chart_data_labels(chart: BarChart, num_fmt: str | None = None) -> None:
    dl = DataLabelList()
    dl.showVal = True
    dl.showCatName = False
    dl.showSerName = False
    dl.showLegendKey = False
    dl.showPercent = False
    dl.dLblPos = "outEnd"
    if num_fmt:
        dl.numFmt = num_fmt
    chart.dataLabels = dl


def _cor_serie_marca(chart: BarChart) -> None:
    for i, marca in enumerate(MARCAS):
        if i < len(chart.series):
            chart.series[i].graphicalProperties.solidFill = CORES_MARCA.get(marca, "888888")


def escrever_mix_contas_interativo(wb: Workbook, df: pd.DataFrame, pos: int | None = 1) -> None:
    """Aba com gráficos nativos Excel: mix % e R$/máquina (legenda clicável)."""
    if SHEET_MIX_CONTAS in wb.sheetnames:
        del wb[SHEET_MIX_CONTAS]
    ws = wb.create_sheet(SHEET_MIX_CONTAS, pos)

    ws["A1"] = "Mix de gastos por tipo de conta — gráficos interativos (clique na legenda para ocultar/mostrar marca)"
    ws["A1"].font = Font(bold=True, size=12, color="004B8D")
    ws.merge_cells("A1:F1")
    ws["A2"] = (
        "Top 6 rubricas do parque (sem ISS). Valores nas barras. "
        "Filtre as tabelas abaixo pelo cabeçalho (▼) para refinar a visualização."
    )
    ws["A2"].font = Font(italic=True, size=10, color="555555")
    ws.merge_cells("A2:F2")

    pct_df, vol_df = montar_dados_mix_contas(df)

    start_pct = 4
    ws.cell(start_pct, 1, "% do volume da marca").font = Font(bold=True)
    for r_idx, row in enumerate(dataframe_to_rows(pct_df, index=False, header=True), start_pct + 1):
        for c_idx, val in enumerate(row, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            if c_idx > 1 and r_idx > start_pct + 1:
                cell.number_format = "0.0"

    n_pct = len(pct_df)
    end_pct = start_pct + 1 + n_pct
    tab_pct = Table(
        displayName="TabMixPct",
        ref=f"A{start_pct + 1}:{get_column_letter(len(pct_df.columns))}{end_pct}",
    )
    tab_pct.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(tab_pct)

    start_vol = end_pct + 3
    ws.cell(start_vol, 1, "R$ médio / máquina do parque").font = Font(bold=True)
    for r_idx, row in enumerate(dataframe_to_rows(vol_df, index=False, header=True), start_vol + 1):
        for c_idx, val in enumerate(row, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            if c_idx > 1 and r_idx > start_vol + 1:
                cell.number_format = '#,##0'

    n_vol = len(vol_df)
    end_vol = start_vol + 1 + n_vol
    tab_vol = Table(
        displayName="TabMixVol",
        ref=f"A{start_vol + 1}:{get_column_letter(len(vol_df.columns))}{end_vol}",
    )
    tab_vol.tableStyleInfo = TableStyleInfo(name="TableStyleMedium9", showRowStripes=True)
    ws.add_table(tab_vol)

    chart_pct = BarChart()
    chart_pct.type = "col"
    chart_pct.grouping = "clustered"
    chart_pct.title = "Mix de gastos por tipo de conta (top 6 rubricas)"
    chart_pct.y_axis.title = "% do volume da marca"
    chart_pct.x_axis.title = "Conta"
    data_pct = Reference(ws, min_col=2, max_col=1 + len(MARCAS), min_row=start_pct + 1, max_row=end_pct)
    cats_pct = Reference(ws, min_col=1, min_row=start_pct + 2, max_row=end_pct)
    chart_pct.add_data(data_pct, titles_from_data=True)
    chart_pct.set_categories(cats_pct)
    chart_pct.height = 11
    chart_pct.width = 18
    _chart_data_labels(chart_pct, num_fmt="0.0")
    _cor_serie_marca(chart_pct)
    ws.add_chart(chart_pct, f"E{start_pct}")

    chart_vol = BarChart()
    chart_vol.type = "bar"
    chart_vol.grouping = "clustered"
    chart_vol.title = "Gasto por conta — custo médio por máquina"
    chart_vol.x_axis.title = "R$ médio / máquina"
    chart_vol.y_axis.title = "Conta"
    data_vol = Reference(ws, min_col=2, max_col=1 + len(MARCAS), min_row=start_vol + 1, max_row=end_vol)
    cats_vol = Reference(ws, min_col=1, min_row=start_vol + 2, max_row=end_vol)
    chart_vol.add_data(data_vol, titles_from_data=True)
    chart_vol.set_categories(cats_vol)
    chart_vol.height = 11
    chart_vol.width = 18
    _chart_data_labels(chart_vol, num_fmt="#,##0")
    _cor_serie_marca(chart_vol)
    ws.add_chart(chart_vol, f"E{start_vol}")

    ws.column_dimensions["A"].width = 34
    for col in ("B", "C"):
        ws.column_dimensions[col].width = 14


def atualizar_aba_mix_contas(dest: Path | None = None) -> Path:
    """Adiciona/atualiza só a aba Mix por conta, preservando demais abas do arquivo."""
    dest = dest or OUT
    if not dest.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {dest}")

    df = carregar_df_maq()
    wb = load_workbook(dest)
    escrever_mix_contas_interativo(wb, df, pos=1)
    try:
        wb.save(dest)
    except PermissionError:
        alt = dest.with_stem(f"{dest.stem}_mix_{datetime.now():%Y%m%d_%H%M%S}")
        wb.save(alt)
        print(f"Arquivo bloqueado; salvo em: {alt}")
        return alt
    return dest


def montar_kpis(df: pd.DataFrame) -> list[tuple[str, str]]:
    vol_maq = df.groupby("MARCA", observed=True)["gasto_abs"].sum()
    meses = df.groupby("MARCA", observed=True)["mes_nf"].nunique()
    custo_mes = {
        m: vol_maq.get(m, 0) / max(meses.get(m, 1), 1) / QTD_PARQUE[m]
        for m in MARCAS
    }
    loc = media_mensal_grupo(df, ["local_operacao"])
    loc_total = loc.groupby("local_operacao", observed=True)["gasto_total"].sum()
    top_local = loc_total.idxmax() if len(loc_total) else "—"

    c_l, c_h = custo_mes["LIEBHERR"], custo_mes["HYUNDAI"]
    diff = abs(c_l - c_h) / min(c_l, c_h) * 100 if min(c_l, c_h) else 0
    maior = "LIEBHERR" if c_l >= c_h else "HYUNDAI"

    return [
        ("Comparativo justo", f"{maior} ~{diff:.0f}% mais cara (média mensal/máq do parque)"),
        ("LIEBHERR", f"R$ {c_l:,.0f} / máq / mês  ({QTD_PARQUE['LIEBHERR']} máq.)"),
        ("HYUNDAI", f"R$ {c_h:,.0f} / máq / mês  ({QTD_PARQUE['HYUNDAI']} máq.)"),
        ("Unidade líder em gasto", str(top_local)),
        ("Período", f"{df['mes_nf'].min()} → {df['mes_nf'].max()} (sem ISS)"),
    ]


def _fmt_moeda_cols(ws, df: pd.DataFrame, start_row: int, money_cols: list[str]) -> None:
    col_idx = {name: i + 1 for i, name in enumerate(df.columns)}
    for name in money_cols:
        if name not in col_idx:
            continue
        letter = get_column_letter(col_idx[name])
        for r in range(start_row + 1, start_row + len(df) + 1):
            ws[f"{letter}{r}"].number_format = '#,##0'


def _add_table(ws, df: pd.DataFrame, name: str, start_cell: str = "A1") -> None:
    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
        for c_idx, val in enumerate(row, 1):
            ws.cell(row=r_idx, column=c_idx, value=val)
    end_col = get_column_letter(len(df.columns))
    end_row = len(df) + 1
    tab = Table(displayName=name, ref=f"A1:{end_col}{end_row}")
    tab.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    ws.add_table(tab)


def _autosize(ws, max_width: int = 22) -> None:
    for col in ws.columns:
        letter = get_column_letter(col[0].column)
        width = min(max(len(str(c.value or "")) for c in col) + 2, max_width)
        ws.column_dimensions[letter].width = width


def escrever_apresentacao(wb: Workbook, kpis: list[tuple[str, str]]) -> None:
    ws = wb.active
    ws.title = "Apresentação"
    ws["A1"] = "Liebherr × Hyundai — Dashboard executivo"
    ws["A1"].font = Font(bold=True, size=16)
    ws["A2"] = f"Atualizado em {datetime.now():%d/%m/%Y %H:%M}  |  Uso: reunião ~10 min"
    ws["A2"].font = Font(italic=True, color="555555")

    r = 4
    ws.cell(r, 1, "Mensagem principal").font = Font(bold=True, size=12)
    r += 1
    ws.cell(r, 1, "Compare marcas pelo custo médio mensal por máquina do parque (÷7 ou ÷16), não pelo total bruto.")
    r += 2
    ws.cell(r, 1, "Indicador").font = Font(bold=True)
    ws.cell(r, 2, "Valor").font = Font(bold=True)
    r += 1
    for label, val in kpis:
        ws.cell(r, 1, label)
        ws.cell(r, 2, val)
        r += 1

    img_row = 4
    for i, fname in enumerate(FIGURAS_APRESENTACAO):
        path = FIG_DIR / fname
        if not path.exists():
            continue
        col = 4 + (i % 2) * 18
        row = img_row + (i // 2) * 16
        img = XLImage(str(path))
        img.width = min(img.width, 480)
        img.height = min(img.height, 280)
        ws.add_image(img, f"{get_column_letter(col)}{row}")

    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 42


def escrever_hierarquia(wb: Workbook, hier: pd.DataFrame, levels: list[int]) -> None:
    ws = wb.create_sheet("Gasto por Local")
    ws["A1"] = "Expanda/recolha: Local → Marca → Máquina  |  Filtros: cabeçalho da tabela (▼)"
    ws["A1"].font = Font(bold=True, color="004B8D")
    ws.merge_cells("A1:H1")

    start = 3
    for r_idx, row in enumerate(dataframe_to_rows(hier, index=False, header=True), start):
        for c_idx, val in enumerate(row, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            if r_idx == start and c_idx >= 5:
                cell.font = Font(bold=True)
        if r_idx > start:
            data_i = r_idx - start - 1
            if data_i < len(levels):
                ws.row_dimensions[r_idx].outlineLevel = levels[data_i]
                nivel = hier.iloc[data_i]["Nível"]
                if nivel == "LOCAL":
                    for c in range(1, 5):
                        ws.cell(r_idx, c).font = Font(bold=True)
                    fill = PatternFill("solid", fgColor="E8EEF7")
                    for c in range(1, len(hier.columns) + 1):
                        ws.cell(r_idx, c).fill = fill
                elif nivel == "MARCA":
                    ws.cell(r_idx, 3).font = Font(bold=True, color=CORES_MARCA.get(str(hier.iloc[data_i]["Marca"]), "000000"))

    ws.sheet_properties.outlinePr.summaryBelow = False
    ws.sheet_properties.outlinePr.applyStyles = True

    money = [c for c in hier.columns if c.startswith(("Gasto", "Média"))]
    _fmt_moeda_cols(ws, hier, start, money)
    end_row = start + len(hier)
    end_col = get_column_letter(len(hier.columns))
    tab = Table(displayName="TabHierarquia", ref=f"A{start}:{end_col}{end_row}")
    tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium9", showRowStripes=True)
    ws.add_table(tab)
    _autosize(ws)


def escrever_pivot_resumo(wb: Workbook, pivot: pd.DataFrame) -> None:
    ws = wb.create_sheet("Resumo Local×Marca")
    ws["A1"] = "Média mensal por unidade e marca (visão pivot)"
    ws["A1"].font = Font(bold=True)
    start = 3
    for r_idx, row in enumerate(dataframe_to_rows(pivot, index=False, header=True), start):
        for c_idx, val in enumerate(row, 1):
            ws.cell(row=r_idx, column=c_idx, value=val)
    money = [c for c in pivot.columns if "Média" in c or "Gasto" in c]
    _fmt_moeda_cols(ws, pivot, start, money)
    end_col = get_column_letter(len(pivot.columns))
    tab = Table(displayName="TabPivotLocal", ref=f"A{start}:{end_col}{start + len(pivot)}")
    tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(tab)

    # Gráfico de barras — média mensal 2025 por local (soma das marcas não faz sentido; usar pivot filtrado)
    if "Média mensal 2025" in pivot.columns:
        chart = BarChart()
        chart.type = "col"
        chart.title = "Média mensal 2025 — por local e marca"
        chart.y_axis.title = "R$"
        chart.x_axis.title = "Local"
        data_ref = Reference(ws, min_col=pivot.columns.get_loc("Média mensal 2025") + 1,
                             min_row=start, max_row=start + len(pivot))
        cats = Reference(ws, min_col=1, min_row=start + 1, max_row=start + len(pivot))
        chart.add_data(data_ref, titles_from_data=True)
        chart.set_categories(cats)
        chart.height = 12
        chart.width = 22
        ws.add_chart(chart, f"{get_column_letter(len(pivot.columns) + 2)}{start}")
    _autosize(ws)


def escrever_fonte_dados(wb: Workbook, fonte: pd.DataFrame) -> None:
    ws = wb.create_sheet("Fonte_Dados")
    ws["A1"] = (
        "Selecione qualquer célula → Inserir → Tabela Dinâmica. "
        "Sugestão: Linhas Local > Marca > Máquina | Colunas Ano | Valores Média de Gasto_Abs (ou soma)."
    )
    ws["A1"].font = Font(italic=True, color="333333")
    ws.merge_cells("A1:L1")
    start = 3
    for r_idx, row in enumerate(dataframe_to_rows(fonte, index=False, header=True), start):
        for c_idx, val in enumerate(row, 1):
            ws.cell(row=r_idx, column=c_idx, value=val)
    end_col = get_column_letter(len(fonte.columns))
    tab = Table(displayName="TabFonteDados", ref=f"A{start}:{end_col}{start + len(fonte)}")
    tab.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
    ws.add_table(tab)
    _autosize(ws, 18)


def montar_gasto_mes_maquina_long(df: pd.DataFrame) -> pd.DataFrame:
    tab = (
        df.groupby(["mes_nf", "MARCA", "maq_id", "local_operacao"], observed=True)["gasto_abs"]
        .sum()
        .reset_index()
        .rename(columns={
            "mes_nf": "Mês",
            "MARCA": "Marca",
            "maq_id": "Máquina",
            "local_operacao": "Local",
            "gasto_abs": "Gasto",
        })
        .sort_values(["Marca", "Máquina", "Mês"])
    )
    return tab


def escrever_gasto_mes_maquina(wb: Workbook, df: pd.DataFrame) -> None:
    """Parque completo por marca + base para pivot/slicer; gráfico com legenda clicável."""
    long = montar_gasto_mes_maquina_long(df)

    ws_long = wb.create_sheet("Gasto_mês_máquina")
    ws_long["A1"] = (
        "Parque completo (sem top N). Inserir → Tabela Dinâmica → Slicer em Máquina para escolher quais linhas ver."
    )
    ws_long["A1"].font = Font(italic=True, color="004B8D")
    ws_long.merge_cells("A1:F1")
    start = 3
    for r_idx, row in enumerate(dataframe_to_rows(long, index=False, header=True), start):
        for c_idx, val in enumerate(row, 1):
            ws_long.cell(row=r_idx, column=c_idx, value=val)
    end_col = get_column_letter(len(long.columns))
    tab = Table(displayName="TabGastoMesMaquina", ref=f"A{start}:{end_col}{start + len(long)}")
    tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium4", showRowStripes=True)
    ws_long.add_table(tab)
    _fmt_moeda_cols(ws_long, long, start, ["Gasto"])
    _autosize(ws_long)

    por_mes = (
        df.groupby(["MARCA", "maq_id", "mes_nf"], observed=True)["gasto_abs"]
        .sum()
        .reset_index(name="gasto")
    )
    for marca in MARCAS:
        ids = PARQUE.get(marca, [])
        sub = por_mes[por_mes["MARCA"] == marca]
        if sub.empty:
            continue
        wide = (
            sub.pivot(index="mes_nf", columns="maq_id", values="gasto")
            .reindex(columns=ids)
            .fillna(0)
            .sort_index()
            .reset_index()
            .rename(columns={"mes_nf": "Mês"})
        )
        nome_aba = f"Mês×Maq {marca[:4]}"
        ws = wb.create_sheet(nome_aba)
        ws["A1"] = (
            f"Todas as {len(ids)} máquinas {marca}. Clique nos itens da legenda do gráfico para "
            "mostrar/ocultar máquinas. Ou use a aba Gasto_mês_máquina com Slicer."
        )
        ws["A1"].font = Font(italic=True, size=10)
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=min(8, len(wide.columns)))
        tbl_start = 3
        for r_idx, row in enumerate(dataframe_to_rows(wide, index=False, header=True), tbl_start):
            for c_idx, val in enumerate(row, 1):
                ws.cell(row=r_idx, column=c_idx, value=val)
        money_cols = [c for c in wide.columns if c != "Mês"]
        _fmt_moeda_cols(ws, wide, tbl_start, money_cols)

        chart = LineChart()
        chart.title = f"Gasto mensal — parque {marca} ({len(ids)} máq.)"
        chart.y_axis.title = "R$"
        chart.x_axis.title = "Mês"
        n_rows = len(wide)
        for col in range(2, len(wide.columns) + 1):
            data = Reference(ws, min_col=col, min_row=tbl_start, max_row=tbl_start + n_rows)
            chart.add_data(data, titles_from_data=True)
        cats = Reference(ws, min_col=1, min_row=tbl_start + 1, max_row=tbl_start + n_rows)
        chart.set_categories(cats)
        chart.height = 16
        chart.width = 28
        ws.add_chart(chart, f"{get_column_letter(len(wide.columns) + 2)}{tbl_start}")
        _autosize(ws, 14)


def escrever_serie_mensal_chart(wb: Workbook, df: pd.DataFrame) -> None:
    por_mes = (
        df.groupby(["mes_nf", "MARCA"], observed=True)["gasto_abs"]
        .sum()
        .reset_index()
        .sort_values("mes_nf")
    )
    por_mes["media_maq"] = por_mes.apply(
        lambda r: r["gasto_abs"] / QTD_PARQUE[r["MARCA"]], axis=1
    )
    pivot = por_mes.pivot(index="mes_nf", columns="MARCA", values="media_maq").fillna(0).reset_index()

    ws = wb.create_sheet("Série mensal")
    for r_idx, row in enumerate(dataframe_to_rows(pivot, index=False, header=True), 1):
        for c_idx, val in enumerate(row, 1):
            ws.cell(row=r_idx, column=c_idx, value=val)

    chart = LineChart()
    chart.title = "Custo médio mensal por máquina do parque"
    chart.y_axis.title = "R$ / máq"
    chart.x_axis.title = "Mês"
    for col in range(2, len(pivot.columns) + 1):
        data = Reference(ws, min_col=col, min_row=1, max_row=len(pivot) + 1)
        chart.add_data(data, titles_from_data=True)
    cats = Reference(ws, min_col=1, min_row=2, max_row=len(pivot) + 1)
    chart.set_categories(cats)
    chart.height = 14
    chart.width = 24
    ws.add_chart(chart, "F2")
    _autosize(ws)


def escrever_graficos(wb: Workbook) -> None:
    ws = wb.create_sheet("Gráficos")
    row = 1
    for fname in FIGURAS_TODAS:
        path = FIG_DIR / fname
        if not path.exists():
            continue
        ws.cell(row, 1, fname.replace(".png", "").replace("_", " ")).font = Font(bold=True)
        img = XLImage(str(path))
        img.width = min(img.width, 640)
        img.height = min(img.height, 360)
        ws.add_image(img, f"A{row + 1}")
        row += 24
    ws.column_dimensions["A"].width = 30


def escrever_como_usar(wb: Workbook) -> None:
    ws = wb.create_sheet("Como usar")
    linhas = [
        ("1. Apresentação", "KPIs e 4 gráficos para abrir a reunião (~2 min)."),
        ("2. Gasto por Local", "Use +/- à esquerda para expandir Local → Marca → Máquina. Filtros no cabeçalho."),
        ("3. Resumo Local×Marca", "Tabela pivot pronta + gráfico de barras. Filtre por Local ou Marca."),
        ("4. Mês×Maq LIEB / HYUN", "Todas as máquinas da marca — clique na legenda para mostrar/ocultar linhas."),
        ("5. Gasto_mês_máquina", "Base longa → Tabela Dinâmica + Slicer em Máquina (escolha livre)."),
        ("6. Série mensal", "Comparativo Liebherr × Hyundai (média/máq do parque)."),
        ("7. Mix por conta", "Gráficos nativos: % do volume e R$/máquina — legenda clicável + filtros nas tabelas."),
        ("8. Fonte_Dados", "Pivot customizada com filtros por Divisão, Conta, Filial."),
        ("9. Gráficos", "Todas as figuras do notebook (parque completo, sem top N)."),
        ("", ""),
        ("Tabela Dinâmica sugerida (como na planilha do diretor)", ""),
        ("Linhas", "Local → Marca → Máquina"),
        ("Colunas", "Ano"),
        ("Valores", "Soma de Gasto_Abs (ou Média mensal calculada no Power Pivot)"),
        ("Filtros", "Divisão, Filial_SAGI, Conta"),
        ("", ""),
        ("Slicer de máquinas", "TabGastoMesMaquina → Pivot: Linhas=Mês, Colunas=Máquina, Filtro=Marca → Slicer Máquina."),
        ("Legenda clicável", "Nos gráficos Mês×Maq: um clique na legenda oculta a série; outro clique mostra de novo."),
        ("Gráfico dinâmico", "Inserir → Gráfico Dinâmico vinculado à pivot (interativo com slicers)."),
    ]
    ws["A1"] = "Como usar este dashboard"
    ws["A1"].font = Font(bold=True, size=14)
    for i, (a, b) in enumerate(linhas, 3):
        ws.cell(i, 1, a).font = Font(bold=True) if a and not a.startswith(" ") else Font()
        ws.cell(i, 2, b)
    ws.column_dimensions["A"].width = 36
    ws.column_dimensions["B"].width = 70


def exportar_dashboard(dest: Path | None = None, preservar_abas_existentes: bool = False) -> Path:
    dest = dest or OUT
    dest.parent.mkdir(parents=True, exist_ok=True)

    df = carregar_df_maq()

    if preservar_abas_existentes and dest.exists():
        return atualizar_aba_mix_contas(dest)

    fonte = montar_fonte_dados(df)
    hier, levels = montar_hierarquia_local(df)
    pivot = montar_pivot_local_ano(df)
    kpis = montar_kpis(df)

    wb = Workbook()
    escrever_apresentacao(wb, kpis)
    escrever_hierarquia(wb, hier, levels)
    escrever_pivot_resumo(wb, pivot)
    escrever_gasto_mes_maquina(wb, df)
    escrever_serie_mensal_chart(wb, df)
    escrever_mix_contas_interativo(wb, df, pos=6)
    escrever_fonte_dados(wb, fonte)
    escrever_graficos(wb)
    escrever_como_usar(wb)

    try:
        wb.save(dest)
    except PermissionError:
        alt = dest.with_stem(f"{dest.stem}_{datetime.now():%Y%m%d_%H%M%S}")
        wb.save(alt)
        print(f"Arquivo bloqueado; salvo em: {alt}")
        return alt
    return dest


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--mix-only":
        path = atualizar_aba_mix_contas()
    else:
        preservar = "--preservar" in sys.argv
        path = exportar_dashboard(preservar_abas_existentes=preservar)
    print(f"Dashboard Excel: {path.resolve()}")
