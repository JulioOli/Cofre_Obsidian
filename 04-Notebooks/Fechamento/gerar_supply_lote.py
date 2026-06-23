"""
Gera Relatorio Contas a Pagar Normalizado + BRACOFER_fechamento por mes
a partir de um arquivo consolidado Supply (Contas a Pagar).

Reutiliza a logica do notebook normalizar_supply.ipynb.
Filtro de periodo: coluna pagamento (data de pagamento).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl.styles import Font

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = Path(__file__).resolve().parent / "normalizar_supply.ipynb"
REFS = ROOT / "02-Referencias"
SUPPLY = REFS / "Supply_bracofer"

sys.path.insert(0, str((Path(__file__).resolve().parent.parent / "Utitlities").resolve()))
from fechamento_excel import gravar_fechamento_excel, parse_data_fechamento  # noqa: E402

MESES_PASTA = {
    "01": "Janeiro",
    "02": "Fevereiro",
    "03": "Março",
    "04": "Abril",
    "05": "Maio",
    "06": "Junho",
    "07": "Julho",
    "08": "Agosto",
    "09": "Setembro",
    "10": "Outubro",
    "11": "Novembro",
    "12": "Dezembro",
}


def _code_cells(nb: dict) -> list[dict]:
    return [c for c in nb["cells"] if c["cell_type"] == "code"]


def _exec_source(src: str, ns: dict) -> None:
    exec(compile(src, str(NOTEBOOK), "exec"), ns)


def _load_notebook_namespace() -> dict:
    """Carrega funcoes e mapas das celulas do notebook (sem executar parse/saida)."""
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = _code_cells(nb)

    ns: dict = {
        "Path": Path,
        "pd": pd,
        "datetime": datetime,
        "re": re,
        "Font": Font,
        "gravar_fechamento_excel": gravar_fechamento_excel,
        "parse_data_fechamento": parse_data_fechamento,
        "REFS_DIR": REFS,
        "SUPPLY_DIR": SUPPLY,
    }

    # Celula 0: parse_relatorio_contas_pagar (sem chamar no ARQUIVO_ENTRADA)
    src_parse = "".join(cells[1]["source"])
    src_parse = re.sub(
        r"\ndf_norm\s*=\s*parse_relatorio_contas_pagar\(ARQUIVO_ENTRADA\)[\s\S]*$",
        "",
        src_parse,
        count=1,
    )
    _exec_source(src_parse, ns)

    # Celulas fechamento: apenas definicoes (sem carregar fonte / converter)
    for idx in (4, 5, 6):
        src = "".join(cells[idx]["source"])
        if idx == 4:
            src = re.sub(
                r"\nfonte_df,\s*fonte_path\s*=\s*carregar_fonte_segunda_normalizacao\(\)[\s\S]*$",
                "",
                src,
                count=1,
            )
        if idx == 6:
            src = re.sub(
                r"\n# Recarrega a fonte[\s\S]*$",
                "",
                src,
                count=1,
            )
        _exec_source(src, ns)

    if "modelo_cols" not in ns:
        fech_dir = REFS / "Fechamento"
        candidatos = sorted(fech_dir.glob("FECHAMENTO_ODBC_*.xlsx"))
        if not candidatos:
            candidatos = sorted(REFS.glob("FECHAMENTO_ODBC_*.xlsx"))
        if not candidatos:
            raise FileNotFoundError("Nenhum FECHAMENTO_ODBC_*.xlsx encontrado.")
        ns["modelo_cols"] = pd.read_excel(candidatos[-1], nrows=0).columns.tolist()

    return ns


def _norm_cod_supply(cod) -> str:
    """Alinha codigo Supply ao formato do MAPA_PC (ex.: 02010101 -> 2010101)."""
    if cod is None or (isinstance(cod, float) and pd.isna(cod)):
        return ""
    s = str(cod).strip()
    if not s or s.lower() == "nan":
        return ""
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    s = s.lstrip("0") or "0"
    return s


def _mapear_pc(ns: dict, cod_supply, contexto: str) -> dict | None:
    chave = _norm_cod_supply(cod_supply)
    if not chave:
        return None
    return ns["mapear_plano_contas_bracofer"](chave, contexto)


def _parse_data_pagamento(val) -> tuple[int | None, int | None]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None, None
    s = str(val).strip()
    if not s or s.lower() == "nan":
        return None, None
    dt = parse_data_fechamento(s)
    if pd.isna(dt):
        return None, None
    return int(dt.month), int(dt.year)


def _filtrar_mes(df: pd.DataFrame, mes: str, ano: str) -> pd.DataFrame:
    mes_i, ano_i = int(mes), int(ano)
    mask = []
    for pag in df["pagamento"]:
        m, a = _parse_data_pagamento(pag)
        mask.append(m == mes_i and a == ano_i)
    out = df.loc[mask].copy().reset_index(drop=True)
    return out


def _salvar_normalizado(df: pd.DataFrame, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    arquivo = destino
    try:
        with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
            sheet_name = "contas_pagar_normalizado"
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            ws = writer.book[sheet_name]
            bold = Font(bold=True)
            for cell in ws[1]:
                cell.font = bold
    except PermissionError:
        arquivo = destino.with_name(destino.stem + "_novo" + destino.suffix)
        with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
            sheet_name = "contas_pagar_normalizado"
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            ws = writer.book[sheet_name]
            bold = Font(bold=True)
            for cell in ws[1]:
                cell.font = bold
    return arquivo


def _gerar_fechamento(ns: dict, df_norm: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    fonte_df = df_norm.copy()
    fonte_df.columns = [str(c).strip().lower().replace(" ", "_") for c in fonte_df.columns]
    modelo_cols = ns["modelo_cols"]
    pcs_nao_mapeados: list = []
    linhas_saida = []

    for i, row in fonte_df.iterrows():
        row = {k: row[k] for k in fonte_df.columns}
        filial = ns["_pick"](row, "filial", "empresa", default="G3S")
        titulo = ns["_pick"](row, "titulo", "numero_documento", "numero", default=f"DOC-{i+1}")

        titulo_txt = str(titulo).strip().lower()
        if "desenvolvido por softland" in titulo_txt or "softland sistemas" in titulo_txt:
            continue

        valor_nf = ns["_to_float"](ns["_pick"](row, "valor_nf", "valor_documento", "valor", default=pd.NA))
        valor_pago = ns["_to_float"](ns["_pick"](row, "valor_pago", "liquido", "valor", default=valor_nf))

        centro_desc = ns["_pick"](
            row, "centro_custos_descricao", "centro_origem", "centro_custo", "departamento", default=""
        )
        cod_cc = ns["_definir_cod_centro"](centro_desc)
        n1, n2, n3, n4 = ns["_hierarquia_cc"](cod_cc)

        nova = {c: pd.NA for c in modelo_cols}
        nova["id"] = i + 1
        nova["filial"] = filial
        nova["titulo"] = str(titulo)
        nova["valor_nf"] = valor_nf
        nova["valor_pago"] = -abs(valor_pago) if valor_pago is not None and not pd.isna(valor_pago) else pd.NA
        vc = valor_nf if pd.isna(valor_pago) else valor_pago
        nova["valor_conta"] = -abs(vc) if vc is not None and not pd.isna(vc) else pd.NA

        nova["n1_cod_centro_custo"] = n1
        nova["n2_cod_centro_custo"] = n2
        nova["n3_cod_centro_custo"] = n3
        nova["n4_cod_centro_custo"] = n4

        desc_h = ns["_descricao_hierarquia"](cod_cc)
        nova["Segmento"] = desc_h["segmento"]
        nova["n1_centro_custo"] = desc_h["n1_desc"]
        nova["n2_centro_custo"] = desc_h["n2_desc"]
        nova["n3_centro_custo"] = desc_h["n3_desc"]
        nova["n4_centro_custo"] = desc_h["n4_desc"]
        nova["n1_CC"] = f"{n1} {desc_h['n1_desc']}"
        nova["n2_CC"] = f"{n2} {desc_h['n2_desc']}"
        nova["n3_CC"] = f"{n3} {desc_h['n3_desc']}"
        nova["n4_CC"] = f"{n4} {desc_h['n4_desc']}"

        nova["data_nf"] = parse_data_fechamento(ns["_pick"](row, "data_nf", "emissao", "emissão", default=""))
        nova["data_pagamento"] = parse_data_fechamento(
            ns["_pick"](row, "data_pagamento", "pagamento", default="")
        )
        nova["credor_forn_cli_func"] = ns["_pick"](row, "credor_forn_cli_func", "fornecedor", "nome", default="")
        nova["observacao"] = ns["_pick"](row, "observacao", default="")

        cod_supply_raw = ns["_pick"](row, "classificacao_financeira_codigo", "cod_conta", default="")
        ctx_pc = " ".join(
            str(ns["_pick"](row, k, default="")).strip()
            for k in (
                "classificacao_financeira_descricao",
                "fornecedor",
                "descricao_documento",
                "observacao",
            )
        )
        pc = _mapear_pc(ns, cod_supply_raw, ctx_pc)
        if pc:
            nova["cod_conta"] = pc["cod"]
            nova["conta"] = pc["desc"]
        else:
            cod_norm = _norm_cod_supply(cod_supply_raw)
            nova["cod_conta"] = cod_norm or cod_supply_raw
            nova["conta"] = ns["_pick"](row, "classificacao_financeira_descricao", "conta", default="")
            if cod_norm:
                pcs_nao_mapeados.append(
                    {
                        "linha": i + 1,
                        "cod_supply": cod_norm,
                        "desc_supply": ns["_pick"](
                            row, "classificacao_financeira_descricao", "conta", default=""
                        ),
                        "fornecedor": ns["_pick"](row, "fornecedor", "credor_forn_cli_func", default=""),
                    }
                )
        if str(nova["cod_conta"]).strip() and str(nova["conta"]).strip():
            nova["cod_conta-descr"] = f"{nova['cod_conta']} {nova['conta']}"

        linhas_saida.append(nova)

    return pd.DataFrame(linhas_saida, columns=modelo_cols), pcs_nao_mapeados


def gerar_meses(
    arquivo_entrada: Path,
    meses: list[tuple[str, str]],
    *,
    sobrescrever: bool = True,
) -> list[dict]:
    ns = _load_notebook_namespace()
    parse = ns["parse_relatorio_contas_pagar"]

    print(f"Entrada consolidada: {arquivo_entrada.resolve()}")
    df_total = parse(arquivo_entrada)
    print(f"Total parseado: {len(df_total)} linhas | layout: {ns.get('_LAYOUT_SUPPLY_DETECTADO', '?')}")

    sem_pag = int(df_total["pagamento"].apply(lambda v: _parse_data_pagamento(v)[0] is None).sum())
    if sem_pag:
        print(f"[AVISO] {sem_pag} linha(s) sem data de pagamento parseavel (nao entram em nenhum mes).")

    resultados: list[dict] = []

    for mes, ano in meses:
        sufixo = f"{mes}-{ano}"
        pasta = MESES_PASTA.get(mes, mes)
        out_dir = SUPPLY / pasta
        out_dir.mkdir(parents=True, exist_ok=True)

        df_mes = _filtrar_mes(df_total, mes, ano)
        arq_norm = out_dir / f"Relatorio Contas a Pagar {sufixo} - Normalizado.xlsx"
        arq_fech = out_dir / f"BRACOFER_fechamento_{sufixo}.xlsx"

        if not sobrescrever and arq_norm.exists() and arq_fech.exists():
            print(f"[PULADO] {mes}/{ano} — arquivos ja existem.")
            continue

        if df_mes.empty:
            print(f"[VAZIO] {mes}/{ano} — nenhuma linha com pagamento no mes.")
            resultados.append({"mes": f"{mes}/{ano}", "linhas": 0, "normalizado": None, "fechamento": None})
            continue

        arq_norm = _salvar_normalizado(df_mes, arq_norm)
        fechamento_df, pendentes = _gerar_fechamento(ns, df_mes)
        gravar_fechamento_excel(fechamento_df, arq_fech, sheet_name="fechamento_normalizado")

        soma = pd.to_numeric(df_mes["liquido"], errors="coerce").sum()
        status = "OK"
        if pendentes:
            status = f"OK ({len(pendentes)} PC nao mapeado(s))"
        print(
            f"[{status}] {mes}/{ano} | {len(df_mes)} linhas | liquido R$ {soma:,.2f}\n"
            f"  -> {arq_norm.name}\n"
            f"  -> {arq_fech.name}"
        )
        resultados.append(
            {
                "mes": f"{mes}/{ano}",
                "linhas": len(df_mes),
                "liquido": soma,
                "normalizado": str(arq_norm),
                "fechamento": str(arq_fech),
                "pc_pendentes": len(pendentes),
            }
        )

    return resultados


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Gera fechamentos Supply Bracofer por mes.")
    parser.add_argument(
        "--entrada",
        type=Path,
        default=SUPPLY
        / "_referencia"
        / "Relatório Contas a Pagar de 01-01-2026 até 23-06-2026.xlsx",
    )
    parser.add_argument(
        "--de",
        default="01/2026",
        help="Mes inicial MM/AAAA",
    )
    parser.add_argument(
        "--ate",
        default="06/2026",
        help="Mes final MM/AAAA",
    )
    args = parser.parse_args()

    if not args.entrada.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {args.entrada}")

    m_ini, a_ini = args.de.split("/")
    m_fim, a_fim = args.ate.split("/")
    meses: list[tuple[str, str]] = []
    y, m = int(a_ini), int(m_ini)
    y_end, m_end = int(a_fim), int(m_fim)
    while (y, m) <= (y_end, m_end):
        meses.append((f"{m:02d}", str(y)))
        m += 1
        if m > 12:
            m = 1
            y += 1

    print(f"Gerando {len(meses)} mes(es): {args.de} a {args.ate}\n")
    gerar_meses(args.entrada, meses)


if __name__ == "__main__":
    main()
