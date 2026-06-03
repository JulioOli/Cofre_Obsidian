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
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
REFS = ROOT / "02-Referencias"

_CC_LINE = re.compile(r"^\s*(\d+(?:\.\d+)*)\s*;")
_LEAF_CC = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$")

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
_FMT_MOEDA_EXCEL = "#,##0.00"

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
    if not re.fullmatch(r"\d+(?:\.\d+)*", cod):
        raise ValueError(f"n4 inválido (esperado código ou 'COD DESC'): {valor!r}")
    return cod, mapa_cc.get(cod, "")


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
    if sagi:
        return sagi
    if cod_nivel == cod_folha:
        return descr_folha
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
    descr_folha = mapa_cc.get(cod_folha) or descr_folha
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


def carregar_entrada(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path, sheet_name=0, dtype=object)
    else:
        df = pd.read_csv(path, sep=";", encoding="latin-1", dtype=str)
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
    ap.add_argument("--sheet-out", default="Fechamento")
    ap.add_argument("--titulo", default="FOPA_04_2026")
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

    data_nf = _parse_data(args.data_nf)
    data_pagamento = _parse_data(args.data_pagamento)
    observacao = (
        args.observacao
        if args.observacao is not None
        else f"Processamento de Folha {data_nf.strftime('%d/%m/%Y')}"
    )

    cod_conta_descr = (
        args.cod_conta_descr
        if args.cod_conta_descr is not None
        else f"{args.cod_conta} {args.conta}".strip()
    )

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

    mapa_cc = carregar_mapa_cc_sagi(args.cc_sagi)

    df_r = carregar_entrada(input_path)

    linhas: list[dict[str, object]] = []
    for _, row in df_r.iterrows():
        rot = str(row["n4_CC"]).strip()
        if not rot or rot.lower() == "nan":
            continue
        vl = _valor_numerico(row["valor_nf"])
        linhas.append(montar_linha_fechamento(len(linhas) + 1, rot, vl, mapa_cc, folha))

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
    with pd.ExcelWriter(output_path, engine="openpyxl") as w:
        out_df.to_excel(w, sheet_name=args.sheet_out, index=False)
        ws = w.sheets[args.sheet_out]
        header_to_col = {
            ws.cell(row=1, column=j).value: j
            for j in range(1, ws.max_column + 1)
            if ws.cell(row=1, column=j).value is not None
        }
        for nome in _COLS_VALOR_NUMERICO:
            j = header_to_col.get(nome)
            if j is None:
                continue
            for r in range(2, ws.max_row + 1):
                cell = ws.cell(row=r, column=j)
                if cell.value is None or cell.value == "":
                    continue
                cell.number_format = _FMT_MOEDA_EXCEL

    print(f"Gravado: {output_path.resolve()} ({len(out_df)} linhas). Layout: {layout.name}")


if __name__ == "__main__":
    main()
