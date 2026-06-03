"""Gera o relatório de fechamento de folha (formato FOPA) a partir do dump
ODBC de abril/2026.

O arquivo final tem o mesmo layout do `02-Referencias/FOPA/03_2026_Mar_Rel_FOPA.xlsx`:
uma aba `GERAL` consolidando todos os credores/funcionários do mês mais uma
aba por tomador (PILARES, BRACOFER, EKIPA, TRANSMOVE, SELETIVA APOIO,
SELETIVA C GRANDE, SELETIVA DOURADOS, SELETIVA PRUDENTE, SELETIVA MARINGÁ,
SELETIVA CIDADE ALTA, SELETIVA LONDRINA).

Como o ODBC traz somente o lado de caixa (lançamentos pagos / a pagar do mês),
as colunas de "Provisão de Férias + 13°" e "Provisão de Encargos" ficam em
branco; elas só conseguem ser preenchidas quando a folha de abril for
processada pelo FOPA. Os demais campos seguem a mesma lógica do mês de março:

* `Eventos Folha (Caixa)` = soma de `valor_bruto` cujo `descdc` é
  `SALÁRIOS`, `BOLSA ESTAGIO` ou `PRO LABORE`.
* `Sal PF` = soma de `valor_bruto` cujo `descdc` é `CONSULTORIA` ou
  `SERVIÇOS CONTRATADOS` (mesmo agrupamento usado no FOPA para PJ/PF).
* `TT BRUTO ABRIL` = `Eventos Folha (Caixa) + Sal PF`.
* `TT BRUTO MARÇO` é trazido da aba GERAL do FOPA de março para comparação.
* Tipo / Setor / Função / Empresa Registro / CNPJ vêm da aba `BASE+TOMADOR`
  do FOPA de março (último cadastro disponível para o credor).

Uso:
    python scripts/fechamento_fopa_abril.py \
        --abril 02-Referencias/dados_fechamento_abril.xlsx \
        --marco 02-Referencias/FOPA/03_2026_Mar_Rel_FOPA.xlsx \
        --saida 02-Referencias/FOPA/04_2026_Abr_Rel_FOPA.xlsx
"""

from __future__ import annotations

import argparse
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.worksheet import Worksheet


# ─── Configuração ────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ABRIL = ROOT / "02-Referencias" / "dados_fechamento_abril.xlsx"
DEFAULT_MARCO = ROOT / "02-Referencias" / "03_2026_Mar_Rel_FOPA.xlsx"
DEFAULT_SAIDA = ROOT / "02-Referencias" / "04_2026_Abr_Rel_FOPA.xlsx"

MES_REF_LABEL = "ABRIL/2026"
MES_REF_COL = "TT BRUTO\nABRIL"
MES_ANT_COL = "TT BRUTO\nMARÇO"

# Tipos que entram em "Eventos Folha (Caixa)" (folha de pagamento)
DESCDC_FOLHA = {"SALÁRIOS", "BOLSA ESTAGIO", "PRO LABORE"}
# Tipos que entram em "Sal PF" (PJ / serviços de pessoa-equivalente)
DESCDC_PF = {"CONSULTORIA", "SERVIÇOS CONTRATADOS"}


# ─── Mapa descen → tomador ───────────────────────────────────────────────────


@dataclass(frozen=True)
class Regra:
    """Regra de classificação de descen em um tomador.

    Cada regra avalia o `descen` (já normalizado em maiúsculas e sem acentos)
    e devolve True se o lançamento pertence ao tomador-alvo.
    """

    tomador: str
    contains_all: tuple[str, ...] = ()
    contains_any: tuple[str, ...] = ()
    not_contains: tuple[str, ...] = ()


# Ordem importa: a primeira regra que casar vence.
REGRAS_TOMADOR: tuple[Regra, ...] = (
    Regra("PILARES", contains_any=("/ PILARES /", "PILARES /")),
    Regra("BRACOFER", contains_any=("/ BRACOFER /", "BRACOFER /")),
    Regra("TRANSMOVE", contains_any=("TRANSMOVE",)),
    Regra(
        "SELETIVA CIDADE ALTA",
        contains_any=("MARINGA CIDADE ALTA",),
    ),
    Regra(
        "SELETIVA MARINGÁ",
        contains_any=("/ MARINGA /",),
        not_contains=("CIDADE ALTA",),
    ),
    Regra("SELETIVA DOURADOS", contains_any=("/ DOURADOS /",)),
    Regra("SELETIVA LONDRINA", contains_any=("/ LONDRINA /",)),
    Regra("SELETIVA C GRANDE", contains_any=("/ CAMPO GRANDE /",)),
    Regra(
        "SELETIVA APOIO",
        contains_any=("CORPORATIVO SUCATA", "/ CORPORATIVO /"),
    ),
    Regra(
        "SELETIVA PRUDENTE",
        contains_any=("/ PRESIDENTE PRUDENTE /",),
        not_contains=("EKIPA", "BRACOFER", "TRANSMOVE"),
    ),
    Regra("EKIPA", contains_any=("/ EKIPA ", "EKIPA LOCACOES")),
)

# Tomadores que devem aparecer mesmo sem dados (preserva a ordem do FOPA)
TOMADORES_FIXOS: tuple[str, ...] = (
    "PILARES",
    "BRACOFER",
    "EKIPA",
    "TRANSMOVE",
    "SELETIVA APOIO",
    "SELETIVA C GRANDE",
    "SELETIVA DOURADOS",
    "SELETIVA PRUDENTE",
    "SELETIVA MARINGÁ",
    "SELETIVA CIDADE ALTA",
    "SELETIVA LONDRINA",
)


