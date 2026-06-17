"""
Atualiza abas filtradas do dashboard Liebherr × Hyundai (mesmo layout de Gasto geral).

Abas:
  - Gastos com Manutenção — contas 7.1.1, 7.1.2, 7.1.18
  - Gastos com combustível — 7.1.4, 7.1.22 (+ abastecimento jan–mar/2026 da planilha de médias)
  - Gastos com Contratos — duas tabelas: Seletiva (G3S) e Contratos externos
"""
from __future__ import annotations

import re
import sys
from copy import copy
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from gerar_analise_contratos_diesel_maquinas import (  # noqa: E402
    carregar_catalogo_maquinas,
    carregar_media_consumo,
    parse_numero_br,
)

BASE = ROOT / "02-Referencias" / "Custos-Maquinas" / "relatorio_marcas_maquinas_base.xlsx"
OUT = ROOT / "outputs" / "tabelas" / "dashboard_liebherr_hyundai.xlsx"

PARQUE = {
    "LIEBHERR": ["EHL0013", "EHL0014", "EHL0028", "EHL0041", "EHL0042", "EHL0043", "EHL0070"],
    "HYUNDAI": [
        "EHH0002", "EHH0003", "EHH0004", "EHH0006", "EHH0007", "EHH0008", "EHH0009",
        "EHH0015", "EHH0019", "EHH0036", "EHH0037", "EHH0038", "EHH0039", "EHH0040",
        "EHH0044", "EHH0046",
    ],
}
ALL_MAQUINAS = {m for ids in PARQUE.values() for m in ids}

CONTAS_MANUTENCAO = frozenset({"7.1.1", "7.1.2", "7.1.18"})
CONTAS_COMBUSTIVEL = frozenset({"7.1.4", "7.1.22"})
CONTAS_GERAL = CONTAS_MANUTENCAO | CONTAS_COMBUSTIVEL
CONTAS_EXCLUIR = frozenset({"7.4.5"})

LOCAIS_SELETIVA = frozenset({
    "PRUDENTE", "MARINGÁ DISTRITO", "MARINGÁ", "MARINGÁ CIDADE ALTA",
    "LONDRINA", "DOURADOS", "CAMPO GRANDE", "PÁTIO DE MANUTENÇÃO",
})
LOCAIS_EXTERNO = frozenset({
    "ARCELOR BARRA MANSA", "TUPY", "MATHEUS", "MULTI AÇO",
})

LinhaGasto = tuple[str, str | None, int, list[str]]

LINHAS_GASTO: list[LinhaGasto] = [
    ("PRUDENTE", None, 4, ["EHL0028", "EHL0070", "EHH0009", "EHH0006"]),
    ("PRUDENTE", "LIEBHERR", 2, ["EHL0028", "EHL0070"]),
    ("PRUDENTE", "HYUNDAI", 2, ["EHH0009", "EHH0006"]),
    ("MARINGÁ DISTRITO", None, 3, ["EHL0043", "EHH0039", "EHH0002"]),
    ("MARINGÁ", "LIEBHERR", 1, ["EHL0043"]),
    ("MARINGÁ", "HYUNDAI", 2, ["EHH0039", "EHH0002"]),
    ("MARINGÁ CIDADE ALTA", None, 1, ["EHH0004"]),
    ("MARINGÁ CIDADE ALTA", "HYUNDAI", 1, ["EHH0004"]),
    ("LONDRINA", None, 2, ["EHH0008", "EHH0040"]),
    ("LONDRINA", "HYUNDAI", 2, ["EHH0008", "EHH0040"]),
    ("DOURADOS", None, 3, ["EHL0042", "EHH0036", "EHH0044"]),
    ("DOURADOS", "LIEBHERR", 1, ["EHL0042"]),
    ("DOURADOS", "HYUNDAI", 2, ["EHH0036", "EHH0044"]),
    ("CAMPO GRANDE", None, 2, ["EHH0038", "EHH0046"]),
    ("CAMPO GRANDE", "HYUNDAI", 2, ["EHH0038", "EHH0046"]),
    ("ARCELOR BARRA MANSA", None, 2, ["EHH0015", "EHH0019"]),
    ("ARCELOR BARRA MANSA", "HYUNDAI", 2, ["EHH0015", "EHH0019"]),
    ("TUPY", None, 2, ["EHL0041", "EHH0003"]),
    ("TUPY", "LIEBHERR", 1, ["EHL0041"]),
    ("TUPY", "HYUNDAI", 1, ["EHH0003"]),
    ("PÁTIO DE MANUTENÇÃO", None, 2, ["EHL0013", "EHL0014"]),
    ("PÁTIO DE MANUTENÇÃO", "LIEBHERR", 2, ["EHL0013", "EHL0014"]),
    ("MATHEUS", None, 1, ["EHH0007"]),
    ("MATHEUS", "HYUNDAI", 1, ["EHH0007"]),
    ("MULTI AÇO", None, 1, ["EHH0037"]),
    ("MULTI AÇO", "HYUNDAI", 1, ["EHH0037"]),
]


