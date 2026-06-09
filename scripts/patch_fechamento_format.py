"""Aplica padrao fechamento_excel nos notebooks/scripts de conversao."""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FECHAMENTO_DIR = REPO / "04-Notebooks" / "Fechamento"
UTILS_DIR = REPO / "04-Notebooks" / "Utitlities"

IMPORT_BLOCK = (
    "import sys\n"
    "from pathlib import Path\n"
    'sys.path.insert(0, str((Path.cwd().parent / "Utitlities").resolve()))\n'
    "from fechamento_excel import parse_valor_fechamento, parse_data_fechamento, gravar_fechamento_excel\n"
    "\n"
)


def _cell_src(cell: dict) -> str:
    return "".join(cell.get("source", []))


def _set_src(cell: dict, text: str) -> None:
    cell["source"] = [text]


def _ensure_import(src: str) -> str:
    if "from fechamento_excel import" in src:
        return src
    return IMPORT_BLOCK + src


def patch_despesas() -> None:
    p = FECHAMENTO_DIR / "normalizar_atua_despesas.ipynb"
    nb = json.loads(p.read_text(encoding="utf-8"))
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = _cell_src(cell)
        if "linhas_saida = []" in src and "def _to_float(v):" in src:
            src = _ensure_import(src)
            src = re.sub(
                r"def _to_float\(v\):.*?(?=\nmodelo_cols = )",
                "def _to_float(v):\n    return parse_valor_fechamento(v)\n\n\n",
                src,
                count=1,
                flags=re.S,
            )
            src = src.replace(
                'nova["valor_pago"] = v\n        nova["valor_conta"] = v',
                'nova["valor_pago"] = -abs(v)\n        nova["valor_conta"] = -abs(v)',
            )
            src = src.replace(
                'nova["data_nf"] = _fmt_data(row["dt_lancamento_"])\n    nova["data_pagamento"] = ""',
                'nova["data_nf"] = parse_data_fechamento(row["dt_lancamento_"])\n    nova["data_pagamento"] = pd.NaT',
            )
            _set_src(cell, src)
        if "_salvar_excel" in src:
            tail = ""
            if "if ccs_nao_mapeados_cc:" in src:
                tail = src[src.index("if ccs_nao_mapeados_cc:") :]
            _set_src(
                cell,
                """import datetime

SHEET_NAME = "ATUA_despesas_fechamento"

arquivo_saida_exec = ARQUIVO_SAIDA
try:
    gravar_fechamento_excel(fechamento_df, arquivo_saida_exec, sheet_name=SHEET_NAME)
    print(f"Arquivo gerado: {arquivo_saida_exec.resolve()}")
except PermissionError:
    ts = datetime.datetime.now().strftime("%H%M%S")
    arquivo_saida_exec = ARQUIVO_SAIDA.with_stem(f"{ARQUIVO_SAIDA.stem}_{ts}")
    gravar_fechamento_excel(fechamento_df, arquivo_saida_exec, sheet_name=SHEET_NAME)
    print(
        f"[AVISO] Arquivo principal em uso ({ARQUIVO_SAIDA.name}). "
        f"Salvo como: {arquivo_saida_exec.resolve()}"
    )

print(f"Linhas gravadas: {len(fechamento_df)}")

"""
                + tail,
            )
    p.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("patched", p.name)