# Tomador da aba `BASE+TOMADOR` de março → label do tomador no relatório
MAPA_TOMADOR_FOPA = {
    "PILARES": "PILARES",
    "BRACOFER": "BRACOFER",
    "EKIPA LOCACOES E SERV G&S": "EKIPA",
    "TRANSMOVE GSL": "TRANSMOVE",
    "SELETIVA CORPORATIVO SUCATA": "SELETIVA APOIO",
    "SELETIVA C GRANDE": "SELETIVA C GRANDE",
    "SELETIVA DOURADOS": "SELETIVA DOURADOS",
    "SELETIVA PRESIDENTE PRUDENTE": "SELETIVA PRUDENTE",
    "SELETIVA MARINGA": "SELETIVA MARINGÁ",
    "SELETIVA MARINGA DISTRITO": "SELETIVA MARINGÁ",
    "SELETIVA MARINGA CIDADE ALTA": "SELETIVA CIDADE ALTA",
    "SELETIVA LONDRINA": "SELETIVA LONDRINA",
    "RENDER LOCACOES": None,
}


# ─── Estilos ─────────────────────────────────────────────────────────────────

FONT_TITULO = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
FONT_HEADER = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
FONT_BODY = Font(name="Calibri", size=10)
FONT_TOTAL = Font(name="Calibri", size=10, bold=True)

FILL_TITULO = PatternFill("solid", fgColor="305496")
FILL_HEADER = PatternFill("solid", fgColor="305496")
FILL_TOTAL = PatternFill("solid", fgColor="D9E1F2")
FILL_RESUMO = PatternFill("solid", fgColor="EDF2F9")

ALIGN_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
ALIGN_LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center", wrap_text=False)

