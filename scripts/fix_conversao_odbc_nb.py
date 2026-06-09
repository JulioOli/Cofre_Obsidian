"""
Aplica todas as correcoes no conversao_odbc_para_fechamento.ipynb.

Uso (na raiz do repo):
  .\\.venv\\Scripts\\python.exe scripts\\fix_conversao_odbc_nb.py
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NB = REPO / "04-Notebooks" / "Fechamento" / "conversao_odbc_para_fechamento.ipynb"

SALVAR_FECHAMENTO = """def salvar_fechamento(df_out: pd.DataFrame, caminho: Path) -> None:
    gravar_fechamento_excel(
        df_out,
        caminho,
        sheet_name='Fechamento',
        colunas_preservar_sinal=('valor_conta',),
    )"""


def _build_cell3() -> str:
    raw = subprocess.check_output(
        ["git", "show", "188745a:04-Notebooks/Fechamento/conversao_odbc_para_fechamento.ipynb"],
        cwd=REPO,
    )
    cell3 = "".join(json.loads(raw.decode("utf-8"))["cells"][3]["source"])

    cell3 = re.sub(
        r"def salvar_fechamento\(df_out: pd\.DataFrame, caminho: Path\) -> None:.*?(?=\n\nsaidas_por_mes)",
        SALVAR_FECHAMENTO.rstrip(),
        cell3,
        count=1,
        flags=re.S,
    )
    cell3 = cell3.replace(
        "out['valor_conta'] = work['valor_centro_num']",
        "out['valor_conta'] = work['valor_plano_num']",
    )
    cell3 = cell3.replace(
        'print(f"{prefixo}ODBC valor_centro={centro:,.2f} | saida valor_conta={conta:,.2f}")',
        'print(f"{prefixo}ODBC valor_plano={plano:,.2f} | saida valor_conta={conta:,.2f}")',
    )

    header = (
        "import sys\n"
        "from pathlib import Path\n"
        'sys.path.insert(0, str((Path.cwd().parent / "Utitlities").resolve()))\n'
        "from fechamento_excel import gravar_fechamento_excel\n\n"
    )
    cell3 = header + cell3

    checagem = """

# --- Checagem de layout ---
faltantes = [c for c in COLUNAS_FECHAMENTO if c not in out.columns]
extras = [c for c in out.columns if c not in COLUNAS_FECHAMENTO]
print('Colunas faltantes:', faltantes)
print('Colunas extras:', extras)
print('Quantidade de colunas esperadas:', len(COLUNAS_FECHAMENTO))
print('Quantidade de colunas na saida:', len(out.columns))
print()
if arquivos_gerados:
    print('Arquivo(s) gerado(s):')
    for caminho in arquivos_gerados:
        print(f'  - {caminho.resolve()}')
else:
    print('Nenhum arquivo gerado.')
"""
    return cell3.rstrip() + checagem


def main() -> None:
    nb = json.loads(NB.read_text(encoding="utf-8"))

    md = "".join(nb["cells"][0]["source"])
    md = md.replace("`valor_conta` <- `valor_centro`", "`valor_conta` <- `valor_plano` (sinal preservado)")
    nb["cells"][0]["source"] = [line + "\n" for line in md.splitlines()]

    src1 = "".join(nb["cells"][1]["source"])
    src1 = re.sub(
        r"NOTEBOOK_VERSAO = '[^']+'.*",
        "NOTEBOOK_VERSAO = '2.3'  # valor_conta <- valor_plano, sinal preservado na gravacao",
        src1,
        count=1,
    )
    src1 = re.sub(
        r"MESES_REFERENCIA = \[.*?\]",
        "MESES_REFERENCIA = ['05/2026']",
        src1,
        count=1,
    )
    if "/ 'Fechamento'" not in src1:
        src1 = src1.replace(
            "OUT_DIR = Path('..') / '..' / '02-Referencias'",
            "OUT_DIR = Path('..') / '..' / '02-Referencias' / 'Fechamento'",
        )
    nb["cells"][1]["source"] = [line + "\n" for line in src1.splitlines()]

    cell3 = _build_cell3()
    nb["cells"][3]["source"] = [line + "\n" for line in cell3.splitlines()]
    nb["cells"][3]["outputs"] = []
    nb["cells"][3]["execution_count"] = None

    nb["cells"][4]["source"] = [
        "# v2.3: conversao na celula 3. Restart Kernel -> Run All.\n",
        "# valor_conta = valor_plano do ODBC (sem forcar -abs na gravacao).\n",
    ]
    nb["cells"][4]["outputs"] = []
    nb["cells"][4]["execution_count"] = None

    NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")

    assert "valor_plano_num" in cell3 and "colunas_preservar_sinal" in cell3
    print(f"OK {NB.name} v2.3 | celula 3: {len(cell3)} chars")


if __name__ == "__main__":
    main()
