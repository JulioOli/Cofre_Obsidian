"""Restaura a celula de conversao ODBC apagada pelo patch_odbc."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NB = REPO / "04-Notebooks" / "Fechamento" / "conversao_odbc_para_fechamento.ipynb"
TMP = Path(__file__).with_name("_cell3_odbc_src.py")

raw = subprocess.check_output(
    ["git", "show", "188745a:04-Notebooks/Fechamento/conversao_odbc_para_fechamento.ipynb"],
    cwd=REPO,
)
nb_old = json.loads(raw.decode("utf-8"))
cell3_src = "".join(nb_old["cells"][3]["source"])

cell3_src = re.sub(
    r"def salvar_fechamento\(df_out: pd\.DataFrame, caminho: Path\) -> None:.*?(?=\n\nsaidas_por_mes)",
    "def salvar_fechamento(df_out: pd.DataFrame, caminho: Path) -> None:\n"
    "    gravar_fechamento_excel(df_out, caminho, sheet_name='Fechamento')",
    cell3_src,
    count=1,
    flags=re.S,
)

header = (
    "import sys\n"
    "from pathlib import Path\n"
    'sys.path.insert(0, str((Path.cwd().parent / "Utitlities").resolve()))\n'
    "from fechamento_excel import gravar_fechamento_excel\n\n"
)
cell3_src = header + cell3_src

checagem = """

# --- Checagem de layout (mesma celula: evita NameError se rodar so a ultima) ---
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
cell3_src = cell3_src.rstrip() + checagem

TMP.write_text(cell3_src, encoding="utf-8")

nb = json.loads(NB.read_text(encoding="utf-8"))
nb["cells"][3]["source"] = [line + "\n" for line in cell3_src.splitlines()]
nb["cells"][3]["outputs"] = []
nb["cells"][3]["execution_count"] = None

src1 = "".join(nb["cells"][1]["source"])
src1 = src1.replace(
    "NOTEBOOK_VERSAO = '2.0'",
    "NOTEBOOK_VERSAO = '2.1'  # celula 3 = leitura + conversao + exportacao",
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

# ultima celula vira lembrete (checagem ja esta na celula 3)
nb["cells"][4]["source"] = [
    "# A checagem de colunas e listagem de arquivos rodam no final da celula anterior.\n",
    "# Restart Kernel -> Run All apos alterar BASE_PATH ou MESES_REFERENCIA.\n",
]
nb["cells"][4]["outputs"] = []
nb["cells"][4]["execution_count"] = None

NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"OK: {NB.name} — celula 3 com {len(cell3_src)} caracteres")