THIN = Side(border_style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

FMT_BRL = 'R$ #,##0.00;[Red]-R$ #,##0.00;""'
FMT_PCT = "0.00%"

HEADERS = [
    "Qtde",
    "FUNCIONÁRIO",
    "Tipo",
    "Setor",
    "Função ",
    "Status",
    "Empresa Registro",
    "CNPJ",
    "Provisão\nde Férias + 13°",
    "Provisão \nde Encargos",
    "Eventos Folha\n(Caixa)",
    "Sal PF",
    MES_REF_COL,
    "%",
    MES_ANT_COL,
]

NUM_COLS_IDX = (8, 9, 10, 11, 12, 14)  # 0-based índices das colunas numéricas
PCT_COL_IDX = 13


# ─── Utilitários ─────────────────────────────────────────────────────────────


def _normalizar(s: str) -> str:
    """Remove acentos, força maiúsculas e colapsa múltiplos espaços."""
    if s is None:
        return ""
    txt = unicodedata.normalize("NFKD", str(s))
    txt = "".join(ch for ch in txt if not unicodedata.combining(ch))
    txt = txt.upper().strip()
    txt = re.sub(r"\s+", " ", txt)
    return txt


def classificar_tomador(descen: str) -> str | None:
    """Aplica as regras configuradas e devolve o tomador (ou None)."""
    norm = _normalizar(descen)
    norm_padded = f" {norm} "
    for regra in REGRAS_TOMADOR:
        if any(t in norm_padded for t in regra.not_contains):
            continue
        if regra.contains_all and not all(t in norm_padded for t in regra.contains_all):
            continue
        if regra.contains_any and not any(t in norm_padded for t in regra.contains_any):
            continue
        return regra.tomador
    return None


# ─── Pipeline principal ──────────────────────────────────────────────────────


def carregar_abril(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=0, dtype={"codcen": str, "codcdc": str})
    df.columns = [c.strip() for c in df.columns]
    df["descdc"] = df["descdc"].astype(str).str.strip().str.upper()
    df["descen"] = df["descen"].astype(str).str.strip()
    df["nome"] = df["nome"].astype(str).str.strip()
    df["valor_bruto"] = pd.to_numeric(df["valor_bruto"], errors="coerce").fillna(0.0)
    return df


def carregar_base_tomador(path: Path) -> pd.DataFrame:
    base = pd.read_excel(path, sheet_name="BASE+TOMADOR")
    base.columns = [c.strip() for c in base.columns]
    cols_alvo = {
        "FUNCIONÁRIO": "nome",
        "MODALIDADE": "tipo",
        "SETOR": "setor",
        "FUNÇÃO": "funcao",
        "EMPRESA": "empresa",
        "CNPJ": "cnpj",
        "TOMADOR": "tomador_fopa",
    }
    faltando = [c for c in cols_alvo if c not in base.columns]
    if faltando:
        raise ValueError(f"Colunas faltando em BASE+TOMADOR: {faltando}")
    base = base[list(cols_alvo)].rename(columns=cols_alvo)
    base["nome_norm"] = base["nome"].map(_normalizar)
    base["tomador"] = base["tomador_fopa"].map(MAPA_TOMADOR_FOPA)
    return base


def carregar_geral_marco(path: Path) -> pd.DataFrame:
    """Lê a aba GERAL do FOPA de março como referência de TT BRUTO anterior."""
    raw = pd.read_excel(path, sheet_name="GERAL", header=1)
    raw.columns = [str(c).strip() for c in raw.columns]
    nome_col = next((c for c in raw.columns if c.upper().startswith("FUNCION")), None)
    bruto_col = next((c for c in raw.columns if c.upper().startswith("TT BRUTO\nMAR")), None)
    if nome_col is None or bruto_col is None:
        bruto_col = next(
            (c for c in raw.columns if "TT BRUTO" in c.upper() and "MAR" in c.upper()),
            None,
        )
    if nome_col is None or bruto_col is None:
        raise ValueError(
            "Não encontrei colunas FUNCIONÁRIO / TT BRUTO MARÇO na aba GERAL. "
            f"Colunas disponíveis: {raw.columns.tolist()}"
        )
    out = raw[[nome_col, bruto_col]].copy()
    out.columns = ["nome", "tt_bruto_marco"]
    out = out.dropna(subset=["nome"])
    out["nome_norm"] = out["nome"].map(_normalizar)
    out["tt_bruto_marco"] = pd.to_numeric(out["tt_bruto_marco"], errors="coerce")
    out = (
        out.groupby("nome_norm", as_index=False)
        .agg(nome=("nome", "first"), tt_bruto_marco=("tt_bruto_marco", "sum"))
    )
    return out


def aplicar_classificacao(abril: pd.DataFrame) -> pd.DataFrame:
    df = abril.copy()
    df = df[~df["codcen"].astype(str).str.startswith("2")]
    df["tomador"] = df["descen"].map(classificar_tomador)
    df = df[df["tomador"].notna()].copy()
    df["bucket"] = df["descdc"].map(
        lambda d: "eventos_folha"
        if d in DESCDC_FOLHA
        else ("sal_pf" if d in DESCDC_PF else "outros")
    )
    df = df[df["bucket"] != "outros"].copy()
    return df


def consolidar(
    abril: pd.DataFrame,
    base: pd.DataFrame,
    marco: pd.DataFrame,
) -> pd.DataFrame:
    abril["nome_norm"] = abril["nome"].map(_normalizar)
    pivot = (
        abril.pivot_table(
            index=["tomador", "nome_norm"],
            columns="bucket",
            values="valor_bruto",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reset_index()
    )
    for col in ("eventos_folha", "sal_pf"):
        if col not in pivot.columns:
            pivot[col] = 0.0
    pivot["tt_bruto_abr"] = pivot["eventos_folha"] + pivot["sal_pf"]

    nomes_orig = (
        abril.groupby("nome_norm", as_index=False)["nome"].agg(lambda s: s.mode().iat[0])
    )
    pivot = pivot.merge(nomes_orig, on="nome_norm", how="left")

    base_unique = base.drop_duplicates(subset="nome_norm", keep="last")[
        ["nome_norm", "tipo", "setor", "funcao", "empresa", "cnpj"]
    ]
    pivot = pivot.merge(base_unique, on="nome_norm", how="left")

    pivot = pivot.merge(
        marco[["nome_norm", "tt_bruto_marco"]],
        on="nome_norm",
        how="left",
    )
    pivot["tt_bruto_marco"] = pivot["tt_bruto_marco"].fillna(0.0)
    pivot["status"] = "Ativo"
    pivot["provisao_ferias"] = 0.0
    pivot["provisao_encargos"] = 0.0
    return pivot


# ─── Escrita do Excel ────────────────────────────────────────────────────────


# Nome da Tabela do Excel que serve como fonte das fórmulas dinâmicas das abas
# de tomador. Mantenha em ASCII para evitar problemas em fórmulas estruturadas.
NOME_TABELA = "tbl_dados"

# Cabeçalhos da tabela de detalhe gravada na aba GERAL.
# Estes valores DEVEM bater com as referências usadas nas fórmulas das abas
# por tomador (`tbl_dados[<header>]`).
HEADERS_GERAL = [
    "Tomador",
    "FUNCIONÁRIO",
    "Tipo",
    "Setor",
    "Função",
    "Status",
    "Empresa Registro",
    "CNPJ",
    "Provisão de Férias + 13°",
    "Provisão de Encargos",
    "Eventos Folha (Caixa)",
    "Sal PF",
    "TT BRUTO ABRIL",
    "TT BRUTO MARÇO",
]

# Mapa coluna lógica → nome do header na tabela (para uso em fórmulas)
COL_TOMADOR = "Tomador"
COL_FUNCIONARIO = "FUNCIONÁRIO"
COL_TIPO = "Tipo"
COL_EMPRESA = "Empresa Registro"
COL_CNPJ = "CNPJ"
COL_PROV_FERIAS = "Provisão de Férias + 13°"
COL_PROV_ENCARGOS = "Provisão de Encargos"
COL_EVENTOS = "Eventos Folha (Caixa)"
COL_SALPF = "Sal PF"
COL_TT_ABR = "TT BRUTO ABRIL"
COL_TT_MAR = "TT BRUTO MARÇO"


def _aplicar_largura(ws: Worksheet, larguras: list[int]) -> None:
    for idx, larg in enumerate(larguras, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = larg


def _t(col: str) -> str:
    """Atalho para gerar a referência estruturada `tbl_dados[<col>]`."""
    return f"{NOME_TABELA}[{col}]"


def _escrever_titulo(ws: Worksheet, tomador: str, totais: dict[str, float]) -> None:
    ws.cell(row=1, column=1, value=tomador)
    ws.cell(row=1, column=2, value=f"FOLHA DE PAGAMENTO {MES_REF_LABEL}")
    ws.cell(row=1, column=9, value=totais.get("provisao_ferias", 0.0))
    ws.cell(row=1, column=10, value=totais.get("provisao_encargos", 0.0))
    ws.cell(row=1, column=11, value="Soma")
    ws.cell(row=1, column=13, value=totais.get("tt_bruto_abr", 0.0))
    ws.cell(row=1, column=15, value=totais.get("tt_bruto_marco", 0.0))
    for col in (1, 2, 11):
        cel = ws.cell(row=1, column=col)
        cel.font = FONT_TITULO
        cel.fill = FILL_TITULO
        cel.alignment = ALIGN_CENTER
    for col in (9, 10, 13, 15):
        cel = ws.cell(row=1, column=col)
        cel.font = FONT_TOTAL
        cel.fill = FILL_TOTAL
        cel.alignment = ALIGN_RIGHT
        cel.number_format = FMT_BRL
    ws.row_dimensions[1].height = 28


def _escrever_header(ws: Worksheet, row: int) -> None:
    for idx, h in enumerate(HEADERS, start=1):
        cel = ws.cell(row=row, column=idx, value=h)
        cel.font = FONT_HEADER
        cel.fill = FILL_HEADER
        cel.alignment = ALIGN_CENTER
        cel.border = BORDER
    ws.row_dimensions[row].height = 36


def _escrever_linhas(
    ws: Worksheet,
    df: pd.DataFrame,
    inicio_row: int,
    total_tomador: float,
) -> int:
    df = df.sort_values("tt_bruto_abr", ascending=False).reset_index(drop=True)
    for i, lin in df.iterrows():
        r = inicio_row + i
        valores = [
            i + 1,
            lin["nome"],
            lin.get("tipo") or "",
            lin.get("setor") or "",
            lin.get("funcao") or "",
            lin.get("status") or "Ativo",
            lin.get("empresa") or "",
            lin.get("cnpj") or "",
            lin.get("provisao_ferias", 0.0) or 0.0,
            lin.get("provisao_encargos", 0.0) or 0.0,
            float(lin.get("eventos_folha") or 0.0),
            float(lin.get("sal_pf") or 0.0),
            float(lin.get("tt_bruto_abr") or 0.0),
            (float(lin["tt_bruto_abr"]) / total_tomador) if total_tomador else 0.0,
            float(lin.get("tt_bruto_marco") or 0.0),
        ]
        for j, v in enumerate(valores, start=1):
            cel = ws.cell(row=r, column=j, value=v)
            cel.font = FONT_BODY
            cel.border = BORDER
            if j == 1:
                cel.alignment = ALIGN_CENTER
            elif j in NUM_COLS_IDX or j == 13 or j == PCT_COL_IDX + 1:
                cel.alignment = ALIGN_RIGHT
            else:
                cel.alignment = ALIGN_LEFT
            if j in NUM_COLS_IDX or j == 13:
                cel.number_format = FMT_BRL
            elif j == PCT_COL_IDX + 1:
                cel.number_format = FMT_PCT
    return inicio_row + len(df)


def _resumo_modalidade(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["MODALIDADE", "FUNCIONÁRIOS", "TT BRUTO"])
    g = (
        df.groupby(df["tipo"].fillna("(sem cadastro)"), dropna=False)
        .agg(FUNCIONARIOS=("nome", "count"), TT_BRUTO=("tt_bruto_abr", "sum"))
        .reset_index()
        .rename(columns={"tipo": "MODALIDADE", "FUNCIONARIOS": "FUNCIONÁRIOS", "TT_BRUTO": "TT BRUTO"})
    )
    return g.sort_values("TT BRUTO", ascending=False)


def _resumo_empresa(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["EMPRESA", "CNPJ", "FUNCIONÁRIOS", "TT BRUTO"])
    g = (
        df.assign(
            empresa=df["empresa"].fillna("(sem cadastro)"),
            cnpj=df["cnpj"].fillna(""),
        )
        .groupby(["empresa", "cnpj"], dropna=False)
        .agg(FUNCIONARIOS=("nome", "count"), TT_BRUTO=("tt_bruto_abr", "sum"))
        .reset_index()
        .rename(
            columns={
                "empresa": "EMPRESA",
                "cnpj": "CNPJ",
                "FUNCIONARIOS": "FUNCIONÁRIOS",
                "TT_BRUTO": "TT BRUTO",
            }
        )
    )
    return g.sort_values("TT BRUTO", ascending=False)


def _escrever_resumo(ws: Worksheet, inicio_row: int, df_dados: pd.DataFrame) -> int:
    r = inicio_row + 2
    cabecalho = ("MODALIDADE", "FUNCIONÁRIOS", "TT BRUTO")
    for j, h in enumerate(cabecalho, start=2):
        cel = ws.cell(row=r, column=j, value=h)
        cel.font = FONT_HEADER
        cel.fill = FILL_HEADER
        cel.alignment = ALIGN_CENTER
        cel.border = BORDER
    r += 1
    resumo = _resumo_modalidade(df_dados)
    for _, lin in resumo.iterrows():
        cels = [lin["MODALIDADE"], int(lin["FUNCIONÁRIOS"]), float(lin["TT BRUTO"])]
        for j, v in enumerate(cels, start=2):
            cel = ws.cell(row=r, column=j, value=v)
            cel.font = FONT_BODY
            cel.fill = FILL_RESUMO
            cel.border = BORDER
            if j == 4:
                cel.number_format = FMT_BRL
                cel.alignment = ALIGN_RIGHT
            elif j == 3:
                cel.alignment = ALIGN_CENTER
            else:
                cel.alignment = ALIGN_LEFT
        r += 1
    if not resumo.empty:
        cels = ["TOTAL", int(resumo["FUNCIONÁRIOS"].sum()), float(resumo["TT BRUTO"].sum())]
        for j, v in enumerate(cels, start=2):
            cel = ws.cell(row=r, column=j, value=v)
            cel.font = FONT_TOTAL
            cel.fill = FILL_TOTAL
            cel.border = BORDER
            if j == 4:
                cel.number_format = FMT_BRL
                cel.alignment = ALIGN_RIGHT
            elif j == 3:
                cel.alignment = ALIGN_CENTER
            else:
                cel.alignment = ALIGN_LEFT
        r += 1

    r += 1
    cabecalho_emp = ("EMPRESA", "CNPJ", "FUNCIONÁRIOS", "TT BRUTO")
    for j, h in enumerate(cabecalho_emp, start=2):
        cel = ws.cell(row=r, column=j, value=h)
        cel.font = FONT_HEADER
        cel.fill = FILL_HEADER
        cel.alignment = ALIGN_CENTER
        cel.border = BORDER
    r += 1
    resumo_emp = _resumo_empresa(df_dados)
    for _, lin in resumo_emp.iterrows():
        cels = [
            lin["EMPRESA"],
            lin["CNPJ"],
            int(lin["FUNCIONÁRIOS"]),
            float(lin["TT BRUTO"]),
        ]
        for j, v in enumerate(cels, start=2):
            cel = ws.cell(row=r, column=j, value=v)
            cel.font = FONT_BODY
            cel.fill = FILL_RESUMO
            cel.border = BORDER
            if j == 5:
                cel.number_format = FMT_BRL
                cel.alignment = ALIGN_RIGHT
            elif j == 4:
                cel.alignment = ALIGN_CENTER
            else:
                cel.alignment = ALIGN_LEFT
        r += 1
    if not resumo_emp.empty:
        cels = ["TOTAL", "", int(resumo_emp["FUNCIONÁRIOS"].sum()), float(resumo_emp["TT BRUTO"].sum())]
        for j, v in enumerate(cels, start=2):
            cel = ws.cell(row=r, column=j, value=v)
            cel.font = FONT_TOTAL
            cel.fill = FILL_TOTAL
            cel.border = BORDER
            if j == 5:
                cel.number_format = FMT_BRL
                cel.alignment = ALIGN_RIGHT
            elif j == 4:
                cel.alignment = ALIGN_CENTER
            else:
                cel.alignment = ALIGN_LEFT
        r += 1
    return r


def _escrever_aba_estatica(ws: Worksheet, tomador: str, df: pd.DataFrame) -> None:
    """Modo legado: grava os dados como valores fixos (sem fórmulas)."""
    _aplicar_largura(ws, [6, 38, 10, 22, 30, 12, 30, 22, 14, 14, 14, 14, 16, 8, 16])
    totais = {
        "provisao_ferias": float(df["provisao_ferias"].sum()),
        "provisao_encargos": float(df["provisao_encargos"].sum()),
        "tt_bruto_abr": float(df["tt_bruto_abr"].sum()),
        "tt_bruto_marco": float(df["tt_bruto_marco"].sum()),
    }
    _escrever_titulo(ws, tomador, totais)
    _escrever_header(ws, 2)
    proxima_row = _escrever_linhas(ws, df, 3, totais["tt_bruto_abr"]) if not df.empty else 3
    _escrever_resumo(ws, proxima_row, df)
    ws.freeze_panes = "B3"


# ─── Modo dinâmico (Tabela do Excel + FILTER/SORT/SUMIFS) ────────────────────


def _escrever_geral_dinamica(ws: Worksheet, consolidado: pd.DataFrame) -> None:
    """Grava na aba GERAL a tabela de detalhe (uma linha por tomador-credor).

    A tabela é registrada como Excel Table (`tbl_dados`) e serve como fonte
    única para as abas por tomador.
    """
    _aplicar_largura(
        ws,
        [22, 36, 10, 22, 30, 12, 30, 22, 14, 14, 14, 14, 16, 16],
    )

    # Linha 1 — Título + totais grandes
    ws.cell(row=1, column=1, value="GERAL")
    ws.cell(row=1, column=2, value=f"FOLHA DE PAGAMENTO {MES_REF_LABEL}")
    ws.cell(row=1, column=9, value=f"=SUBTOTAL(9,{_t(COL_PROV_FERIAS)})")
    ws.cell(row=1, column=10, value=f"=SUBTOTAL(9,{_t(COL_PROV_ENCARGOS)})")
    ws.cell(row=1, column=11, value="Soma")
    ws.cell(row=1, column=13, value=f"=SUBTOTAL(9,{_t(COL_TT_ABR)})")
    ws.cell(row=1, column=14, value=f"=SUBTOTAL(9,{_t(COL_TT_MAR)})")
    for col in (1, 2, 11):
        cel = ws.cell(row=1, column=col)
        cel.font = FONT_TITULO
        cel.fill = FILL_TITULO
        cel.alignment = ALIGN_CENTER
    for col in (9, 10, 13, 14):
        cel = ws.cell(row=1, column=col)
        cel.font = FONT_TOTAL
        cel.fill = FILL_TOTAL
        cel.alignment = ALIGN_RIGHT
        cel.number_format = FMT_BRL
    ws.row_dimensions[1].height = 28

    # Linha 2 — cabeçalho da tabela
    for j, h in enumerate(HEADERS_GERAL, start=1):
        cel = ws.cell(row=2, column=j, value=h)
        cel.font = FONT_HEADER
        cel.fill = FILL_HEADER
        cel.alignment = ALIGN_CENTER
        cel.border = BORDER
    ws.row_dimensions[2].height = 36

    # Linhas 3+ — dados de detalhe (uma linha por tomador × credor)
    df = consolidado.copy()
    df = df.assign(
        tipo=df["tipo"].fillna("(sem cadastro)"),
        setor=df["setor"].fillna(""),
        funcao=df["funcao"].fillna(""),
        empresa=df["empresa"].fillna("(sem cadastro)"),
        cnpj=df["cnpj"].fillna(""),
        status=df["status"].fillna("Ativo"),
    )
    # Ordena agrupando por tomador (na mesma ordem das abas) e dentro de cada
    # tomador por TT BRUTO ABRIL decrescente.
    ordem_tomador = {t: i for i, t in enumerate(TOMADORES_FIXOS)}
    df["_ord_tomador"] = df["tomador"].map(lambda t: ordem_tomador.get(t, 99))
    df = df.sort_values(
        ["_ord_tomador", "tt_bruto_abr"], ascending=[True, False]
    ).reset_index(drop=True)

    for i, lin in df.iterrows():
        r = 3 + i
        valores = [
            lin["tomador"],
            lin["nome"],
            lin["tipo"],
            lin["setor"],
            lin["funcao"],
            lin["status"],
            lin["empresa"],
            lin["cnpj"],
            float(lin["provisao_ferias"] or 0.0),
            float(lin["provisao_encargos"] or 0.0),
            float(lin["eventos_folha"] or 0.0),
            float(lin["sal_pf"] or 0.0),
            float(lin["tt_bruto_abr"] or 0.0),
            float(lin["tt_bruto_marco"] or 0.0),
        ]
        for j, v in enumerate(valores, start=1):
            cel = ws.cell(row=r, column=j, value=v)
            cel.font = FONT_BODY
            cel.border = BORDER
            if j in (1, 3, 6):
                cel.alignment = ALIGN_CENTER
            elif j in (9, 10, 11, 12, 13, 14):
                cel.alignment = ALIGN_RIGHT
                cel.number_format = FMT_BRL
            else:
                cel.alignment = ALIGN_LEFT

    # Registra como Excel Table
    if len(df) > 0:
        last_row = 2 + len(df)
        last_col_letter = get_column_letter(len(HEADERS_GERAL))
        table_ref = f"A2:{last_col_letter}{last_row}"
        tabela = Table(displayName=NOME_TABELA, ref=table_ref)
        tabela.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )
        ws.add_table(tabela)

    ws.freeze_panes = "C3"
    ws.sheet_view.showGridLines = False


def _formatar_buffer(ws: Worksheet, coluna_letra: str, num_format: str,
                     align: Alignment, linhas: range) -> None:
    """Pré-formata um intervalo de células de uma coluna para que valores
    derramados (spill) por fórmulas dinâmicas sejam exibidos no formato
    correto."""
    for r in linhas:
        cel = ws[f"{coluna_letra}{r}"]
        cel.number_format = num_format
        cel.alignment = align
        cel.font = FONT_BODY


def _escrever_tomador_dinamico(
    ws: Worksheet, tomador: str, buffer_linhas: int = 80
) -> None:
    """Cria uma aba de tomador como tabela dinâmica baseada em `tbl_dados`."""
    _aplicar_largura(
        ws,
        [6, 36, 10, 22, 30, 12, 30, 22, 14, 14, 14, 14, 16, 8, 16],
    )

    # ─── Linha 1: título + totais (via SUMIFS sobre a tabela GERAL) ──────────
    ws["A1"] = tomador  # serve também de critério de filtro para as fórmulas
    ws["B1"] = f"FOLHA DE PAGAMENTO {MES_REF_LABEL}"
    ws["I1"] = f"=SUMIFS({_t(COL_PROV_FERIAS)},{_t(COL_TOMADOR)},$A$1)"
    ws["J1"] = f"=SUMIFS({_t(COL_PROV_ENCARGOS)},{_t(COL_TOMADOR)},$A$1)"
    ws["K1"] = "Soma"
    ws["M1"] = f"=SUMIFS({_t(COL_TT_ABR)},{_t(COL_TOMADOR)},$A$1)"
    ws["O1"] = f"=SUMIFS({_t(COL_TT_MAR)},{_t(COL_TOMADOR)},$A$1)"

    for col in (1, 2, 11):
        cel = ws.cell(row=1, column=col)
        cel.font = FONT_TITULO
        cel.fill = FILL_TITULO
        cel.alignment = ALIGN_CENTER
    for col in (9, 10, 13, 15):
        cel = ws.cell(row=1, column=col)
        cel.font = FONT_TOTAL
        cel.fill = FILL_TOTAL
        cel.alignment = ALIGN_RIGHT
        cel.number_format = FMT_BRL
    ws.row_dimensions[1].height = 28

    # ─── Linha 2: cabeçalho ─────────────────────────────────────────────────
    _escrever_header(ws, 2)

    # ─── Linhas 3+: corpo dinâmico ──────────────────────────────────────────
    #
    #  • A3 → Qtde: SEQUENCE alinhado ao spill de B3.
    #  • B3 → 12 colunas (FUNCIONÁRIO … TT BRUTO ABRIL), ordenadas por TT BRUTO
    #         ABRIL desc. via SORT(FILTER(...)).
    #  • N3 → % do TT BRUTO ABRIL da linha sobre o total do tomador.
    #  • O3 → TT BRUTO MARÇO da mesma linha (mantendo a mesma ordenação).
    #
    # Funções novas (Dynamic Arrays) precisam do prefixo `_xlfn.` para serem
    # gravadas pelo OOXML — sem ele, abrir no Excel pode resultar em #NAME?.
    bloco_principal = (
        f"_xlfn._xlws.SORT(_xlfn._xlws.FILTER("
        f"{NOME_TABELA}[[{COL_FUNCIONARIO}]:[{COL_TT_ABR}]],"
        f"{_t(COL_TOMADOR)}=$A$1),12,-1)"
    )
    bloco_com_marco = (
        f"_xlfn._xlws.SORT(_xlfn._xlws.FILTER("
        f"{NOME_TABELA}[[{COL_FUNCIONARIO}]:[{COL_TT_MAR}]],"
        f"{_t(COL_TOMADOR)}=$A$1),12,-1)"
    )

    ws["A3"] = '=IFERROR(_xlfn.SEQUENCE(ROWS(B3#)),"")'
    ws["B3"] = f'=IFERROR({bloco_principal},"")'
    ws["N3"] = '=IFERROR(INDEX(B3#,,12)/$M$1,"")'
    ws["O3"] = f'=IFERROR(INDEX({bloco_com_marco},,13),"")'

    # Pré-formata um buffer generoso para receber os valores derramados
    linhas_buf = range(3, 3 + buffer_linhas)
    _formatar_buffer(ws, "A", "0", ALIGN_CENTER, linhas_buf)
    for col_letra in ("B", "C", "D", "E", "F", "G", "H"):
        _formatar_buffer(ws, col_letra, "@", ALIGN_LEFT, linhas_buf)
    for col_letra in ("I", "J", "K", "L", "M", "O"):
        _formatar_buffer(ws, col_letra, FMT_BRL, ALIGN_RIGHT, linhas_buf)
    _formatar_buffer(ws, "N", FMT_PCT, ALIGN_RIGHT, linhas_buf)

    # ─── Painel lateral: Modalidade (Q-S) e Empresa (U-X) ────────────────────
    # Cabeçalhos
    for col_letra, texto in (("Q", "MODALIDADE"), ("R", "FUNCIONÁRIOS"), ("S", "TT BRUTO")):
        cel = ws[f"{col_letra}2"]
        cel.value = texto
        cel.font = FONT_HEADER
        cel.fill = FILL_HEADER
        cel.alignment = ALIGN_CENTER
        cel.border = BORDER
    for col_letra, texto in (
        ("U", "EMPRESA"),
        ("V", "CNPJ"),
        ("W", "FUNCIONÁRIOS"),
        ("X", "TT BRUTO"),
    ):
        cel = ws[f"{col_letra}2"]
        cel.value = texto
        cel.font = FONT_HEADER
        cel.fill = FILL_HEADER
        cel.alignment = ALIGN_CENTER
        cel.border = BORDER

    ws.column_dimensions["Q"].width = 22
    ws.column_dimensions["R"].width = 14
    ws.column_dimensions["S"].width = 16
    ws.column_dimensions["T"].width = 2
    ws.column_dimensions["U"].width = 32
    ws.column_dimensions["V"].width = 22
    ws.column_dimensions["W"].width = 14
    ws.column_dimensions["X"].width = 16

    # Fórmulas das tabelas-resumo (com prefixo _xlfn. para funções modernas)
    ws["Q3"] = (
        f'=IFERROR(_xlfn.UNIQUE(_xlfn._xlws.FILTER('
        f'{_t(COL_TIPO)},{_t(COL_TOMADOR)}=$A$1)),"")'
    )
    ws["R3"] = (
        f'=IFERROR(_xlfn.BYROW(Q3#,_xlfn.LAMBDA(_x,'
        f'COUNTIFS({_t(COL_TOMADOR)},$A$1,{_t(COL_TIPO)},_x))),"")'
    )
    ws["S3"] = (
        f'=IFERROR(_xlfn.BYROW(Q3#,_xlfn.LAMBDA(_x,'
        f'SUMIFS({_t(COL_TT_ABR)},{_t(COL_TOMADOR)},$A$1,{_t(COL_TIPO)},_x))),"")'
    )

    ws["U3"] = (
        f'=IFERROR(_xlfn.UNIQUE(_xlfn._xlws.FILTER('
        f'{_t(COL_EMPRESA)},{_t(COL_TOMADOR)}=$A$1)),"")'
    )
    ws["V3"] = (
        f'=IFERROR(_xlfn.BYROW(U3#,_xlfn.LAMBDA(_x,'
        f'IFERROR(INDEX({_t(COL_CNPJ)},MATCH(_x,{_t(COL_EMPRESA)},0)),""))),"")'
    )
    ws["W3"] = (
        f'=IFERROR(_xlfn.BYROW(U3#,_xlfn.LAMBDA(_x,'
        f'COUNTIFS({_t(COL_TOMADOR)},$A$1,{_t(COL_EMPRESA)},_x))),"")'
    )
    ws["X3"] = (
        f'=IFERROR(_xlfn.BYROW(U3#,_xlfn.LAMBDA(_x,'
        f'SUMIFS({_t(COL_TT_ABR)},{_t(COL_TOMADOR)},$A$1,{_t(COL_EMPRESA)},_x))),"")'
    )

    # Formata buffer dos painéis laterais
    lin_painel = range(3, 3 + 30)
    _formatar_buffer(ws, "Q", "@", ALIGN_LEFT, lin_painel)
    _formatar_buffer(ws, "R", "0", ALIGN_CENTER, lin_painel)
    _formatar_buffer(ws, "S", FMT_BRL, ALIGN_RIGHT, lin_painel)
    _formatar_buffer(ws, "U", "@", ALIGN_LEFT, lin_painel)
    _formatar_buffer(ws, "V", "@", ALIGN_CENTER, lin_painel)
    _formatar_buffer(ws, "W", "0", ALIGN_CENTER, lin_painel)
    _formatar_buffer(ws, "X", FMT_BRL, ALIGN_RIGHT, lin_painel)

    ws.freeze_panes = "B3"
    ws.sheet_view.showGridLines = False


# ─── Orquestração ───────────────────────────────────────────────────────────


def gerar_workbook(
    consolidado: pd.DataFrame, saida: Path, modo: str = "dinamico"
) -> None:
    """Escreve o workbook final.

    Parâmetros
    ----------
    consolidado : DataFrame
        Linhas (tomador, credor) com totais já calculados.
    saida : Path
        Caminho do .xlsx a gerar.
    modo : {"dinamico", "estatico"}
        • dinamico (padrão): GERAL contém todos os detalhes como Excel Table
          (`tbl_dados`) e as abas por tomador são preenchidas via fórmulas
          (FILTER, SORT, SUMIFS, BYROW, LAMBDA). Editar GERAL atualiza as
          demais abas automaticamente. Requer Microsoft 365 / Excel 2021+.
        • estatico: cada aba recebe os valores já calculados, sem fórmulas.
    """
    if modo not in {"dinamico", "estatico"}:
        raise ValueError("modo deve ser 'dinamico' ou 'estatico'")

    wb = Workbook()
    ws_geral = wb.active
    ws_geral.title = "GERAL"

    tomadores = list(TOMADORES_FIXOS)
    extras = sorted(set(consolidado["tomador"]) - set(tomadores))
    for extra in extras:
        tomadores.append(extra)

    if modo == "dinamico":
        _escrever_geral_dinamica(ws_geral, consolidado)
        for tomador in tomadores:
            ws = wb.create_sheet(_nome_aba(tomador))
            _escrever_tomador_dinamico(ws, tomador)
    else:
        geral_view = _consolidar_geral(consolidado)
        _escrever_aba_estatica(ws_geral, "GERAL", geral_view)
        for tomador in tomadores:
            ws = wb.create_sheet(_nome_aba(tomador))
            df_t = consolidado[consolidado["tomador"] == tomador].copy()
            _escrever_aba_estatica(ws, tomador, df_t)

    saida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(saida)


def _consolidar_geral(consolidado: pd.DataFrame) -> pd.DataFrame:
    """Reaggrega o consolidado por credor (somando entre tomadores) — usado na
    aba GERAL do modo estático."""
    if consolidado.empty:
        return consolidado.copy()
    cadastro_cols = ["tipo", "setor", "funcao", "empresa", "cnpj"]
    agg_dict = {
        "nome": "first",
        "eventos_folha": "sum",
        "sal_pf": "sum",
        "tt_bruto_abr": "sum",
        "tt_bruto_marco": "max",
        "provisao_ferias": "sum",
        "provisao_encargos": "sum",
        "status": "first",
    }
    for col in cadastro_cols:
        agg_dict[col] = lambda s: next(
            (v for v in s if isinstance(v, str) and v), pd.NA
        )
    out = consolidado.groupby("nome_norm", as_index=False).agg(agg_dict)
    out["tomador"] = "GERAL"
    return out


def _nome_aba(tomador: str) -> str:
    nome = tomador
    for ch in r"[]:*?/\\":
        nome = nome.replace(ch, " ")
    return nome[:31].strip()


# ─── CLI ─────────────────────────────────────────────────────────────────────


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--abril", type=Path, default=DEFAULT_ABRIL,
                   help="Planilha com o dump ODBC de abril (uma única aba).")
    p.add_argument("--marco", type=Path, default=DEFAULT_MARCO,
                   help="Arquivo FOPA de março, usado como referência de cadastro.")
    p.add_argument("--saida", type=Path, default=DEFAULT_SAIDA,
                   help="Caminho do XLSX gerado.")
    p.add_argument(
        "--modo",
        choices=("dinamico", "estatico"),
        default="dinamico",
        help=(
            "dinamico (padrão): aba GERAL como Excel Table e abas por tomador "
            "como fórmulas dinâmicas (FILTER/SORT/SUMIFS — requer Excel 365). "
            "estatico: gravar valores fixos em cada aba."
        ),
    )
    return p.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    print(f"Lendo abril: {args.abril}")
    abril = carregar_abril(args.abril)
    abril_class = aplicar_classificacao(abril)
    descartados = abril[~abril["codcen"].isin(abril_class["codcen"])].copy()
    if not descartados.empty:
        descartados_unicos = (
            descartados[["codcen", "descen", "descdc"]].drop_duplicates()
        )
        print(
            f"  • {len(descartados)} linhas descartadas "
            f"(receitas, familiares ou tipos fora da folha):"
        )
        for _, lin in descartados_unicos.iterrows():
            print(f"    - {lin['codcen']:<10} {lin['descdc']:<22} {lin['descen']}")

    print(f"Lendo março (BASE+TOMADOR + GERAL): {args.marco}")
    base = carregar_base_tomador(args.marco)
    marco_geral = carregar_geral_marco(args.marco)

    print("Consolidando por tomador / credor…")
    consolidado = consolidar(abril_class, base, marco_geral)

    sem_tomador = abril_class[abril_class["tomador"].isna()]
    if not sem_tomador.empty:
        print(
            f"⚠️  {len(sem_tomador)} lançamento(s) sem tomador identificado — "
            "ajuste REGRAS_TOMADOR se necessário."
        )

    sem_cadastro = consolidado[consolidado["tipo"].isna()]
    if not sem_cadastro.empty:
        print(
            f"  • {len(sem_cadastro)} credor(es) sem cadastro no BASE+TOMADOR de março "
            "(Tipo/Setor/Função em branco):"
        )
        for nome in sorted(sem_cadastro["nome"].unique()):
            print(f"    - {nome}")

    print(f"Gerando workbook ({args.modo}): {args.saida}")
    gerar_workbook(consolidado, args.saida, modo=args.modo)

    total_geral = consolidado["tt_bruto_abr"].sum()
    print(
        "\nResumo por tomador (TT BRUTO ABRIL/2026):"
    )
    resumo = (
        consolidado.groupby("tomador")["tt_bruto_abr"].sum().sort_values(ascending=False)
    )
    for tomador, valor in resumo.items():
        pct = valor / total_geral * 100 if total_geral else 0
        print(f"  {tomador:<24} R$ {valor:>14,.2f}  ({pct:5.1f}%)")
    print(f"  {'TOTAL':<24} R$ {total_geral:>14,.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