def patch_receitas_custo_frete(name: str, sheet: str) -> None:
    p = FECHAMENTO_DIR / name
    nb = json.loads(p.read_text(encoding="utf-8"))
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = _cell_src(cell)
        if "def _fmt_brl(v)" in src and "linhas_saida" in src:
            src = _ensure_import(src)
            src = re.sub(
                r"def _fmt_brl\(v\).*?(?=\n(?:def |for i, row|linhas_saida))",
                "",
                src,
                count=1,
                flags=re.S,
            )
            src = src.replace(
                'nova["valor_nf"]             = _fmt_brl(valor)',
                'nova["valor_nf"]             = valor',
            )
            src = src.replace(
                'nova["valor_pago"]           = _fmt_brl(valor)',
                'nova["valor_pago"]           = -abs(valor) if valor is not None else pd.NA',
            )
            src = src.replace(
                'nova["valor_conta"]          = _fmt_brl(valor)',
                'nova["valor_conta"]          = -abs(valor) if valor is not None else pd.NA',
            )
            src = src.replace(
                'nova["valor_nf"]             = _fmt_brl(valor_neg)',
                'nova["valor_nf"]             = valor_neg',
            )
            src = src.replace(
                'nova["valor_pago"]           = _fmt_brl(valor_neg)',
                'nova["valor_pago"]           = -abs(valor_neg) if valor_neg is not None else pd.NA',
            )
            src = src.replace(
                'nova["valor_conta"]          = _fmt_brl(valor_neg)',
                'nova["valor_conta"]          = -abs(valor_neg) if valor_neg is not None else pd.NA',
            )
            src = src.replace(
                "    nova[\"data_nf\"]              = dt_emis\n",
                "    nova[\"data_nf\"]              = parse_data_fechamento(row.get(\"dt_emissao\", \"\"))\n",
            )
            src = src.replace(
                "    nova[\"data_pagamento\"]       = dt_emis\n",
                "    nova[\"data_pagamento\"]       = parse_data_fechamento(row.get(\"dt_emissao\", \"\"))\n",
            )
            _set_src(cell, src)
        if "fechamento_df.to_excel" in src and "openpyxl" in src:
            tail = ""
            if "if filiais_sem_mapa:" in src:
                tail = src[src.index("if filiais_sem_mapa:") :]
            elif "print()" in src and "[OK]" in src:
                tail = src[src.index("print()") :]
            _set_src(
                cell,
                f"""import datetime

SHEET_NAME = {sheet!r}

arquivo_saida_exec = ARQUIVO_SAIDA
try:
    gravar_fechamento_excel(fechamento_df, arquivo_saida_exec, sheet_name=SHEET_NAME)
    print(f"Arquivo gerado: {{arquivo_saida_exec.resolve()}}")
    print(f"Linhas gravadas: {{len(fechamento_df)}}")
except PermissionError:
    ts = datetime.datetime.now().strftime("%H%M%S")
    alt = arquivo_saida_exec.with_stem(f"{{arquivo_saida_exec.stem}}_{{ts}}")
    gravar_fechamento_excel(fechamento_df, alt, sheet_name=SHEET_NAME)
    print(f"[AVISO] Arquivo principal em uso. Salvo como: {{alt.resolve()}}")
    print(f"Linhas gravadas: {{len(fechamento_df)}}")

"""
                + tail,
            )
    p.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("patched", p.name)


def patch_supply() -> None:
    p = FECHAMENTO_DIR / "normalizar_supply.ipynb"
    nb = json.loads(p.read_text(encoding="utf-8"))
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = _cell_src(cell)
        if "def _fmt_brl(v):" in src and "fechamento_df = pd.DataFrame" not in src:
            src = _ensure_import(src)
            src = re.sub(r"def _fmt_brl\(v\):.*?(?=\ndef )", "", src, count=1, flags=re.S)
            _set_src(cell, src)
        if "fechamento_df = pd.DataFrame(linhas_saida" in src:
            src = _ensure_import(src)
            src = src.replace(
                'nova["valor_nf"] = _fmt_brl(valor_nf)',
                'nova["valor_nf"] = valor_nf',
            )
            src = src.replace(
                'nova["valor_pago"] = _fmt_brl(valor_pago)',
                'nova["valor_pago"] = -abs(valor_pago) if valor_pago is not None and not pd.isna(valor_pago) else pd.NA',
            )
            src = src.replace(
                'nova["valor_conta"] = _fmt_brl(valor_nf if pd.isna(valor_pago) else valor_pago)',
                'vc = valor_nf if pd.isna(valor_pago) else valor_pago\n    nova["valor_conta"] = -abs(vc) if vc is not None and not pd.isna(vc) else pd.NA',
            )
            src = src.replace(
                'from openpyxl.styles import Font as _Font\n\n',
                "",
            )
            src = re.sub(
                r"for destino in \[.*?\n(?:.*?\n)*?print\(f\"\\nLinhas geradas",
                """for destino in [ARQUIVO_SAIDA_FECHAMENTO, ARQUIVO_SAIDA_BRACOFER, ARQUIVO_SAIDA_FINAL]:
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        gravar_fechamento_excel(fechamento_df, destino, sheet_name="fechamento_normalizado")
        print(f"Arquivo gerado: {destino.resolve()}")
    except PermissionError:
        print(f"[AVISO] Arquivo em uso, pulando: {destino.name}")

print(f"\\nLinhas geradas""",
                src,
                count=1,
                flags=re.S,
            )
            _set_src(cell, src)
    p.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("patched", p.name)


