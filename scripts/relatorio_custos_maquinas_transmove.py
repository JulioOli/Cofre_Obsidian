"""
Relatório de custos de máquinas alugadas — formato Transmove (e-mail Andressa).

Layout de saída (Excel):
  - Uma linha por operador (ou máquina) e competência mensal — coluna Competência filtrável
  - Formatação: cabeçalho negrito, valores em R$, datas tipadas

Fontes:
  - ODBC (manutenção e demais despesas): Custos_das_maquinas_alugadas.xlsx
  - Folha: arquivos *FOPA* em 02-Referencias/
"""

from __future__ import annotations

import calendar
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / "02-Referencias"
CUSTOS_ODBC = REFS / "Custos-Maquinas" / "Custos_das_maquinas_alugadas.xlsx"
SAIDA = REFS / "Custos-Maquinas" / "Relatorio_Custos_Maquinas_Transmove.xlsx"

PERIODO_INI = date(2024, 1, 1)
PERIODO_FIM = date(2026, 4, 30)

TIPOS_CUSTO = ["Manutenção", "Salário", "Imposto", "Outros"]

# Decomposição do antigo "Outros" + folha (aba Por operador (detalhado))
TIPOS_DETALHADO_FOPA = ["Salário", "Imposto"]
TIPOS_DETALHADO_ODBC = [
    "Manutenção",
    "Locação da máquina",
    "Combustível",
    "Viagem e diárias",
    "Frete e transporte",
    "Hospedagem",
    "Serviços de terceiros",
    "Encargos ODBC (folha)",
    "Demais",
]
TIPOS_DETALHADO = TIPOS_DETALHADO_FOPA + TIPOS_DETALHADO_ODBC

MES_ABBR = (
    "jan",
    "fev",
    "mar",
    "abr",
    "mai",
    "jun",
    "jul",
    "ago",
    "set",
    "out",
    "nov",
    "dez",
)

# ─── Formatação Excel (padrão do arquivo editado manualmente) ─────────────────

