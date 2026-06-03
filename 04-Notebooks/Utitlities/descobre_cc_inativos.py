"""Lista centros de custo presentes no relatorio completo e ausentes no de apenas ativos."""
from __future__ import annotations

import re
from pathlib import Path

# Raiz do repositorio (este arquivo: .../Cofre_Trabalho/04-Notebooks/Utitlities/)
ROOT = Path(__file__).resolve().parent.parent.parent
REFS = ROOT / "02-Referencias"

PATH_TODOS = REFS / "SAGI" / "centro-de-custo_ativos-e-inativos.csv"
PATH_ATIVOS = REFS / "SAGI" / "centro-de-custo_apenas-ativos.csv"

# Linhas de dado SAGI: codigo hierarquico no inicio da linha antes do primeiro ';'
_CC_LINE = re.compile(r"^\s*(\d+(?:\.\d+)*)\s*;")


def _codigos_cc(path: Path) -> set[str]:
    if not path.exists():
        raise FileNotFoundError(path.resolve())
    texto = path.read_text(encoding="latin-1", errors="replace")
    return {m.group(1) for line in texto.splitlines() if (m := _CC_LINE.match(line))}


def main() -> None:
    todos = _codigos_cc(PATH_TODOS)
    ativos = _codigos_cc(PATH_ATIVOS)
    inativos = sorted(todos - ativos)
    print(f"Arquivos:\n  {PATH_TODOS.name} ({len(todos)} codigos)\n  {PATH_ATIVOS.name} ({len(ativos)} codigos)")
    print(f"\nCentros de custo inativos ({len(inativos)}):")
    for cc in inativos:
        print(cc)


if __name__ == "__main__":
    main()
