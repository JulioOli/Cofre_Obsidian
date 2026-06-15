"""
Monta planilha no layout da folha de pagamento (ex.: base_R_fechamento_folha_pagamento_correto.xlsx)
a partir de base_R.csv (n4_CC + valor_nf), conta 7.3.1 SALÁRIOS.

Regras alinhadas ao arquivo corrigido de referência:
- n1_CC usa sempre a descrição oficial do SAGI no nível 1 (ex.: 1.1 G3S ESCRITORIO).
- n1_centro_custo usa o rótulo de Segmento em exceções (ex.: 1.1 -> PILARES em vez de G3S ESCRITORIO).
- Valores em despesa (folha) saem negativos; demais colunas financeiras espelham valor_nf.
- filial derivada do código n2 (1.2.5 -> G3S PRUDENTE, etc.), com exceções por n4 (ex.: 1.7.1.8.1 -> G&S PRUDENTE).
- descrições de CC preferem o cadastro SAGI (rótulos truncados da planilha FOPA/R são ignorados quando existir código no SAGI).
- códigos com typo na exportação FOPA são corrigidos (ex.: 1.7.8.1.1 -> 1.7.1.8.1).
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from calendar import monthrange
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from fechamento_excel import gravar_fechamento_excel

ROOT = Path(__file__).resolve().parent.parent.parent
REFS = ROOT / "02-Referencias"

_CC_LINE = re.compile(r"^\s*(\d+(?:\.\d+)*)\s*;")
_LEAF_CC = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$")
_PLACA_COD_CC = re.compile(r"^(\S+)\s+(\d+(?:\.\d+)+)\s*$")

# Coluna Segmento por código n1 (X.Y) — igual ao uso no FECHAMENTO_ODBC / folha corrigida.
SEGMENTO_POR_N1: dict[str, str] = {
    "1.1": "PILARES",
    "1.2": "SELETIVA",
    "1.3": "BRACOFER",
    "1.4": "TRANSMOVE",
    "1.5": "EKIPA",
    "1.7": "EKIPA SERVICOS - G&S",
    "1.8": "RENDER LOCACOES",
    "1.12": "NVS SERVICOS DE ENTULHO",
    "2.2": "SELETIVA",
    "2.7": "EKIPA SERVICOS - G&S",
}

# n1_centro_custo: quando o nome “curto” do segmento difere da descrição SAGI usada em n1_CC.
N1_CENTRO_CUSTO_OVERRIDE: dict[str, str] = {
    "1.1": "PILARES",
}

CONTA_FOLHA_COD = "7.3.1"
CONTA_FOLHA_NOME = "SALÁRIOS"
CONTA_FOLHA_DESCR = "7.3.1 SALÁRIOS"

# filial por n2_cod_centro_custo (base em base_R_fechamento_folha_pagamento_correto.xlsx).
FILIAL_POR_N2_COD: dict[str, str] = {
    "1.1.2": "G3S PRUDENTE",
    "1.1.3": "G3S ADM",
    "1.1.4": "G3S ADM",
    "1.1.5": "G3S ADM",
    "1.1.10": "G3S ADM",
    "1.1.14": "G3S ADM",
    "1.1.15": "G&S PRUDENTE",
    "1.2.1": "G3S ADM",
    "1.2.2": "G3S DOURADOS",
    "1.2.3": "G3S LONDRINA",
    "1.2.4": "G3S MARINGA",
    "1.2.5": "G3S PRUDENTE",
    "1.2.7": "G3S CAMPO GRANDE",
    "1.2.8": "G3S CIDADE ALTA",
    "1.3.1": "BRACOFER",
    "1.4.1": "G&S PRUDENTE",
    "1.5.1": "RSE",
    "1.7.1": "G&S BARUERI",
    "1.7.3": "G&S BARUERI",
    "1.7.4": "G&S CAMPO GRANDE",
    "1.7.5": "G&S DOURADOS",
    "1.7.6": "G&S LONDRINA",
    "1.7.7": "G&S MARINGA",
    "1.7.8": "G&S PRUDENTE",
    "1.7.2": "G&S PRUDENTE",
    "1.7.9": "G&S PRUDENTE",
    "1.7.10": "G&S PRUDENTE",
    "1.6.3": "RSE",
    "1.8.1": "G3S PRUDENTE",
}

# Typos frequentes na exportação FOPA / planilha R (ex.: 1.7.8.1.1 → 1.7.1.8.1).
CODIGO_CC_CORRECAO_FOPA: dict[str, str] = {
    "1.7.8.1.1": "1.7.1.8.1",
}

# Filial por n4 quando difere do n2 (ex.: contrato TUPY em 1.7.1.8.1 → G&S PRUDENTE).
FILIAL_POR_N4_COD: dict[str, str] = {
    "1.7.1.8.1": "G&S PRUDENTE",
}

_COLS_VALOR_NUMERICO = ("valor_nf", "valor_pago", "valor_conta", "Valor Oficial")

LAYOUT_CORRETO = REFS / "FOPA" / "base_R_fechamento_folha_pagamento_correto.xlsx"
TEMPLATE_FECHAMENTO_ODBC = REFS / "Fechamento" / "FECHAMENTO_ODBC_2026_04.xlsx"


@dataclass
class ParametrosFolha:
    titulo: str
    observacao: str
    credor: str
    origem: str
    sistema: str
    dados_auxiliares: str
    data_nf: date
    data_pagamento: date
    multiplicador_valor: float = -1.0
    cod_conta: str = CONTA_FOLHA_COD
    conta: str = CONTA_FOLHA_NOME
    cod_conta_descr: str = CONTA_FOLHA_DESCR


def _norm_desc(s: str) -> str:
    s = re.sub(r"\s+", " ", s.strip())
    return s


def _descr_sagi_placeholder(desc: str) -> bool:
    """SAGI usa XXXXXX (ou vazio) quando o ativo ainda não foi nomeado no cadastro."""
    d = _norm_desc(desc).upper()
    return not d or d == "XXXXXX" or set(d) == {"X"}


def carregar_mapa_cc_sagi(path: Path) -> dict[str, str]:
    """Código hierárquico (ex.: 1.2.5.1) -> descrição do centro no relatório SAGI."""
    texto = path.read_text(encoding="latin-1", errors="replace")
    mapeamento: dict[str, str] = {}
    for line in texto.splitlines():
        m = _CC_LINE.match(line)
        if not m:
            continue
        cod = m.group(1)
        tail = line[m.end() :]
        partes = [p for p in tail.split(";") if p.strip()]
        desc = partes[0] if partes else tail
        mapeamento[cod] = _norm_desc(desc)
    return mapeamento


def parse_valor_br(s: str) -> float:
    s = str(s).strip()
    s = re.sub(r"[^\d,.-]", "", s)
    if not s:
        return float("nan")
    s = s.replace(".", "").replace(",", ".")
    return float(s)


def parse_n4_cc_rotulo(rotulo: str) -> tuple[str, str] | None:
    m = _LEAF_CC.match(str(rotulo).strip())
    if not m:
        return None
    cod = m.group(1).rstrip(".")
    descr = _norm_desc(m.group(2))
    return cod, descr


def parse_n4_entrada(valor: str, mapa_cc: dict[str, str]) -> tuple[str, str]:
    """Aceita n4_CC ('COD DESC') ou só o código (n4_cod_centro_custo)."""
    texto = str(valor).strip()
    if not texto or texto.lower() == "nan":
        raise ValueError(f"Centro de custo vazio: {valor!r}")
    parsed = parse_n4_cc_rotulo(texto)
    if parsed is not None:
        return parsed
    cod = texto.rstrip(".")
    if re.fullmatch(r"\d+(?:\.\d+)*", cod):
        return cod, mapa_cc.get(cod, "")
    # Relatórios de combustível: "PLACA 1.2.2.5.1" — placa vira descrição do n4.
    m_placa_cod = _PLACA_COD_CC.match(texto)
    if m_placa_cod:
        placa, cod = m_placa_cod.group(1), m_placa_cod.group(2)
        sagi = mapa_cc.get(cod, "")
        if sagi and not _descr_sagi_placeholder(sagi):
            return cod, sagi
        return cod, placa
    m_cod_final = re.search(r"(\d+(?:\.\d+)+)\s*$", texto)
    if m_cod_final:
        cod = m_cod_final.group(1)
        return cod, mapa_cc.get(cod, "")
    raise ValueError(f"n4 inválido (esperado código ou 'COD DESC'): {valor!r}")


def tamanhos_prefixo_niveis(num_partes: int) -> tuple[int, int, int, int]:
    L = max(num_partes, 1)
    return (min(2, L), min(3, L), min(4, L), L)


def codigo_prefixo(partes: list[str], ate: int) -> str:
    return ".".join(partes[:ate])


def normalizar_codigo_cc(cod: str) -> str:
    return CODIGO_CC_CORRECAO_FOPA.get(cod, cod)


def descricao_no_nivel(
    cod_nivel: str,
    cod_folha: str,
    descr_folha: str,
    mapa: dict[str, str],
) -> str:
    sagi = mapa.get(cod_nivel, "")
    if sagi and not _descr_sagi_placeholder(sagi):
        return sagi
    if cod_nivel == cod_folha and descr_folha:
        return descr_folha
    if sagi:
        return sagi
    return ""


def segmento_para(n1_cod: str) -> str:
    return SEGMENTO_POR_N1.get(n1_cod, "")


def cc_col(cod: str, desc: str) -> str:
    desc = desc.strip()
    return f"{cod} {desc}".strip() if desc else cod


def filial_para_n2(n2_cod: str) -> str:
    return FILIAL_POR_N2_COD.get(n2_cod, "")


def montar_linha_fechamento(
    idx: int,
    rotulo_n4: str,
    valor_nf_bruto: float,
    mapa_cc: dict[str, str],
    folha: ParametrosFolha,
) -> dict[str, object]:
    cod_folha, descr_folha = parse_n4_entrada(rotulo_n4, mapa_cc)
    cod_folha = normalizar_codigo_cc(cod_folha)
    sagi_n4 = mapa_cc.get(cod_folha, "")
    if sagi_n4 and not _descr_sagi_placeholder(sagi_n4):
        descr_folha = sagi_n4
    elif not descr_folha and sagi_n4:
        descr_folha = sagi_n4
    partes = cod_folha.split(".")
    t1, t2, t3, t4 = tamanhos_prefixo_niveis(len(partes))

    c1, c2, c3, c4 = (
        codigo_prefixo(partes, t1),
        codigo_prefixo(partes, t2),
        codigo_prefixo(partes, t3),
        codigo_prefixo(partes, t4),
    )
    d1 = descricao_no_nivel(c1, cod_folha, descr_folha, mapa_cc)
    d2 = descricao_no_nivel(c2, cod_folha, descr_folha, mapa_cc)
    d3 = descricao_no_nivel(c3, cod_folha, descr_folha, mapa_cc)
    d4 = descricao_no_nivel(c4, cod_folha, descr_folha, mapa_cc)

    sagi_n1 = mapa_cc.get(c1, d1)
    n1_centro = N1_CENTRO_CUSTO_OVERRIDE.get(c1, sagi_n1 if sagi_n1 else d1)
    n1_cc = cc_col(c1, sagi_n1 if sagi_n1 else d1)

    valor = float(valor_nf_bruto) * folha.multiplicador_valor

    filial = FILIAL_POR_N4_COD.get(c4) or filial_para_n2(c2)
    if not filial:
        raise KeyError(
            f"filial não mapeada para n2_cod_centro_custo={c2!r} (n4_CC={rotulo_n4!r}). "
            "Atualize FILIAL_POR_N2_COD em base_r_para_fechamento_folha.py."
        )

    return {
        "id": idx,
        "Segmento": segmento_para(c1),
        "n1_cod_centro_custo": c1,
        "n1_centro_custo": n1_centro,
        "n1_CC": n1_cc,
        "n2_cod_centro_custo": c2,
        "n2_centro_custo": d2,
        "n2_CC": cc_col(c2, d2),
        "n3_cod_centro_custo": c3,
        "n3_centro_custo": d3,
        "n3_CC": cc_col(c3, d3),
        "n4_cod_centro_custo": c4,
        "n4_centro_custo": d4,
        "n4_CC": cc_col(c4, d4),
        "cod_conta": folha.cod_conta,
        "conta": folha.conta,
        "cod_conta-descr": folha.cod_conta_descr,
        "filial": filial,
        "titulo": folha.titulo,
        "valor_nf": valor,
        "valor_pago": valor,
        "valor_conta": valor,
        "observacao": folha.observacao,
        "data_nf": folha.data_nf,
        "data_pagamento": folha.data_pagamento,
        "cod_credor_forn_cli_func": pd.NA,
        "credor_forn_cli_func": folha.credor,
        "Origem": folha.origem,
        "Sistema": folha.sistema,
        "Dados auxiliares": folha.dados_auxiliares,
        "Valor Oficial": valor,
    }


def _colunas_layout(layout_path: Path) -> list[str]:
    return list(pd.read_excel(layout_path, sheet_name=0, nrows=0).columns)


def _valor_numerico(val) -> float:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return float("nan")
    if isinstance(val, (int, float)) and not pd.isna(val):
        return float(val)
    return parse_valor_br(val)


_MES_PT: dict[str, int] = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "março": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}


def competencia_da_aba(nome_aba: str) -> tuple[int, int] | None:
    """Ex.: 'Maio 2026' -> (2026, 5). Retorna None se o nome não tiver mês/ano reconhecíveis."""
    partes = re.split(r"\s+", str(nome_aba).strip())
    if len(partes) < 2:
        return None
    mes_txt = partes[0].lower()
    if mes_txt not in _MES_PT:
        return None
    try:
        ano = int(partes[1])
    except ValueError:
        return None
    return ano, _MES_PT[mes_txt]


def ultimo_dia_mes(ano: int, mes: int) -> date:
    return date(ano, mes, monthrange(ano, mes)[1])


def data_pagamento_padrao(data_nf: date) -> date:
    if data_nf.month == 12:
        return date(data_nf.year + 1, 1, 8)
    return date(data_nf.year, data_nf.month + 1, 8)


def titulo_competencia(prefixo: str, ano: int, mes: int) -> str:
    return f"{prefixo}_{mes:02d}_{ano}"


def _normalizar_colunas_entrada(df: pd.DataFrame) -> pd.DataFrame:
    df = df.loc[:, [c for c in df.columns if str(c).strip() and not str(c).startswith("Unnamed")]]
    col_cc = next(
        (
            c
            for c in df.columns
            if str(c).strip().lower() in {"n4_cc", "n4_cod_centro_custo"}
            or ("n4" in str(c).lower() and "cod" in str(c).lower() and "centro" in str(c).lower())
            or ("n4" in str(c).lower() and "cc" in str(c).lower())
        ),
        df.columns[0],
    )
    col_vl = next((c for c in df.columns if "valor" in str(c).lower()), df.columns[1])
    return df.rename(columns={col_cc: "n4_CC", col_vl: "valor_nf"})


def carregar_entrada(path: Path, sheet: str | int | None = None) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path, sheet_name=0 if sheet is None else sheet, dtype=object)
    else:
        df = pd.read_csv(path, sep=";", encoding="latin-1", dtype=str)
    return _normalizar_colunas_entrada(df)


def carregar_todas_abas(path: Path) -> list[tuple[str, pd.DataFrame, tuple[int, int] | None]]:
    xl = pd.ExcelFile(path)
    abas: list[tuple[str, pd.DataFrame, tuple[int, int] | None]] = []
    for nome in xl.sheet_names:
        df = _normalizar_colunas_entrada(pd.read_excel(path, sheet_name=nome, dtype=object))
        abas.append((nome, df, competencia_da_aba(nome)))
    abas.sort(
        key=lambda item: (
            item[2] if item[2] is not None else (9999, 99),
            item[0],
        )
    )
    return abas


def prefixo_titulo(titulo: str) -> str:
    if "_" in titulo:
        return titulo.split("_", 1)[0]
    return titulo


def observacao_competencia(
    data_nf: date,
    observacao_cli: str | None,
    cod_conta: str,
) -> str:
    if observacao_cli is not None:
        return observacao_cli.replace("{competencia}", data_nf.strftime("%m/%Y"))
    if cod_conta == CONTA_FOLHA_COD:
        return f"Processamento de Folha {data_nf.strftime('%d/%m/%Y')}"
    return f"Custo combustível {data_nf.strftime('%m/%Y')} por máquina"


def parametros_folha_competencia(
    args: argparse.Namespace,
    ano: int,
    mes: int,
    cod_conta_descr: str,
) -> ParametrosFolha:
    data_nf = ultimo_dia_mes(ano, mes)
    data_pagamento = (
        _parse_data(args.data_pagamento)
        if args.data_pagamento_fixa
        else data_pagamento_padrao(data_nf)
    )
    prefixo = args.titulo_prefix or prefixo_titulo(args.titulo)
    return ParametrosFolha(
        titulo=titulo_competencia(prefixo, ano, mes),
        observacao=observacao_competencia(data_nf, args.observacao, args.cod_conta),
        credor=args.credor,
        origem=args.origem,
        sistema=args.sistema,
        dados_auxiliares=args.dados_auxiliares,
        data_nf=data_nf,
        data_pagamento=data_pagamento,
        multiplicador_valor=args.multiplicador_valor,
        cod_conta=args.cod_conta,
        conta=args.conta,
        cod_conta_descr=cod_conta_descr,
    )


def _parse_data(s: str) -> date:
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Data inválida: {s!r}")


DEFAULT_INPUT = REFS / "FOPA" / "base_R.csv"
DEFAULT_OUTPUT = REFS / "FOPA" / "base_R_fechamento_folha_pagamento.xlsx"


def main() -> None:
    ap = argparse.ArgumentParser(
        description="CSV/Excel (n4_CC ou n4_cod_centro_custo + valor_nf) -> Excel fechamento."
    )
    ap.add_argument(
        "entrada",
        nargs="?",
        type=Path,
        default=None,
        metavar="ENTRADA",
        help="Arquivo de entrada (.csv ou .xlsx). Também pode usar --input.",
    )
    ap.add_argument(
        "--input",
        "-i",
        type=Path,
        default=None,
        dest="input_flag",
        help="Arquivo de entrada (.csv ou .xlsx). Sobrescreve o argumento posicional.",
    )
    ap.add_argument("--cc-sagi", type=Path, default=REFS / "SAGI" / "sagi_rel_centro_custo.csv")
    ap.add_argument(
        "--layout",
        type=Path,
        default=None,
        help="Excel só para ordem das colunas. Padrão: base_R_fechamento_folha_pagamento_correto.xlsx se existir; senão FECHAMENTO_ODBC.",
    )
    ap.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Arquivo Excel gerado. Padrão: <entrada>_fechamento.xlsx (ou base_R_fechamento_folha_pagamento.xlsx para a folha).",
    )
    ap.add_argument(
        "--sheet",
        default=None,
        help="Aba do Excel de entrada (nome ou índice). Padrão: primeira aba.",
    )
    ap.add_argument(
        "--all-sheets",
        action="store_true",
        help="Lê todas as abas do Excel e consolida numa única saída. "
        "Competência (data_nf, titulo, observação) vem do nome da aba (ex.: 'Maio 2026').",
    )
    ap.add_argument("--sheet-out", default="Fechamento")
    ap.add_argument("--titulo", default="FOPA_04_2026")
    ap.add_argument(
        "--titulo-prefix",
        default=None,
        help="Com --all-sheets: prefixo do titulo por aba (ex.: COMB -> COMB_05_2026). "
        "Padrão: parte antes do '_' em --titulo.",
    )
    ap.add_argument(
        "--observacao",
        default=None,
        help="Padrão: 'Processamento de Folha' + data NF (dd/mm/aaaa), como no arquivo corrigido.",
    )
    ap.add_argument("--credor", default="PROCESSAMENTO DE FOLHA")
    ap.add_argument("--origem", default="Saída (Aplicações)")
    ap.add_argument("--sistema", default="FOPA")
    ap.add_argument("--dados-auxiliares", default="Processamento de folha")
    ap.add_argument("--data-nf", default="2026-04-30")
    ap.add_argument("--data-pagamento", default="2026-05-08")
    ap.add_argument(
        "--data-pagamento-fixa",
        action="store_true",
        help="Com --all-sheets: usa --data-pagamento para todas as linhas em vez do dia 8 do mês seguinte.",
    )
    ap.add_argument(
        "--multiplicador-valor",
        type=float,
        default=-1.0,
        help="Por padrão -1 (valores de saída / despesa negativos, como no arquivo corrigido).",
    )
    ap.add_argument("--cod-conta", default=CONTA_FOLHA_COD)
    ap.add_argument("--conta", default=CONTA_FOLHA_NOME)
    ap.add_argument(
        "--cod-conta-descr",
        default=None,
        help="Padrão: '<cod-conta> <conta>'.",
    )
    args = ap.parse_args()

    input_path = args.input_flag or args.entrada or DEFAULT_INPUT
    output_path = (
        args.output
        if args.output is not None
        else DEFAULT_OUTPUT
        if input_path.resolve() == DEFAULT_INPUT.resolve()
        else input_path.with_name(f"{input_path.stem}_fechamento.xlsx")
    )

    layout = args.layout
    if layout is None:
        layout = LAYOUT_CORRETO if LAYOUT_CORRETO.exists() else TEMPLATE_FECHAMENTO_ODBC
    if not layout.exists():
        raise FileNotFoundError(f"Arquivo de layout não encontrado: {layout.resolve()}")

    if not input_path.exists():
        raise FileNotFoundError(input_path.resolve())
    if not args.cc_sagi.exists():
        raise FileNotFoundError(args.cc_sagi.resolve())

    cod_conta_descr = (
        args.cod_conta_descr
        if args.cod_conta_descr is not None
        else f"{args.cod_conta} {args.conta}".strip()
    )

    mapa_cc = carregar_mapa_cc_sagi(args.cc_sagi)

    linhas: list[dict[str, object]] = []
    abas_lidas = 0

    if args.all_sheets:
        if input_path.suffix.lower() not in {".xlsx", ".xls"}:
            raise ValueError("--all-sheets só se aplica a arquivos Excel (.xlsx/.xls).")
        if args.sheet is not None:
            raise ValueError("Use --sheet ou --all-sheets, não os dois.")
        for nome_aba, df_r, competencia in carregar_todas_abas(input_path):
            if competencia is None:
                raise ValueError(
                    f"Aba {nome_aba!r} sem competência reconhecível. "
                    "Esperado nome como 'Maio 2026'."
                )
            ano, mes = competencia
            folha = parametros_folha_competencia(args, ano, mes, cod_conta_descr)
            abas_lidas += 1
            for _, row in df_r.iterrows():
                rot = str(row["n4_CC"]).strip()
                if not rot or rot.lower() == "nan":
                    continue
                vl = _valor_numerico(row["valor_nf"])
                linhas.append(montar_linha_fechamento(len(linhas) + 1, rot, vl, mapa_cc, folha))
    else:
        data_nf = _parse_data(args.data_nf)
        data_pagamento = _parse_data(args.data_pagamento)
        observacao = observacao_competencia(data_nf, args.observacao, args.cod_conta)
        folha = ParametrosFolha(
            titulo=args.titulo,
            observacao=observacao,
            credor=args.credor,
            origem=args.origem,
            sistema=args.sistema,
            dados_auxiliares=args.dados_auxiliares,
            data_nf=data_nf,
            data_pagamento=data_pagamento,
            multiplicador_valor=args.multiplicador_valor,
            cod_conta=args.cod_conta,
            conta=args.conta,
            cod_conta_descr=cod_conta_descr,
        )
        sheet_in: str | int | None = args.sheet
        if sheet_in is not None and str(sheet_in).isdigit():
            sheet_in = int(sheet_in)
        df_r = carregar_entrada(input_path, sheet=sheet_in)
        abas_lidas = 1
        for _, row in df_r.iterrows():
            rot = str(row["n4_CC"]).strip()
            if not rot or rot.lower() == "nan":
                continue
            vl = _valor_numerico(row["valor_nf"])
            linhas.append(montar_linha_fechamento(len(linhas) + 1, rot, vl, mapa_cc, folha))

    if not linhas:
        raise ValueError("Nenhuma linha gerada. Verifique o arquivo de entrada.")

    out_df = pd.DataFrame(linhas)
    cols = _colunas_layout(layout)
    for c in cols:
        if c not in out_df.columns:
            out_df[c] = pd.NA
    out_df = out_df[cols]

    for col in _COLS_VALOR_NUMERICO:
        if col in out_df.columns:
            out_df[col] = pd.to_numeric(out_df[col], errors="coerce")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    gravar_fechamento_excel(out_df, output_path, sheet_name=args.sheet_out)
    msg_abas = f", {abas_lidas} abas" if args.all_sheets else ""
    print(
        f"Gravado: {output_path.resolve()} ({len(out_df)} linhas{msg_abas}). "
        f"Layout: {layout.name}"
    )


if __name__ == "__main__":
    main()