LINHAS_SELETIVA = [ln for ln in LINHAS_GASTO if ln[0] in LOCAIS_SELETIVA]
LINHAS_EXTERNO = [ln for ln in LINHAS_GASTO if ln[0] in LOCAIS_EXTERNO]

META_ABAS: dict[str, dict[str, str]] = {
    "Gastos com Manutenção": {
        "titulo": "Manutenção — recorte da aba «Gasto geral»",
        "descricao": (
            "Mesma hierarquia Local → Marca → Máquina da aba «Gasto geral» (mesmos locais e parque "
            "Liebherr/Hyundai), porém somando apenas as contas 7.1.1 (peças), 7.1.2 (manutenção) "
            "e 7.1.18 (fretes). Os valores aqui são parte do total do Gasto geral — não o substituem."
        ),
        "modo": "manutencao",
    },
    "Gastos com combustível": {
        "titulo": "Combustível — recorte da aba «Gasto geral»",
        "descricao": (
            "Mesma estrutura da «Gasto geral», restrita às contas 7.1.4 (diesel em posto) e "
            "7.1.22 (diesel interno). Em 2026 (até março), quando o SAGI não registra abastecimento, "
            "entram os custos da base consolidada (Custos-Maquinas). Também é subconjunto do Gasto geral."
        ),
        "modo": "combustivel",
    },
    "Gastos com Contratos": {
        "titulo": "Contratos — manutenção + combustível por operação",
        "descricao": (
            "Reúne as mesmas rubricas das abas de Manutenção e Combustível (soma das contas 7.1.1, "
            "7.1.2, 7.1.18, 7.1.4 e 7.1.22), separadas em duas visões: operações Seletiva (G3S) e "
            "contratos externos. Equivale ao Gasto geral filtrado por essas contas, agrupado por "
            "onde a máquina está alocada."
        ),
        "modo": "contratos",
    },
}


def extrair_id_maquina(valor) -> str | None:
    s = re.sub(r"\s+", "", str(valor).strip().upper())
    m = re.match(r"^(EHL\d+|EHH\d+)", s)
    return m.group(1) if m else None


def _valor_numerico(series: pd.Series) -> pd.Series:
    num = pd.to_numeric(series, errors="coerce")
    falt = num.isna() & series.notna()
    if falt.any():
        num.loc[falt] = series.loc[falt].map(parse_numero_br)
    return num


def carregar_base() -> pd.DataFrame:
    raw = pd.read_excel(BASE, sheet_name="base_maquinas_2025_2026")
    raw["valor_conta_num"] = _valor_numerico(raw["valor_conta"])
    raw["gasto_abs"] = raw["valor_conta_num"].abs()
    raw["data_nf"] = pd.to_datetime(raw["data_nf"], errors="coerce", dayfirst=True)
    raw["MARCA"] = raw["MARCA"].astype(str).str.strip().str.upper()
    raw["ano_nf"] = raw["data_nf"].dt.year
    raw["mes_nf"] = raw["data_nf"].dt.month
    raw["cod_conta"] = raw["cod_conta"].astype(str).str.strip()
    raw["maq_id"] = raw["n4_centro_custo"].map(extrair_id_maquina)
    return raw[
        raw["maq_id"].isin(ALL_MAQUINAS)
        & raw["MARCA"].isin(PARQUE.keys())
        & ~raw["cod_conta"].isin(CONTAS_EXCLUIR)
    ].copy()