FONT_HEADER = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
FONT_BODY = Font(name="Calibri", size=10)
FONT_TOTAL = Font(name="Calibri", size=10, bold=True)
FILL_HEADER = PatternFill("solid", fgColor="305496")
FILL_TOTAL = PatternFill("solid", fgColor="D9E1F2")
ALIGN_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
ALIGN_LEFT = Alignment(horizontal="left", vertical="center", wrap_text=False)
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")
THIN = Side(border_style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
FMT_BRL = 'R$ #,##0.00;[Red]-R$ #,##0.00;""'
FMT_COMPETENCIA = "mmm/yyyy"
FMT_DATA = "dd/mm/yyyy"
FMT_INTEIRO = "0"

MesChave = tuple[int, int]

# Nome completo no FOPA por apelido do e-mail
NOMES_FOPA: dict[str, str] = {
    "SERGIO": "SERGIO LUIZ RIBEIRO",
    "DANIEL": "DANIEL JUNIOR SANTOS",
    "SILVANO": "SILVANO VIEIRA DE SANTANA",
    "MARCOS": "MARCOS ANTONIO CLAUDIO",
    "JOÃO": "JOAO BATISTA RIBEIRO SILVA",
    "JOAO": "JOAO BATISTA RIBEIRO SILVA",
    "CRISTIANO": "CRISTIANO LUCAS BACHIO",
    "JOSE": "JOSE MANOEL DOS SANTOS",
    "LUCAS": "LUCAS NOGUEIRA TORRES",
    "GERSON": "GERSON TELES DA ROSA",
    "BARRETO": "RIVAEL BARRETO DA SILVA",
}

# Aba ODBC → código da máquina no e-mail
ABA_MAQUINA: dict[str, str] = {
    "PHH0044": "PHH0044",
    "PHH0049": "PHH0049",
    "EHH0044": "EHH0044",
    "EHL0043 e EHL0041": "EHL0043/EHL0041",
}

MANUT_CODCDC = {"7.1.1", "7.1.2", "7.6.3"}
MANUT_KEYWORDS = ("MANUTEN", "PEÇAS DE", "PECAS DE")
IMPOSTO_KEYWORDS = ("ISS", "TAXAS", "IMPOSTO")
SALARIO_ODBC_KEYWORDS = ("SALÁRIO", "SALARIO", "BOLSA ESTAGIO", "PRO LABORE")


@dataclass
class Periodo:
    inicio: date
    fim: date
    fator: float = 1.0  # ex.: 50% dos custos em mar/2025 (Silvano)


@dataclass
class ColunaRelatorio:
    id: str
    local: str
    maquina: str
    operador: str
    aba_odbc: str
    periodos: list[Periodo] = field(default_factory=list)

    @property
    def label(self) -> str:
        maq = self.maquina.replace("/", "·")
        if len(self.periodos) == 1:
            p = self.periodos[0]
            sufixo = f" ({p.inicio:%m/%y}"
            if p.inicio != p.fim:
                sufixo += f"-{p.fim:%m/%y}"
            sufixo += ")"
            if p.fator != 1:
                sufixo = sufixo[:-1] + f" ×{p.fator:.0%})"
        else:
            sufixo = f" ({len(self.periodos)} períodos)"
        return f"{self.local} | {maq} | {self.operador}{sufixo}"


# Cadastro extraído do e-mail (Andressa, 20/05/2026)
COLUNAS: list[ColunaRelatorio] = [
    ColunaRelatorio(
        "resende_sergio",
        "RESENDE",
        "PHH0044",
        "SERGIO",
        "PHH0044",
        [Periodo(date(2025, 11, 1), date(2026, 5, 31))],
    ),
    ColunaRelatorio(
        "resende_daniel",
        "RESENDE",
        "PHH0044",
        "DANIEL",
        "PHH0044",
        [Periodo(date(2025, 4, 1), date(2026, 5, 31))],
    ),
    ColunaRelatorio(
        "resende_silvano_mar25",
        "RESENDE",
        "PHH0044",
        "SILVANO",
        "PHH0044",
        [Periodo(date(2025, 3, 15), date(2025, 3, 31), 0.5)],
    ),
    ColunaRelatorio(
        "resende_silvano_jan26",
        "RESENDE",
        "PHH0044",
        "SILVANO",
        "PHH0044",
        [Periodo(date(2026, 1, 22), date(2026, 1, 31), 0.3)],
    ),
    ColunaRelatorio(
        "piracicaba_marcos",
        "PIRACICABA",
        "PHH0049",
        "MARCOS",
        "PHH0049",
        [Periodo(date(2025, 9, 23), date(2026, 5, 31))],
    ),
    # Joinville — Tesoura (EHH0044)
    ColunaRelatorio(
        "jv_tes_joao",
        "JOINVILLE (Tesoura)",
        "EHH0044",
        "JOÃO",
        "EHH0044",
        [Periodo(date(2024, 1, 11), date(2024, 2, 2))],
    ),
    ColunaRelatorio(
        "jv_tes_crist_1",
        "JOINVILLE (Tesoura)",
        "EHH0044",
        "CRISTIANO",
        "EHH0044",
        [
            Periodo(date(2024, 4, 1), date(2024, 8, 31)),
            Periodo(date(2024, 10, 21), date(2024, 10, 31)),
            Periodo(date(2025, 1, 1), date(2026, 5, 31)),
        ],
    ),
    ColunaRelatorio(
        "jv_tes_jose",
        "JOINVILLE (Tesoura)",
        "EHH0044",
        "JOSE",
        "EHH0044",
        [Periodo(date(2024, 1, 1), date(2024, 1, 31))],
    ),
    ColunaRelatorio(
        "jv_tes_lucas_1",
        "JOINVILLE (Tesoura)",
        "EHH0044",
        "LUCAS",
        "EHH0044",
        [Periodo(date(2024, 3, 1), date(2024, 12, 31))],
    ),
    ColunaRelatorio(
        "jv_tes_lucas_2",
        "JOINVILLE (Tesoura)",
        "EHH0044",
        "LUCAS",
        "EHH0044",
        [Periodo(date(2025, 2, 1), date(2026, 5, 31))],
    ),
    ColunaRelatorio(
        "jv_tes_gerson",
        "JOINVILLE (Tesoura)",
        "EHH0044",
        "GERSON",
        "EHH0044",
        [
            Periodo(date(2024, 12, 1), date(2024, 12, 31)),
            Periodo(date(2025, 1, 1), date(2025, 1, 31)),
        ],
    ),
    # Joinville — Garra (EHL0043 até set/2024, EHL0041 depois; e-mail da Andressa trazia EHH por engano)
    ColunaRelatorio(
        "jv_gar_barreto_1",
        "JOINVILLE (Garra)",
        "EHL0043",
        "BARRETO",
        "EHL0043 e EHL0041",
        [Periodo(date(2024, 1, 1), date(2024, 10, 31))],
    ),
    ColunaRelatorio(
        "jv_gar_barreto_2",
        "JOINVILLE (Garra)",
        "EHL0043",
        "BARRETO",
        "EHL0043 e EHL0041",
        [Periodo(date(2024, 12, 1), date(2024, 12, 11))],
    ),
    ColunaRelatorio(
        "jv_gar_barreto_3",
        "JOINVILLE (Garra)",
        "EHL0041",
        "BARRETO",
        "EHL0043 e EHL0041",
        [Periodo(date(2025, 1, 1), date(2026, 4, 30))],
    ),
    ColunaRelatorio(
        "jv_gar_crist_1",
        "JOINVILLE (Garra)",
        "EHL0043",
        "CRISTIANO",
        "EHL0043 e EHL0041",
        [Periodo(date(2024, 1, 1), date(2024, 2, 29))],
    ),
    ColunaRelatorio(
        "jv_gar_crist_2",
        "JOINVILLE (Garra)",
        "EHL0043",
        "CRISTIANO",
        "EHL0043 e EHL0041",
        [
            Periodo(date(2024, 9, 1), date(2024, 11, 30)),
            Periodo(date(2025, 8, 1), date(2026, 5, 31)),
        ],
    ),
    ColunaRelatorio(
        "jv_gar_joao",
        "JOINVILLE (Garra)",
        "EHL0043",
        "JOÃO",
        "EHL0043 e EHL0041",
        [Periodo(date(2024, 3, 1), date(2024, 11, 30))],
    ),
    ColunaRelatorio(
        "jv_gar_lucas",
        "JOINVILLE (Garra)",
        "EHL0041",
        "LUCAS",
        "EHL0043 e EHL0041",
        [
            Periodo(date(2024, 12, 1), date(2025, 1, 31)),
            Periodo(date(2025, 2, 1), date(2026, 5, 31)),
        ],
    ),
]

FOPA_DIR = REFS / "FOPA"
FOPA_ARQUIVOS = [
    FOPA_DIR / "FOPA GERAL 2025.csv",
    FOPA_DIR / "01_2026_Jan_Rel_FOPA.csv",
    FOPA_DIR / "02_2026_Fev_Rel_FOPA.csv",
    FOPA_DIR / "03_2026_Mar_Rel_FOPA.csv",
    FOPA_DIR / "04_2026_Abr_Rel_FOPA.csv",
]


def norm_txt(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = s.encode("ascii", "ignore").decode("ascii").upper()
    return re.sub(r"\s+", " ", s).strip()


def parse_moeda(val) -> float:
    if pd.isna(val):
        return 0.0
    t = str(val).strip()
    if not t or t.lower() in {"nan", "-", ""}:
        return 0.0
    neg = t.startswith("(") and t.endswith(")")
    t = t.replace("R$", "").replace("(", "").replace(")", "").strip()
    t = t.replace(".", "").replace(",", ".")
    try:
        v = float(t)
    except ValueError:
        return 0.0
    return -v if neg else v


def parse_competencia(comp: str) -> tuple[int, int] | None:
    """Converte 'abr/26', 'jan-25', 'mar/25' em (ano, mês)."""
    c = norm_txt(comp).replace("-", "/")
    m = re.match(r"([A-Z]{3})/(\d{2,4})", c)
    if not m:
        return None
    meses = {
        "JAN": 1,
        "FEV": 2,
        "MAR": 3,
        "ABR": 4,
        "MAI": 5,
        "JUN": 6,
        "JUL": 7,
        "AGO": 8,
        "SET": 9,
        "OUT": 10,
        "NOV": 11,
        "DEZ": 12,
    }
    mes = meses.get(m.group(1))
    if not mes:
        return None
    ano_txt = m.group(2)
    ano = int(ano_txt) if len(ano_txt) == 4 else 2000 + int(ano_txt)
    return ano, mes


def classificar_odbc(descdc: str, codcdc: str) -> str:
    """Agrupamento resumido (4 linhas do e-mail da Andressa)."""
    return _mapear_detalhado_para_resumo(classificar_odbc_detalhado(descdc, codcdc))


def classificar_odbc_detalhado(descdc: str, codcdc: str) -> str:
    desc = norm_txt(descdc)
    cod = str(codcdc or "").strip()

    if any(k in desc for k in SALARIO_ODBC_KEYWORDS) or "FGTS" in desc or cod in {
        "7.3.2",
        "7.3.20",
        "7.3.21",
    }:
        return "Encargos ODBC (folha)"
    if cod == "7.3.7" or "ALUGUEL DE FUNCIONARIO" in desc:
        return "Hospedagem"
    if cod in {"7.1.4", "7.1.5", "7.1.23"} or "COMBUSTIVEL" in desc:
        return "Combustível"
    if cod == "7.1.3" or ("LOCACAO" in desc and "EQUIPAMENT" in desc):
        return "Locação da máquina"
    if cod in {"7.1.18", "7.3.10", "7.1.21"} or "FRETE" in desc or "CARRETO" in desc:
        return "Frete e transporte"
    if (
        cod in {"7.1.8", "7.3.5"}
        or "VIAGEM" in desc
        or "DIARIA" in desc
        or "ALIMENTACAO" in desc
    ):
        return "Viagem e diárias"
    if cod in MANUT_CODCDC or any(k in desc for k in MANUT_KEYWORDS):
        return "Manutenção"
    if (
        cod in {"7.1.16", "7.5.9", "7.1.17", "7.1.20"}
        or "SERVICOS DE TERCEIROS" in desc
        or "CONSULTORIA" in desc
        or "RASTREADOR" in desc
        or "SISTEMAS" in desc
    ):
        return "Serviços de terceiros"
    return "Demais"


def _mapear_detalhado_para_resumo(tipo_detalhado: str) -> str:
    if tipo_detalhado == "Manutenção":
        return "Manutenção"
    if tipo_detalhado in {"Encargos ODBC (folha)"}:
        return "Outros"  # folha oficial está em Salário/Imposto (FOPA)
    return "Outros"


def nome_coincide(nome_lancamento: str, apelido: str) -> bool:
    full = NOMES_FOPA.get(apelido, apelido)
    nl = norm_txt(nome_lancamento)
    partes = [p for p in norm_txt(full).split() if len(p) > 2]
    if not partes:
        return False
    # exige sobrenome + um primeiro nome
    return partes[-1] in nl and partes[0] in nl


def data_no_periodo(dt: date, periodos: list[Periodo]) -> float:
    """Retorna fator de alocação se a data cair em algum período."""
    for p in periodos:
        if p.inicio <= dt <= p.fim:
            return p.fator
    return 0.0


def mes_no_periodo(ano: int, mes: int, periodos: list[Periodo]) -> float:
    """Fator para competência mensal (usa fator do período que cobre o mês)."""
    ini_mes = date(ano, mes, 1)
    fim_mes = date(ano, mes, calendar.monthrange(ano, mes)[1])

    fatores = []
    for p in periodos:
        overlap_ini = max(ini_mes, p.inicio)
        overlap_fim = min(fim_mes, p.fim)
        if overlap_ini <= overlap_fim:
            fatores.append(p.fator)
    return max(fatores) if fatores else 0.0


def carregar_odbc() -> dict[str, pd.DataFrame]:
    if not CUSTOS_ODBC.exists():
        raise FileNotFoundError(CUSTOS_ODBC)
    xl = pd.ExcelFile(CUSTOS_ODBC)
    out = {}
    for aba in xl.sheet_names:
        df = pd.read_excel(CUSTOS_ODBC, sheet_name=aba)
        df["pagamento"] = pd.to_datetime(df["iterea_pagamento"], errors="coerce")
        df = df[df["pagamento"].notna()].copy()
        # Despesas no ODBC costumam vir negativas; custo = módulo do valor.
        df["valor"] = (
            pd.to_numeric(df["valor_centro"], errors="coerce").fillna(0).abs()
        )
        df["tipo_custo"] = df.apply(
            lambda r: classificar_odbc(r.get("descdc", ""), r.get("codcdc", "")), axis=1
        )
        df["tipo_detalhado"] = df.apply(
            lambda r: classificar_odbc_detalhado(r.get("descdc", ""), r.get("codcdc", "")),
            axis=1,
        )
        out[aba] = df
    return out


def _carregar_fopa_resumido(path: Path) -> pd.DataFrame | None:
    """Layout compacto (ex.: 01_2026_Jan_Rel_FOPA.csv)."""
    raw = pd.read_csv(path, sep=";", encoding="latin-1", header=None, dtype=str)
    idx = raw.iloc[:, 0].astype(str).str.strip().eq("Qtde")
    if not idx.any():
        return None
    start = int(idx.idxmax()) + 1
    body = raw.iloc[start:]
    body = body[body.iloc[:, 1].notna() & (body.iloc[:, 1].astype(str).str.strip() != "")]
    meses_arq = {"JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4}
    mes_num = next((v for k, v in meses_arq.items() if k in path.name.upper()), 1)
    mes_label = next((k.lower() for k in meses_arq if k in path.name.upper()), "jan")
    ano = 2026 if "2026" in path.name else 2025
    rows = []
    for _, r in body.iterrows():
        func = str(r.iloc[1]).strip()
        if not func or func.upper() == "NAN":
            continue
        rows.append(
            {
                "funcionario": func,
                "competencia": f"{mes_label}/{str(ano)[-2:]}",
                "total_bruto": r.iloc[12],  # TT BRUTO do mês
                "total_encargos": r.iloc[9],  # Provisão de encargos (layout resumido)
                "_arquivo": path.name,
            }
        )
    return pd.DataFrame(rows) if rows else None


def _normalizar_fopa_bruto(df: pd.DataFrame) -> pd.DataFrame:
    col_func = next((c for c in df.columns if norm_txt(c).startswith("FUNCION")), None)
    col_comp = next((c for c in df.columns if "COMPET" in norm_txt(c)), None)
    col_bruto = next(
        (
            c
            for c in df.columns
            if norm_txt(c) in {"TOTAL BRUTO", "TOTAL BRUTO + PF"}
            or "TT BRUTO" in norm_txt(c)
        ),
        None,
    )
    col_enc = next((c for c in df.columns if norm_txt(c) == "TOTAL ENCARGOS"), None)
    if not all([col_func, col_comp, col_bruto]):
        raise KeyError(f"Colunas FOPA não encontradas: {df.columns.tolist()[:12]}")
    out = df.rename(
        columns={
            col_func: "funcionario",
            col_comp: "competencia",
            col_bruto: "total_bruto",
        }
    )
    if col_enc:
        out = out.rename(columns={col_enc: "total_encargos"})
    else:
        out["total_encargos"] = 0
    return out


def carregar_fopa() -> pd.DataFrame:
    frames = []
    for path in FOPA_ARQUIVOS:
        if not path.exists():
            continue
        if path.name.startswith("01_2026"):
            resumido = _carregar_fopa_resumido(path)
            if resumido is not None:
                frames.append(resumido)
                continue
        if path.suffix.lower() == ".csv":
            bruto = pd.read_csv(path, sep=";", encoding="latin-1", low_memory=False)
        else:
            bruto = pd.read_excel(path, sheet_name=0)
        bruto["_arquivo"] = path.name
        frames.append(_normalizar_fopa_bruto(bruto))
    if not frames:
        raise FileNotFoundError("Nenhum arquivo FOPA encontrado em 02-Referencias/")
    fopa = pd.concat(frames, ignore_index=True)
    parsed = fopa["competencia"].map(parse_competencia)
    fopa["ano"] = parsed.map(lambda x: x[0] if x else None)
    fopa["mes"] = parsed.map(lambda x: x[1] if x else None)
    fopa["func_norm"] = fopa["funcionario"].map(norm_txt)
    fopa["salario"] = fopa["total_bruto"].map(parse_moeda)
    fopa["imposto"] = fopa["total_encargos"].map(parse_moeda)
    return fopa


def competencia_label(ano: int, mes: int) -> str:
    return f"{MES_ABBR[mes - 1]}/{ano}"


def init_matriz_mensal(tipos: list[str]) -> dict[str, dict[MesChave, dict[str, float]]]:
    return {c.id: {} for c in COLUNAS}


def _bucket_mes(
    store: dict[str, dict[MesChave, dict[str, float]]],
    col_id: str,
    ano: int,
    mes: int,
    tipos: list[str],
) -> dict[str, float]:
    por_mes = store.setdefault(col_id, {})
    return por_mes.setdefault((ano, mes), {t: 0.0 for t in tipos})


def linha_na_maquina(row: pd.Series, maquina: str, aba_odbc: str) -> bool:
    """Na aba combinada Garra, filtra por EHL0043 ou EHL0041 no descen/observação."""
    if aba_odbc != "EHL0043 e EHL0041":
        return True
    texto = norm_txt(f"{row.get('descen', '')} {row.get('observacao', '')}")
    placa = norm_txt(maquina)
    return placa in texto


def acumular_odbc(
    odbc: dict[str, pd.DataFrame],
    matriz_mes: dict[str, dict[MesChave, dict[str, float]]],
    matriz_det_mes: dict[str, dict[MesChave, dict[str, float]]],
    detalhe: list,
) -> None:
    for col in COLUNAS:
        df = odbc.get(col.aba_odbc)
        if df is None:
            continue
        for _, row in df.iterrows():
            dt = row["pagamento"].date()
            if dt < PERIODO_INI or dt > PERIODO_FIM:
                continue
            fator = data_no_periodo(dt, col.periodos)
            if fator <= 0:
                continue
            if not linha_na_maquina(row, col.maquina, col.aba_odbc):
                continue
            if not nome_coincide(row.get("nome", ""), col.operador):
                continue
            ano, mes = dt.year, dt.month
            tipo = row["tipo_custo"]
            tipo_d = row["tipo_detalhado"]
            val = float(row["valor"]) * fator
            b = _bucket_mes(matriz_mes, col.id, ano, mes, TIPOS_CUSTO)
            b[tipo] = b.get(tipo, 0) + val
            bd = _bucket_mes(matriz_det_mes, col.id, ano, mes, TIPOS_DETALHADO)
            bd[tipo_d] = bd.get(tipo_d, 0) + val
            comp = date(ano, mes, 1)
            detalhe.append(
                {
                    "Local": col.local,
                    "Máquina": col.maquina,
                    "Operador": col.operador,
                    "Competência": comp,
                    "Ano": ano,
                    "Mês": mes,
                    "Competência texto": competencia_label(ano, mes),
                    "fonte": "ODBC",
                    "Data pagamento": dt,
                    "tipo": tipo,
                    "tipo_detalhado": tipo_d,
                    "valor": val,
                    "descdc": row.get("descdc"),
                    "nome": row.get("nome"),
                    "documento": row.get("documento"),
                }
            )


def acumular_fopa(
    fopa: pd.DataFrame,
    matriz_mes: dict[str, dict[MesChave, dict[str, float]]],
    matriz_det_mes: dict[str, dict[MesChave, dict[str, float]]],
    detalhe: list,
) -> None:
    for col in COLUNAS:
        nome = norm_txt(NOMES_FOPA.get(col.operador, col.operador))
        sub = fopa[fopa["func_norm"] == nome]
        for _, row in sub.iterrows():
            if pd.isna(row["ano"]) or pd.isna(row["mes"]):
                continue
            ano, mes = int(row["ano"]), int(row["mes"])
            ref = date(ano, mes, 1)
            if ref < date(PERIODO_INI.year, PERIODO_INI.month, 1):
                continue
            if ref > date(PERIODO_FIM.year, PERIODO_FIM.month, 1):
                continue
            fator = mes_no_periodo(ano, mes, col.periodos)
            if fator <= 0:
                continue
            sal = row["salario"] * fator
            imp = row["imposto"] * fator
            b = _bucket_mes(matriz_mes, col.id, ano, mes, TIPOS_CUSTO)
            b["Salário"] = b.get("Salário", 0) + sal
            b["Imposto"] = b.get("Imposto", 0) + imp
            bd = _bucket_mes(matriz_det_mes, col.id, ano, mes, TIPOS_DETALHADO)
            bd["Salário"] = bd.get("Salário", 0) + sal
            bd["Imposto"] = bd.get("Imposto", 0) + imp
            base = {
                "Local": col.local,
                "Máquina": col.maquina,
                "Operador": col.operador,
                "Competência": ref,
                "Ano": ano,
                "Mês": mes,
                "Competência texto": competencia_label(ano, mes),
                "fonte": "FOPA",
                "Data pagamento": None,
                "descdc": row.get("competencia"),
                "nome": row.get("funcionario"),
                "documento": row.get("_arquivo"),
            }
            detalhe.append({**base, "tipo": "Salário", "tipo_detalhado": "Salário", "valor": sal})
            detalhe.append({**base, "tipo": "Imposto", "tipo_detalhado": "Imposto", "valor": imp})


def _linha_competencia(col: ColunaRelatorio, ano: int, mes: int) -> dict:
    return {
        "Local": col.local,
        "Máquina": col.maquina,
        "Operador": col.operador,
        "Competência": date(ano, mes, 1),
        "Ano": ano,
        "Mês": mes,
        "Competência texto": competencia_label(ano, mes),
    }


def _iter_meses_matriz(
    matriz_mes: dict[str, dict[MesChave, dict[str, float]]],
) -> list[tuple[ColunaRelatorio, int, int, dict[str, float]]]:
    itens: list[tuple[ColunaRelatorio, int, int, dict[str, float]]] = []
    for col in COLUNAS:
        for (ano, mes), vals in sorted(matriz_mes.get(col.id, {}).items()):
            if sum(vals.values()) == 0:
                continue
            itens.append((col, ano, mes, vals))
    return itens


def montar_por_operador_mensal(
    matriz_mes: dict[str, dict[MesChave, dict[str, float]]],
) -> pd.DataFrame:
    linhas = []
    for col, ano, mes, vals in _iter_meses_matriz(matriz_mes):
        row = _linha_competencia(col, ano, mes)
        for tipo in TIPOS_CUSTO:
            row[tipo] = vals.get(tipo, 0)
        row["Total"] = sum(vals.get(tipo, 0) for tipo in TIPOS_CUSTO)
        linhas.append(row)
    df = pd.DataFrame(linhas)
    if df.empty:
        return df
    return df.sort_values(["Competência", "Local", "Máquina", "Operador"]).reset_index(
        drop=True
    )


def montar_por_operador_detalhado_mensal(
    matriz_det_mes: dict[str, dict[MesChave, dict[str, float]]],
    matriz_mes: dict[str, dict[MesChave, dict[str, float]]],
) -> pd.DataFrame:
    linhas = []
    for col, ano, mes, vals in _iter_meses_matriz(matriz_det_mes):
        row = _linha_competencia(col, ano, mes)
        for tipo in TIPOS_DETALHADO:
            row[tipo] = vals.get(tipo, 0)
        row["Total ODBC"] = sum(vals.get(t, 0) for t in TIPOS_DETALHADO_ODBC)
        row["Total geral"] = sum(vals.get(t, 0) for t in TIPOS_DETALHADO)
        resumo = matriz_mes.get(col.id, {}).get((ano, mes), {})
        row["Total (4 categorias)"] = sum(resumo.get(t, 0) for t in TIPOS_CUSTO)
        linhas.append(row)
    df = pd.DataFrame(linhas)
    if df.empty:
        return df
    return df.sort_values(["Competência", "Local", "Máquina", "Operador"]).reset_index(
        drop=True
    )


def montar_por_maquina_mensal(
    matriz_mes: dict[str, dict[MesChave, dict[str, float]]],
) -> pd.DataFrame:
    agreg: dict[tuple[str, str, int, int], dict[str, float]] = {}
    for col, ano, mes, vals in _iter_meses_matriz(matriz_mes):
        chave = (col.local, col.maquina, ano, mes)
        bucket = agreg.setdefault(chave, {t: 0.0 for t in TIPOS_CUSTO})
        for tipo in TIPOS_CUSTO:
            bucket[tipo] += vals.get(tipo, 0)

    linhas = []
    for (local, maquina, ano, mes), vals in sorted(agreg.items()):
        row = {
            "Local": local,
            "Máquina": maquina,
            "Competência": date(ano, mes, 1),
            "Ano": ano,
            "Mês": mes,
            "Competência texto": competencia_label(ano, mes),
        }
        for tipo in TIPOS_CUSTO:
            row[tipo] = vals.get(tipo, 0)
        row["Total"] = sum(vals.get(tipo, 0) for tipo in TIPOS_CUSTO)
        linhas.append(row)
    return pd.DataFrame(linhas)


def formatar_aba(
    ws,
    df: pd.DataFrame,
    *,
    colunas_moeda: list[str],
    colunas_data: list[str] | None = None,
    colunas_inteiro: list[str] | None = None,
    linhas_total: set[int] | None = None,
) -> None:
    colunas_data = colunas_data or []
    colunas_inteiro = colunas_inteiro or []
    linhas_total = linhas_total or set()
    col_idx = {name: i + 1 for i, name in enumerate(df.columns)}

    for c in range(1, len(df.columns) + 1):
        cell = ws.cell(1, c)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER

    for r in range(2, ws.max_row + 1):
        is_total = r in linhas_total
        for c in range(1, ws.max_column + 1):
            cell = ws.cell(r, c)
            cell.font = FONT_TOTAL if is_total else FONT_BODY
            cell.border = BORDER
            nome = df.columns[c - 1]
            if nome in colunas_moeda:
                cell.alignment = ALIGN_RIGHT
                cell.number_format = FMT_BRL
            elif nome in colunas_data:
                cell.alignment = ALIGN_CENTER
                cell.number_format = (
                    FMT_COMPETENCIA if nome == "Competência" else FMT_DATA
                )
            elif nome in colunas_inteiro:
                cell.alignment = ALIGN_CENTER
                cell.number_format = FMT_INTEIRO
            else:
                cell.alignment = ALIGN_LEFT

        if is_total:
            for c in range(1, ws.max_column + 1):
                ws.cell(r, c).fill = FILL_TOTAL

    for nome, idx in col_idx.items():
        if nome in colunas_moeda:
            width = 14
        elif nome in ("Competência", "Data pagamento"):
            width = 14
        elif nome in ("Ano", "Mês"):
            width = 8
        elif nome == "Competência texto":
            width = 12
        else:
            sample = df[nome].astype(str).head(50).map(len).max() if len(df) else 10
            width = min(max(sample + 2, len(nome) + 2), 40)
        ws.column_dimensions[get_column_letter(idx)].width = width

    ws.freeze_panes = "A2"
    if ws.max_row > 1:
        ws.auto_filter.ref = f"A1:{get_column_letter(ws.max_column)}{ws.max_row}"


def exportar_excel(
    sheets: list[tuple[str, pd.DataFrame, dict]],
) -> None:
    with pd.ExcelWriter(SAIDA, engine="openpyxl", datetime_format=FMT_DATA) as writer:
        for nome_aba, df, fmt in sheets:
            if df is None or df.empty:
                vazio = pd.DataFrame({"Aviso": ["Sem dados no período"]})
                vazio.to_excel(writer, sheet_name=nome_aba, index=False)
                formatar_aba(
                    writer.sheets[nome_aba],
                    vazio,
                    colunas_moeda=[],
                    colunas_data=[],
                    colunas_inteiro=[],
                )
                continue
            export = df.copy()
            if "Competência" in export.columns:
                export["Competência"] = pd.to_datetime(export["Competência"])
            if "Data pagamento" in export.columns:
                export["Data pagamento"] = pd.to_datetime(
                    export["Data pagamento"], errors="coerce"
                )
            export.to_excel(writer, sheet_name=nome_aba, index=False)
            formatar_aba(writer.sheets[nome_aba], export, **fmt)


def _fmt_operador(df: pd.DataFrame) -> dict:
    cols = list(df.columns) if not df.empty else []
    return {
        "colunas_moeda": [c for c in cols if c in TIPOS_CUSTO + ["Total"]],
        "colunas_data": [c for c in cols if c == "Competência"],
        "colunas_inteiro": [c for c in cols if c in ("Ano", "Mês")],
    }


def _fmt_operador_det(df: pd.DataFrame) -> dict:
    cols = list(df.columns) if not df.empty else []
    money = [
        c
        for c in cols
        if c in TIPOS_DETALHADO + ["Total ODBC", "Total geral", "Total (4 categorias)"]
    ]
    return {
        "colunas_moeda": money,
        "colunas_data": [c for c in cols if c == "Competência"],
        "colunas_inteiro": [c for c in cols if c in ("Ano", "Mês")],
    }


def _fmt_detalhe(df: pd.DataFrame) -> dict:
    cols = list(df.columns) if not df.empty else []
    return {
        "colunas_moeda": [c for c in cols if c == "valor"],
        "colunas_data": [c for c in cols if c in ("Competência", "Data pagamento")],
        "colunas_inteiro": [c for c in cols if c in ("Ano", "Mês")],
    }


def main() -> None:
    odbc = carregar_odbc()
    fopa = carregar_fopa()

    matriz_mes = init_matriz_mensal(TIPOS_CUSTO)
    matriz_det_mes = init_matriz_mensal(TIPOS_DETALHADO)
    detalhe: list[dict] = []

    acumular_odbc(odbc, matriz_mes, matriz_det_mes, detalhe)
    acumular_fopa(fopa, matriz_mes, matriz_det_mes, detalhe)

    resumo_operador = montar_por_operador_mensal(matriz_mes)
    resumo_operador_det = montar_por_operador_detalhado_mensal(matriz_det_mes, matriz_mes)
    resumo_maquina = montar_por_maquina_mensal(matriz_mes)

    cadastro = pd.DataFrame(
        [
            {
                "ID": c.id,
                "Coluna": c.label,
                "Local": c.local,
                "Máquina": c.maquina,
                "Operador (e-mail)": c.operador,
                "Nome FOPA": NOMES_FOPA.get(c.operador, ""),
                "Aba ODBC": c.aba_odbc,
                "Períodos": "; ".join(
                    f"{p.inicio:%d/%m/%Y}-{p.fim:%d/%m/%Y}"
                    + (f" ×{p.fator:.0%}" if p.fator != 1 else "")
                    for p in c.periodos
                ),
            }
            for c in COLUNAS
        ]
    )

    notas = pd.DataFrame(
        [
            {
                "Item": "Período do relatório",
                "Descrição": f"{PERIODO_INI:%d/%m/%Y} a {PERIODO_FIM:%d/%m/%Y}",
            },
            {
                "Item": "Salário / Imposto",
                "Descrição": "FOPA: TOTAL BRUTO e TOTAL ENCARGOS, filtrados por competência e período do operador.",
            },
            {
                "Item": "Manutenção / Outros",
                "Descrição": "ODBC (Custos_das_maquinas_alugadas.xlsx), lançamentos no CC da máquina com nome do credor = operador.",
            },
            {
                "Item": "FOPA disponível",
                "Descrição": "2025: jan–mar (FOPA GERAL 2025). 2026: jan–abr. Meses de 2024 sem arquivo FOPA nesta pasta — salário/imposto de 2024 podem ficar zerados.",
            },
            {
                "Item": "ODBC disponível",
                "Descrição": "Abas filtradas por data de pagamento; verifique se extrair 01/2024 exige atualizar a extração ODBC.",
            },
            {
                "Item": "Placas Garra (Joinville)",
                "Descrição": "E-mail citava EHH0043/EHH0041 por engano; relatório usa EHL0043 e EHL0041 (abas e descen ODBC).",
            },
            {
                "Item": "Organização mensal",
                "Descrição": "Uma linha por competência (mês). Use filtros em Competência, Ano, Mês ou Competência texto. Vigência do operador no e-mail: aba Cadastro email.",
            },
            {
                "Item": "Por operador (detalhado)",
                "Descrição": "Decomposição do ODBC antes agrupado em 'Outros'. Encargos ODBC (folha) podem coincidir com Imposto do FOPA — priorizar FOPA para folha.",
            },
        ]
    )

    df_detalhe = pd.DataFrame(detalhe)
    if not df_detalhe.empty:
        df_detalhe = df_detalhe.sort_values(
            ["Competência", "Local", "Máquina", "Operador", "fonte"],
            na_position="last",
        ).reset_index(drop=True)

    exportar_excel(
        [
            ("Por operador", resumo_operador, _fmt_operador(resumo_operador)),
            (
                "Por operador (detalhado)",
                resumo_operador_det,
                _fmt_operador_det(resumo_operador_det),
            ),
            ("Por máquina", resumo_maquina, _fmt_operador(resumo_maquina)),
            (
                "Cadastro email",
                cadastro,
                {"colunas_moeda": [], "colunas_data": [], "colunas_inteiro": []},
            ),
            ("Detalhe", df_detalhe, _fmt_detalhe(df_detalhe)),
            (
                "Notas",
                notas,
                {"colunas_moeda": [], "colunas_data": [], "colunas_inteiro": []},
            ),
        ]
    )

    print(f"Relatório gerado: {SAIDA}")
    print(f"Linhas mensais (operador): {len(resumo_operador)}")
    if not resumo_operador.empty:
        print(resumo_operador.head(8).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