def patch_odbc() -> None:
    p = FECHAMENTO_DIR / "conversao_odbc_para_fechamento.ipynb"
    nb = json.loads(p.read_text(encoding="utf-8"))
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = _cell_src(cell)
        if "FMT_NUMERICO_EXCEL" in src:
            src = src.replace("FMT_NUMERICO_EXCEL = '#,##0.00'", "FMT_NUMERICO_EXCEL = '#.##0,00'")
            _set_src(cell, src)
        if "def salvar_fechamento(df_out" in src and "read_odbc_base" in src:
            if "from fechamento_excel import" not in src:
                src = _ensure_import(src)
            src = re.sub(
                r"def salvar_fechamento\(df_out: pd\.DataFrame, caminho: Path\) -> None:.*?(?=\n\nsaidas_por_mes)",
                "def salvar_fechamento(df_out: pd.DataFrame, caminho: Path) -> None:\n"
                "    gravar_fechamento_excel(df_out, caminho, sheet_name='Fechamento')\n",
                src,
                count=1,
                flags=re.S,
            )
            _set_src(cell, src)
    p.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("patched", p.name)


def patch_base_r() -> None:
    p = UTILS_DIR / "base_r_para_fechamento_folha.py"
    text = p.read_text(encoding="utf-8")
    if "from fechamento_excel import" not in text:
        text = text.replace(
            "import pandas as pd\n",
            "import pandas as pd\n\nfrom fechamento_excel import gravar_fechamento_excel\n",
        )
    text = text.replace('_FMT_MOEDA_EXCEL = "#,##0.00"\n', "")
    text = re.sub(
        r"    with pd\.ExcelWriter\(output_path, engine=\"openpyxl\"\) as w:.*?print\(f\"Gravado:",
        '    gravar_fechamento_excel(out_df, output_path, sheet_name=args.sheet_out)\n    print(f"Gravado:',
        text,
        count=1,
        flags=re.S,
    )
    p.write_text(text, encoding="utf-8")
    print("patched", p.name)


def patch_r_fopa() -> None:
    p = UTILS_DIR / "r_fopa_para_fechamento.py"
    text = p.read_text(encoding="utf-8")
    if "gravar_fechamento_excel" not in text:
        text = text.replace(
            "from base_r_para_fechamento_folha import (\n",
            "from fechamento_excel import gravar_fechamento_excel\nfrom base_r_para_fechamento_folha import (\n",
        )
    text = re.sub(
        r"    args\.output\.parent\.mkdir\(parents=True, exist_ok=True\)\n    with pd\.ExcelWriter\(args\.output, engine=\"openpyxl\"\) as w:.*?print\(\n        f\"Gravado:",
        '    gravar_fechamento_excel(out_df, args.output, sheet_name=args.sheet_out)\n    print(\n        f"Gravado:',
        text,
        count=1,
        flags=re.S,
    )
    p.write_text(text, encoding="utf-8")
    print("patched", p.name)


if __name__ == "__main__":
    patch_despesas()
    patch_receitas_custo_frete("normalizar_atua_receitas.ipynb", "ATUA_receitas")
    patch_receitas_custo_frete("normalizar_atua_custo_frete.ipynb", "ATUA_custo_frete")
    patch_supply()
    patch_odbc()
    patch_base_r()
    patch_r_fopa()