def carregar_diesel_2026_q1_media(df: pd.DataFrame | None = None) -> dict[str, float]:
    """Médias jan–mar/2026 só para máquinas sem diesel já lançado na base."""
    if df is not None:
        ja_na_base = (
            df[(df["ano_nf"] == 2026) & (df["mes_nf"] <= 3) & df["cod_conta"].isin(CONTAS_COMBUSTIVEL)]
            .groupby("maq_id")["gasto_abs"]
            .sum()
        )
        maqs_com_diesel = {m for m, v in ja_na_base.items() if v > 0}
    else:
        maqs_com_diesel = set()

    cat = carregar_catalogo_maquinas()
    det, _, _ = carregar_media_consumo(cat)
    if det.empty:
        return {}
    q1 = det[
        (det["data_abastecimento"].dt.year == 2026)
        & (det["data_abastecimento"].dt.month <= 3)
        & det["placa"].isin(ALL_MAQUINAS)
        & ~det["placa"].isin(maqs_com_diesel)
    ]
    return q1.groupby("placa")["custo_abastecimento"].sum().to_dict()


def montar_lookup(
    df: pd.DataFrame,
    contas: frozenset[str],
    diesel_2026_q1: dict[str, float] | None = None,
    diesel_2026_modo: str = "ignore",
) -> dict[tuple[str, int], float]:
    sub = df[df["cod_conta"].isin(contas)]
    lookup: dict[tuple[str, int], float] = {}

    for maq, val in sub[sub["ano_nf"] == 2025].groupby("maq_id")["gasto_abs"].sum().items():
        lookup[(maq, 2025)] = float(val)

    sub26 = sub[(sub["ano_nf"] == 2026) & (sub["mes_nf"] <= 3)]
    for maq, val in sub26.groupby("maq_id")["gasto_abs"].sum().items():
        lookup[(maq, 2026)] = float(val)

    if not diesel_2026_q1:
        return lookup

    if diesel_2026_modo == "combustivel":
        for maq in ALL_MAQUINAS:
            sagi = lookup.get((maq, 2026), 0.0)
            media = float(diesel_2026_q1.get(maq, 0.0))
            total = sagi + media
            if total:
                lookup[(maq, 2026)] = total
            elif (maq, 2026) in lookup:
                del lookup[(maq, 2026)]
    elif diesel_2026_modo == "add":
        for maq, val in diesel_2026_q1.items():
            lookup[(maq, 2026)] = lookup.get((maq, 2026), 0.0) + float(val)

    return lookup


def soma_maquinas(maquinas: list[str], lookup: dict[tuple[str, int], float], ano: int) -> float:
    return sum(lookup.get((m, ano), 0.0) for m in maquinas)


def _copiar_estilo_celula(src, dst) -> None:
    if src.has_style:
        dst.font = copy(src.font)
        dst.fill = copy(src.fill)
        dst.border = copy(src.border)
        dst.alignment = copy(src.alignment)
        dst.number_format = src.number_format


def _escrever_titulo_aba(ws, titulo: str, descricao: str) -> int:
    """Título e descrição no topo; retorna a próxima linha livre."""
    ws.cell(1, 1, titulo).font = Font(bold=True, size=14, color="004B8D")
    ws.merge_cells("A1:I1")
    cell_desc = ws.cell(2, 1, descricao)
    cell_desc.font = Font(italic=True, size=10, color="333333")
    cell_desc.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A2:I2")
    ws.row_dimensions[2].height = 42
    return 3


def _ajustar_larguras(ws) -> None:
    for col, width in zip("ABCDEFGHI", [28, 12, 10, 14, 8, 14, 14, 8, 14]):
        ws.column_dimensions[col].width = width


def _limpar_aba(ws, max_row: int = 80, max_col: int = 12) -> None:
    for merged in list(ws.merged_cells.ranges):
        ws.unmerge_cells(str(merged))
    for r in range(1, max_row + 1):
        for c in range(1, max_col + 1):
            ws.cell(r, c).value = None


def _escrever_cabecalho_tabela(ws, row: int, template_ws) -> int:
    for col, val in ((4, 2025), (7, "2026 (até março)")):
        cell = ws.cell(row, col, val)
        _copiar_estilo_celula(template_ws.cell(1, col), cell)
        cell.font = Font(bold=True)

    hdr_row = row + 1
    headers = [
        "Local", "Marca", "Máquina", "Gasto total", "%", "Média mensal",
        "Gasto total", "%", "Média mensal",
    ]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(hdr_row, col, h)
        _copiar_estilo_celula(template_ws.cell(2, col), cell)
        cell.font = Font(bold=True)
    return hdr_row + 1


