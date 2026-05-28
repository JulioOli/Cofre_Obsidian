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

LAYOUT_CORRETO = REFS / "base_R_fechamento_folha_pagamento_correto.xlsx"
TEMPLATE_FECHAMENTO_ODBC = REFS / "FECHAMENTO_ODBC_2026_04.xlsx"


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
    parsed = parse_n4_cc_rotulo(rotulo_n4)
    if parsed is None:
        raise ValueError(f"n4_CC inválido (esperado 'COD DESC'): {rotulo_n4!r}")
    cod_folha, descr_folha = parsed
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
        "cod_conta": CONTA_FOLHA_COD,
        "conta": CONTA_FOLHA_NOME,
        "cod_conta-descr": CONTA_FOLHA_DESCR,
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


def _parse_data(s: str) -> date:
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Data inválida: {s!r}")


def main() -> None:
    ap = argparse.ArgumentParser(description="base_R.csv -> Excel folha pagamento (layout corrigido).")
    ap.add_argument("--input", type=Path, default=REFS / "base_R.csv")
    ap.add_argument("--cc-sagi", type=Path, default=REFS / "sagi_rel_centro_custo.csv")
    ap.add_argument(
        "--layout",
        type=Path,
        default=None,
        help="Excel só para ordem das colunas. Padrão: base_R_fechamento_folha_pagamento_correto.xlsx se existir; senão FECHAMENTO_ODBC.",
    )
    ap.add_argument("--output", type=Path, default=REFS / "base_R_fechamento_folha_pagamento.xlsx")
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

    data_nf = _parse_data(args.data_nf)
    data_pagamento = _parse_data(args.data_pagamento)
    observacao = (
        args.observacao
        if args.observacao is not None
        else f"Processamento de Folha {data_nf.strftime('%d/%m/%Y')}"
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
    )

    mapa_cc = carregar_mapa_cc_sagi(args.cc_sagi)

    df_r = pd.read_csv(args.input, sep=";", encoding="latin-1", dtype=str)
    df_r = df_r.loc[:, [c for c in df_r.columns if str(c).strip() and not str(c).startswith("Unnamed")]]
    if list(df_r.columns[:2]) != ["n4_CC", "valor_nf"]:
        col_cc = next((c for c in df_r.columns if "n4" in c.lower() and "cc" in c.lower()), df_r.columns[0])
        col_vl = next((c for c in df_r.columns if "valor" in c.lower()), df_r.columns[1])
        df_r = df_r.rename(columns={col_cc: "n4_CC", col_vl: "valor_nf"})

    linhas: list[dict[str, object]] = []
    for _, row in df_r.iterrows():
        rot = str(row["n4_CC"]).strip()
        if not rot or rot.lower() == "nan":
            continue
        vl = parse_valor_br(row["valor_nf"])
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

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(args.output, engine="openpyxl") as w:
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

    print(f"Gravado: {args.output.resolve()} ({len(out_df)} linhas). Layout: {layout.name}")


if __name__ == "__main__":
    main()
