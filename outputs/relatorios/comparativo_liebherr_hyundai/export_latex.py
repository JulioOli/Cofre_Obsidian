"""Gera dados.tex, insights.tex, kpi.tex e conclusao.tex a partir do Excel de resumo."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = Path(__file__).resolve().parent
XLSX = ROOT / "outputs" / "tabelas" / "comparativo_liebherr_hyundai.xlsx"

REPORT_AUTHOR = "Julio"
REPORT_AREA = "Qualidade - Pilares"
REPORT_CREDIT = f"Análises feitas por {REPORT_AUTHOR}; {REPORT_AREA}"


def _latex_escape_plain(text: str) -> str:
    text = str(text)
    # setas em modo matemático — proteger antes de escapar $
    text = text.replace("→", "\x00ARROW\x00")
    # R$ fora de modo matemático (insights do notebook)
    text = text.replace("R$", r"R\$")
    mapping = {
        "&": r"\&",
        "%": r"\%",
        "#": r"\#",
        "_": r"\_",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for char, repl in mapping.items():
        text = text.replace(char, repl)
    return text.replace("\x00ARROW\x00", r"$\rightarrow$")


def latex_escape(text: str) -> str:
    bold_parts: list[str] = []

    def stash_bold(match: re.Match[str]) -> str:
        bold_parts.append(match.group(1))
        return f"\x00BOLD{len(bold_parts) - 1}\x00"

    text = re.sub(r"\*\*(.+?)\*\*", stash_bold, str(text))
    text = _latex_escape_plain(text)
    for i, inner in enumerate(bold_parts):
        text = text.replace(f"\x00BOLD{i}\x00", f"\\textbf{{{_latex_escape_plain(inner)}}}")
    return text


def fmt_brl(val: float) -> str:
    if pd.isna(val):
        return "---"
    return r"R\$\," + f"{abs(val):,.0f}".replace(",", ".")


def fmt_num(val: float, dec: int = 0) -> str:
    if pd.isna(val):
        return "---"
    if dec == 0:
        return f"{val:,.0f}".replace(",", ".")
    return f"{val:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def inferir_periodo(xlsx: Path) -> str:
    if not xlsx.exists():
        return "2025--2026"
    por_mes = pd.read_excel(xlsx, sheet_name="por_mes")
    meses = sorted(por_mes["mes_nf"].dropna().astype(str).unique())
    if not meses:
        return "2025--2026"
    ini = meses[0].replace("-", "/")
    fim = meses[-1].replace("-", "/")
    return f"{ini} a {fim}"


def escrever_dados_tex(periodo: str) -> None:
    hoje = date.today().strftime("%d/%m/%Y")
    (OUT_DIR / "dados.tex").write_text(
        f"\\newcommand{{\\reportdate}}{{{hoje}}}\n"
        f"\\newcommand{{\\daterange}}{{{latex_escape(periodo)}}}\n"
        f"\\newcommand{{\\reportauthor}}{{{latex_escape(REPORT_AUTHOR)}}}\n"
        f"\\newcommand{{\\reportarea}}{{{latex_escape(REPORT_AREA)}}}\n"
        f"\\newcommand{{\\reportcredit}}{{{latex_escape(REPORT_CREDIT)}}}\n",
        encoding="utf-8",
    )


def escrever_insights_tex(insights: list[str]) -> None:
    linhas = ["\\begin{itemize}[leftmargin=*]", "  \\setlength{\\itemsep}{0.35em}"]
    for txt in insights:
        linhas.append(f"  \\item {latex_escape(txt)}")
    linhas.append("\\end{itemize}")
    (OUT_DIR / "insights.tex").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def escrever_kpi_tex(kpi: pd.DataFrame) -> None:
    # kpi: linhas = indicador, colunas = marca
    marcas = [c for c in kpi.columns]
    rotulos = {
        "lançamentos (marca)": "Lançamentos (marca)",
        "lançamentos (parque)": "Lançamentos (parque)",
        "máquinas no parque": "Máquinas no parque",
        "máquinas com lanç.": "Máquinas com lançamento",
        "soma valor_conta (líquido)": "Resultado líquido (valor conta)",
        "volume gasto (|valor|)": "Volume de gasto (|valor|)",
        "volume parque (|valor|)": "Volume parque (|valor|)",
        "despesas (<0)": "Despesas",
        "ajustes/créditos (>0)": "Ajustes / créditos",
        "ticket médio (|valor|)": "Ticket médio",
        "custo médio/máquina (parque)": "Custo médio/máquina (parque)",
        "custo/máquina parque (vol÷parque)": "Custo médio/máquina (parque)",
    }
    linhas = [
        "\\begin{table}[H]",
        "\\centering",
        "\\small",
        f"\\begin{{tabular}}{{l{'r' * len(marcas)}}}",
        "\\toprule",
        "Indicador & " + " & ".join(marcas) + r" \\",
        "\\midrule",
    ]
    for idx, row in kpi.iterrows():
        nome = rotulos.get(str(idx), str(idx))
        vals = []
        for m in marcas:
            v = row[m]
            if any(
                k in str(idx)
                for k in ("volume", "despesa", "líquido", "ticket", "custo", "ajuste")
            ):
                vals.append(fmt_brl(v) if abs(v) > 100 else fmt_num(v, 0))
            elif "lanç" in str(idx) and "máquina" not in str(idx):
                vals.append(fmt_num(v, 0))
            else:
                vals.append(fmt_num(v, 1) if isinstance(v, float) and v != int(v) else fmt_num(v, 0))
        linhas.append(f"{latex_escape(nome)} & " + " & ".join(vals) + r" \\")
    linhas.extend(["\\bottomrule", "\\end{tabular}", "\\caption{Indicadores comparativos por marca.}", "\\end{table}"])
    (OUT_DIR / "kpi.tex").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def _meses_colunas(df: pd.DataFrame) -> list[str]:
    return sorted(
        c for c in df.columns
        if re.fullmatch(r"\d{4}-\d{2}", str(c))
    )


def _rotulo_mes_curto(mes: str) -> str:
    ano, mm = str(mes).split("-")
    return f"{mm}/{ano[2:]}"


def fmt_brl_curto(val: float) -> str:
    if pd.isna(val) or val == 0:
        return "---"
    prefix = r"R\$\,"
    if abs(val) >= 1000:
        num = f"{abs(val) / 1000:,.1f}k"
        return prefix + num.replace(",", "X").replace(".", ",").replace("X", ".")
    return prefix + f"{abs(val):,.0f}".replace(",", ".")


def _col_spec_gasto_mensal(n_meses: int) -> str:
    """Colunas: máquina, marca, local (quebra linha), meses, resumo."""
    return f"@{{}}ll>{{\\raggedright\\arraybackslash}}p{{2.2cm}}{'r' * (n_meses + 3)}@{{}}"


def _linhas_dados_gasto_mensal(df: pd.DataFrame, cols_ano: list[str]) -> list[str]:
    linhas: list[str] = []
    for _, row in df.iterrows():
        vals_mes = [fmt_brl_curto(row[m]) for m in cols_ano]
        linhas.append(
            f"{latex_escape(row['maq_id'])} & "
            f"{latex_escape(row['MARCA'])} & "
            f"{latex_escape(row.get('local_operacao', ''))} & "
            + " & ".join(vals_mes)
            + f" & {fmt_brl_curto(row.get('media_mensal', 0))}"
            + f" & {fmt_brl_curto(row.get('total_periodo', 0))}"
            + f" & {fmt_num(row.get('meses_com_gasto', 0), 0)}" + r" \\"
        )
    return linhas


def escrever_gasto_mensal_maquinas_tex(xlsx: Path) -> None:
    df = pd.read_excel(xlsx, sheet_name="gasto_maquina_mes_wide")
    meses = _meses_colunas(df)
    if not meses:
        (OUT_DIR / "gasto_mensal_maquinas.tex").write_text(
            "% Aba gasto\\_maquina\\_mes\\_wide ausente ou sem colunas de mês.\n",
            encoding="utf-8",
        )
        return

    anos = sorted({m[:4] for m in meses})
    linhas = [
        "Cada célula de mês traz o gasto total da máquina naquele período (|valor\\_conta|). "
        "A coluna \\textbf{Média/mês} considera somente meses com lançamento.",
        "",
    ]
    # Tabelas largas (ano completo) em landscape; períodos curtos cabem em retrato.
    limiar_landscape = 7

    for ano in anos:
        cols_ano = [m for m in meses if m.startswith(ano)]
        n_meses = len(cols_ano)
        n_cols = 3 + n_meses + 3
        col_spec = _col_spec_gasto_mensal(n_meses)
        header = (
            "Máquina & Marca & Local & "
            + " & ".join(_rotulo_mes_curto(m) for m in cols_ano)
            + r" & Média/mês & Total & Meses \\"
        )
        titulo = f"Gasto mensal por máquina — {ano}"
        dados = _linhas_dados_gasto_mensal(df, cols_ano)

        if n_meses >= limiar_landscape:
            # Título dentro do landscape (evita página só com subtítulo).
            linhas.extend([
                "\\begin{landscape}",
                "\\footnotesize",
                "\\setlength{\\tabcolsep}{2.5pt}",
                "\\renewcommand{\\arraystretch}{0.92}",
                f"\\begin{{longtable}}{{{col_spec}}}",
                f"\\multicolumn{{{n_cols}}}{{@{{}}l}}{{\\textbf{{{latex_escape(titulo)}}}}} \\\\[0.2em]",
                "\\toprule",
                header,
                "\\midrule",
                "\\endhead",
                "\\midrule",
                f"\\multicolumn{{{n_cols}}}{{r}}{{\\textit{{Continua na próxima página}}}} \\\\",
                "\\endfoot",
                "\\bottomrule",
                "\\endlastfoot",
                *dados,
                "\\end{longtable}",
                "\\end{landscape}",
                "",
            ])
        else:
            linhas.extend([
                "\\begin{table}[H]",
                "\\centering",
                "\\footnotesize",
                "\\setlength{\\tabcolsep}{3.5pt}",
                "\\renewcommand{\\arraystretch}{0.95}",
                f"\\caption{{{latex_escape(titulo)}}}",
                f"\\begin{{tabular}}{{{col_spec}}}",
                "\\toprule",
                header,
                "\\midrule",
                *dados,
                "\\bottomrule",
                "\\end{tabular}",
                "\\end{table}",
                "",
            ])

    (OUT_DIR / "gasto_mensal_maquinas.tex").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def escrever_localizacao_tex(xlsx: Path) -> None:
    resumo = pd.read_excel(xlsx, sheet_name="resumo_local")
    cadastro = pd.read_excel(xlsx, sheet_name="cadastro_parque")
    gasto_local = None
    if "gasto_por_local" in pd.ExcelFile(xlsx).sheet_names:
        gasto_local = pd.read_excel(xlsx, sheet_name="gasto_por_local")

    marcas = [c for c in resumo.columns if c not in ("Local", "Total")]
    linhas = [
        "Distribuição informada pelo diretor financeiro, detalhada por identificador de máquina "
        "(\\texttt{maq\\_id}) e referência de centro de custo na base.",
        "",
        "\\begin{table}[H]",
        "\\centering",
        "\\small",
        f"\\begin{{tabular}}{{l{'r' * len(marcas)}r}}",
        "\\toprule",
        "Local & " + " & ".join(marcas) + r" & Total \\",
        "\\midrule",
    ]
    for _, row in resumo.iterrows():
        local = latex_escape(str(row["Local"]))
        vals = [fmt_num(row[m], 0) for m in marcas]
        linhas.append(f"{local} & " + " & ".join(vals) + f" & {fmt_num(row['Total'], 0)}" + r" \\")
    linhas.extend([
        "\\bottomrule",
        "\\end{tabular}",
        "\\caption{Quantidade de máquinas por local de operação.}",
        "\\end{table}",
    ])
    if gasto_local is not None and len(gasto_local):
        marcas_g = [c for c in gasto_local.columns if c in ("LIEBHERR", "HYUNDAI")]
        linhas.extend([
            "",
            "\\begin{table}[H]",
            "\\centering",
            "\\small",
            f"\\begin{{tabular}}{{l{'r' * (len(marcas_g) + 3)}}}",
            "\\toprule",
            "Local & " + " & ".join(marcas_g) + r" & Total & Máq. & R\$/máq \\",
            "\\midrule",
        ])
        for _, row in gasto_local.iterrows():
            vals_m = [fmt_brl(row[m]) for m in marcas_g]
            linhas.append(
                f"{latex_escape(str(row['Local']))} & "
                + " & ".join(vals_m)
                + f" & {fmt_brl(row['Total'])}"
                + f" & {fmt_num(row['Máquinas'], 0)}"
                + f" & {fmt_brl(row['R$/máq'])}" + r" \\"
            )
        linhas.extend([
            "\\bottomrule",
            "\\end{tabular}",
            "\\caption{Gasto por unidade de operação (soma das máquinas do local).}",
            "\\end{table}",
        ])
    linhas.extend([
        "",
        "\\begin{table}[H]",
        "\\centering",
        "\\scriptsize",
        "\\begin{tabular}{lllll}",
        "\\toprule",
        r"Máquina & Marca & Local & Filial (CC) & Referência CC \\",
        "\\midrule",
    ])
    for _, row in cadastro.iterrows():
        linhas.append(
            f"{latex_escape(row['maq_id'])} & "
            f"{latex_escape(row['MARCA'])} & "
            f"{latex_escape(row['local_operacao'])} & "
            f"{latex_escape(row.get('filial_cc', ''))} & "
            f"{latex_escape(row.get('referencia_cc', ''))}" + r" \\"
        )
    linhas.extend([
        "\\bottomrule",
        "\\end{tabular}",
        "\\caption{Cadastro do parque: local de operação e centro de custo de referência.}",
        "\\end{table}",
    ])
    (OUT_DIR / "localizacao.tex").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def escrever_conclusao_tex(insights: list[str]) -> None:
    texto = (
        "Em síntese, as duas marcas apresentam perfis distintos de custo. "
        "O comparativo principal usa o custo médio por máquina do parque (volume total $\\div$ 7 ou 16), "
        "não o volume bruto --- Liebherr tem 7 máquinas e Hyundai 16, e totais absolutos enviesam a leitura. "
        "Diferem na intensidade por máquina e no mix entre manutenção, combustível e peças. "
    )
    if insights:
        for chave in ("Unidade com maior custo", "Concentração"):
            conc = [i for i in insights if chave in i]
            if conc:
                limpo = re.sub(r"\*\*", "", conc[0])
                trecho = limpo.split(":", 1)[-1].strip() if ":" in limpo else limpo.strip()
                if trecho:
                    texto += latex_escape(trecho) + " "
                break
    texto += (
        "Recomenda-se priorizar revisão dos ativos líderes de gasto e "
        "acompanhar a evolução mensal para validar ações de contenção de custo."
    )
    (OUT_DIR / "conclusao.tex").write_text(texto + "\n", encoding="utf-8")


def sincronizar_figuras() -> None:
    script = OUT_DIR / "sincronizar_figuras.py"
    if not script.exists():
        return
    import importlib.util

    spec = importlib.util.spec_from_file_location("sincronizar_figuras", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.sincronizar(gerar=True)


def exportar(xlsx: Path | None = None) -> Path:
    xlsx = xlsx or XLSX
    if not xlsx.exists():
        raise FileNotFoundError(f"Execute o notebook antes: {xlsx}")

    kpi_raw = pd.read_excel(xlsx, sheet_name="kpi")
    if "indicador" in kpi_raw.columns:
        kpi = kpi_raw.set_index("indicador")
    else:
        kpi = kpi_raw.set_index(kpi_raw.columns[0])

    insights_df = pd.read_excel(xlsx, sheet_name="insights")
    insights = insights_df["insight"].dropna().astype(str).tolist()

    periodo = inferir_periodo(xlsx)
    escrever_dados_tex(periodo)
    escrever_insights_tex(insights)
    escrever_kpi_tex(kpi)
    xl_sheets = pd.ExcelFile(xlsx).sheet_names
    if "cadastro_parque" in xl_sheets and "resumo_local" in xl_sheets:
        escrever_localizacao_tex(xlsx)
    if "gasto_maquina_mes_wide" in xl_sheets:
        escrever_gasto_mensal_maquinas_tex(xlsx)
    escrever_conclusao_tex(insights)
    sincronizar_figuras()
    return OUT_DIR


if __name__ == "__main__":
    dest = exportar()
    print(f"LaTeX atualizado em: {dest}")