def _escrever_linhas_dados(
    ws,
    start_row: int,
    linhas: list[LinhaGasto],
    lookup: dict[tuple[str, int], float],
    template_ws,
) -> tuple[int, list[int], list[int]]:
    parent_por_local: dict[str, int] = {}
    rows_hyundai: list[int] = []
    rows_liebherr: list[int] = []
    r = start_row

    for local, marca, qtd, maquinas in linhas:
        g25 = soma_maquinas(maquinas, lookup, 2025)
        g26 = soma_maquinas(maquinas, lookup, 2026)

        ws.cell(r, 1, local)
        if marca:
            ws.cell(r, 2, marca)
        ws.cell(r, 3, qtd)
        ws.cell(r, 4, round(g25, 2))
        ws.cell(r, 7, round(g26, 2))
        ws.cell(r, 6, f"=D{r}/12")
        ws.cell(r, 9, f"=G{r}/3")

        tpl_row = 3 if marca is None else 4
        for col in range(1, 10):
            _copiar_estilo_celula(template_ws.cell(tpl_row, col), ws.cell(r, col))
        if marca is None:
            parent_por_local[local] = r
            for col in range(1, 10):
                ws.cell(r, col).font = Font(bold=True)
        else:
            parent_r = parent_por_local.get(local)
            if parent_r:
                ws.cell(r, 5, f"=D{r}/D{parent_r}")
                ws.cell(r, 8, f"=G{r}/G{parent_r}")
            ws.cell(r, 2).font = Font(bold=True)
            if marca == "HYUNDAI":
                rows_hyundai.append(r)
            elif marca == "LIEBHERR":
                rows_liebherr.append(r)

        r += 1

    return r, rows_hyundai, rows_liebherr


def _escrever_resumo_geral(
    ws,
    start_row: int,
    rows_hyundai: list[int],
    rows_liebherr: list[int],
    template_ws,
) -> int:
    r = start_row + 1
    ws.cell(r, 4, 2025).font = Font(bold=True)
    ws.cell(r, 7, "2026 (até março)").font = Font(bold=True)
    r += 1

    for col, h in enumerate(["", "Geral", "", "Gasto total", "%", "Média mensal", "Gasto total", "%", "Média mensal"], 1):
        if h:
            ws.cell(r, col, h).font = Font(bold=True)
    r += 1

    def _sum_formula(letter: str, rows: list[int]) -> str:
        if not rows:
            return "0"
        return "+".join(f"{letter}{rr}" for rr in rows)

    r_h, r_l, r_t = r, r + 1, r + 2

    ws.cell(r_h, 2, "HYUNDAI")
    ws.cell(r_h, 3, f"=SUM({_sum_formula('C', rows_hyundai)})" if rows_hyundai else 0)
    ws.cell(r_h, 4, f"={_sum_formula('D', rows_hyundai)}" if rows_hyundai else 0)
    ws.cell(r_h, 5, f"=D{r_h}/D{r_t}")
    ws.cell(r_h, 6, f"={_sum_formula('F', rows_hyundai)}" if rows_hyundai else 0)
    ws.cell(r_h, 7, f"={_sum_formula('G', rows_hyundai)}" if rows_hyundai else 0)
    ws.cell(r_h, 8, f"=G{r_h}/G{r_t}")
    ws.cell(r_h, 9, f"={_sum_formula('I', rows_hyundai)}" if rows_hyundai else 0)

    ws.cell(r_l, 2, "LIEBHERR")
    ws.cell(r_l, 3, f"=SUM({_sum_formula('C', rows_liebherr)})" if rows_liebherr else 0)
    ws.cell(r_l, 4, f"={_sum_formula('D', rows_liebherr)}" if rows_liebherr else 0)
    ws.cell(r_l, 5, f"=D{r_l}/D{r_t}")
    ws.cell(r_l, 6, f"={_sum_formula('F', rows_liebherr)}" if rows_liebherr else 0)
    ws.cell(r_l, 7, f"={_sum_formula('G', rows_liebherr)}" if rows_liebherr else 0)
    ws.cell(r_l, 8, f"=G{r_l}/G{r_t}")
    ws.cell(r_l, 9, f"={_sum_formula('I', rows_liebherr)}" if rows_liebherr else 0)

    ws.cell(r_t, 2, "Total").font = Font(bold=True)
    ws.cell(r_t, 3, f"=SUM(C{r_h}:C{r_l})")
    ws.cell(r_t, 4, f"=SUM(D{r_h}:D{r_l})")
    ws.cell(r_t, 7, f"=SUM(G{r_h}:G{r_l})")

    for rr in (r_h, r_l, r_t):
        for col in range(1, 10):
            _copiar_estilo_celula(template_ws.cell(33, col), ws.cell(rr, col))

    return r_t + 1


def _escrever_bloco(
    ws,
    start_row: int,
    subtitulo: str | None,
    linhas: list[LinhaGasto],
    lookup: dict[tuple[str, int], float],
    template_ws,
) -> int:
    row = start_row
    if subtitulo:
        ws.cell(row, 1, subtitulo).font = Font(bold=True, size=12, color="004B8D")
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=9)
        row += 1

    data_start = _escrever_cabecalho_tabela(ws, row, template_ws)
    _, rows_h, rows_l = _escrever_linhas_dados(ws, data_start, linhas, lookup, template_ws)
    return _escrever_resumo_geral(ws, data_start + len(linhas), rows_h, rows_l, template_ws)


def escrever_aba_unica(
    ws,
    titulo: str,
    descricao: str,
    linhas: list[LinhaGasto],
    lookup: dict[tuple[str, int], float],
    template_ws,
) -> None:
    _limpar_aba(ws)
    prox = _escrever_titulo_aba(ws, titulo, descricao)
    _escrever_bloco(ws, prox, None, linhas, lookup, template_ws)
    _ajustar_larguras(ws)


def escrever_aba_contratos(
    ws,
    titulo: str,
    descricao: str,
    lookup: dict[tuple[str, int], float],
    template_ws,
) -> None:
    _limpar_aba(ws, max_row=95)
    prox = _escrever_titulo_aba(ws, titulo, descricao)
    prox = _escrever_bloco(
        ws,
        prox + 1,
        "Seletiva (G3S) — Prudente, Maringá, Londrina, Dourados, Campo Grande, Pátio de Manutenção",
        LINHAS_SELETIVA,
        lookup,
        template_ws,
    )
    _escrever_bloco(
        ws,
        prox + 2,
        "Contratos externos — Arcelor Mittal Barra Mansa, Tupy, Matheus, Multi Aço",
        LINHAS_EXTERNO,
        lookup,
        template_ws,
    )
    _ajustar_larguras(ws)


def _sum_formula(letter: str, rows: list[int]) -> str:
    if not rows:
        return "0"
    return "+".join(f"{letter}{rr}" for rr in rows)


def _rows_marca_gasto_geral() -> tuple[list[int], list[int]]:
    rows_h: list[int] = []
    rows_l: list[int] = []
    for i, (_local, marca, _qtd, _maqs) in enumerate(LINHAS_GASTO):
        r = 3 + i
        if marca == "HYUNDAI":
            rows_h.append(r)
        elif marca == "LIEBHERR":
            rows_l.append(r)
    return rows_h, rows_l


def corrigir_formulas_resumo_gasto_geral(wb) -> None:
    """Corrige bloco Geral e Por Máquina: somas completas e média = Σ(gasto/mês) sem dividir de novo."""
    if "Gasto geral" not in wb.sheetnames:
        return
    ws = wb["Gasto geral"]
    rows_h, rows_l = _rows_marca_gasto_geral()

    r_geral = None
    for r in range(1, 55):
        if ws.cell(r, 2).value == "Geral":
            r_geral = r
            break
    if r_geral is None:
        return

    r_h, r_l, r_t = r_geral + 1, r_geral + 2, r_geral + 3
    sf = _sum_formula

    ws.cell(r_h, 3, f"=SUM({sf('C', rows_h)})" if rows_h else 0)
    ws.cell(r_h, 4, f"={sf('D', rows_h)}" if rows_h else 0)
    ws.cell(r_h, 5, f"=D{r_h}/D{r_t}")
    ws.cell(r_h, 6, f"={sf('F', rows_h)}" if rows_h else 0)
    ws.cell(r_h, 7, f"={sf('G', rows_h)}" if rows_h else 0)
    ws.cell(r_h, 8, f"=G{r_h}/G{r_t}")
    ws.cell(r_h, 9, f"={sf('I', rows_h)}" if rows_h else 0)

    ws.cell(r_l, 3, f"=SUM({sf('C', rows_l)})" if rows_l else 0)
    ws.cell(r_l, 4, f"={sf('D', rows_l)}" if rows_l else 0)
    ws.cell(r_l, 5, f"=D{r_l}/D{r_t}")
    ws.cell(r_l, 6, f"={sf('F', rows_l)}" if rows_l else 0)
    ws.cell(r_l, 7, f"={sf('G', rows_l)}" if rows_l else 0)
    ws.cell(r_l, 8, f"=G{r_l}/G{r_t}")
    ws.cell(r_l, 9, f"={sf('I', rows_l)}" if rows_l else 0)

    ws.cell(r_t, 3, f"=SUM(C{r_h}:C{r_l})")
    ws.cell(r_t, 4, f"=SUM(D{r_h}:D{r_l})")
    ws.cell(r_t, 7, f"=SUM(G{r_h}:G{r_l})")

    for r in range(r_t + 1, r_t + 12):
        if ws.cell(r, 2).value == "HYUNDAI" and ws.cell(r, 3).value == 16:
            ws.cell(r, 4, f"=D{r_h}/C{r}")
            ws.cell(r, 6, f"=F{r_h}/C{r}")
            ws.cell(r, 7, f"=G{r_h}/C{r}")
            ws.cell(r, 9, f"=I{r_h}/C{r}")
        if ws.cell(r, 2).value == "LIEBHERR" and ws.cell(r, 3).value == 7:
            ws.cell(r, 4, f"=D{r_l}/C{r}")
            ws.cell(r, 6, f"=F{r_l}/C{r}")
            ws.cell(r, 7, f"=G{r_l}/C{r}")
            ws.cell(r, 9, f"=I{r_l}/C{r}")


def corrigir_formulas_media_gasto_geral(wb) -> None:
    """Coluna 2026: média mensal = gasto total ÷ 3 (não ÷ 12)."""
    if "Gasto geral" not in wb.sheetnames:
        return
    ws = wb["Gasto geral"]
    for r in range(3, 40):
        f9 = ws.cell(r, 9).value
        if isinstance(f9, str) and f9 == f"=G{r}/12":
            ws.cell(r, 9, f"=G{r}/3")


def atualizar_gasto_geral(wb, lookup: dict[tuple[str, int], float]) -> None:
    """Atualiza só gasto total 2025/2026 (cols D e G); preserva layout e fórmulas de % / média."""
    if "Gasto geral" not in wb.sheetnames:
        return
    ws = wb["Gasto geral"]
    corrigir_formulas_media_gasto_geral(wb)
    corrigir_formulas_resumo_gasto_geral(wb)
    for i, (_local, _marca, _qtd, maquinas) in enumerate(LINHAS_GASTO):
        r = 3 + i
        ws.cell(r, 4, round(soma_maquinas(maquinas, lookup, 2025), 2))
        ws.cell(r, 7, round(soma_maquinas(maquinas, lookup, 2026), 2))


def atualizar_dashboard(dest: Path | None = None) -> Path:
    dest = dest or OUT
    if not dest.exists():
        raise FileNotFoundError(dest)

    df = carregar_base()
    diesel_q1 = carregar_diesel_2026_q1_media(df)

    lookups = {
        "manutencao": montar_lookup(df, CONTAS_MANUTENCAO),
        "combustivel": montar_lookup(
            df, CONTAS_COMBUSTIVEL, diesel_2026_q1=diesel_q1, diesel_2026_modo="combustivel"
        ),
        "contratos": montar_lookup(
            df, CONTAS_GERAL, diesel_2026_q1=diesel_q1, diesel_2026_modo="add"
        ),
    }

    wb = load_workbook(dest)
    template = wb["Gasto geral"]
    atualizar_gasto_geral(wb, lookups["contratos"])

    for sheet_name, meta in META_ABAS.items():
        if sheet_name not in wb.sheetnames:
            raise KeyError(f"Aba ausente: {sheet_name}")
        modo = meta["modo"]
        if modo == "contratos":
            escrever_aba_contratos(
                wb[sheet_name],
                meta["titulo"],
                meta["descricao"],
                lookups[modo],
                template,
            )
        else:
            escrever_aba_unica(
                wb[sheet_name],
                meta["titulo"],
                meta["descricao"],
                LINHAS_GASTO,
                lookups[modo],
                template,
            )

    wb.save(dest)
    return dest


if __name__ == "__main__":
    path = atualizar_dashboard()
    print(f"Abas filtradas atualizadas: {path.resolve()}")
