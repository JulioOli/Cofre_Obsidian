"""Correcoes finais nos notebooks de fechamento."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FECH = REPO / "04-Notebooks" / "Fechamento"

IMPORT = (
    "import sys\n"
    "from pathlib import Path\n"
    'sys.path.insert(0, str((Path.cwd().parent / "Utitlities").resolve()))\n'
    "from fechamento_excel import parse_valor_fechamento, parse_data_fechamento, gravar_fechamento_excel\n\n"
)


def fix_save_imports(path: Path) -> None:
    nb = json.loads(path.read_text(encoding="utf-8"))
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        if "gravar_fechamento_excel(" in src and "from fechamento_excel import" not in src:
            cell["source"] = [IMPORT + src]
    path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("save import", path.name)


def fix_supply() -> None:
    p = FECH / "normalizar_supply.ipynb"
    nb = json.loads(p.read_text(encoding="utf-8"))
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        if "fechamento_df = pd.DataFrame(linhas_saida" not in src:
            continue
        src = src.replace(
            'nova["valor_pago"] = -abs(valor_pago) if valor_pago is not None and not pd.isna(valor_pago) else pd.NA\n    nova["valor_conta"] = -abs(vc) if vc is not None and not pd.isna(vc) else pd.NA',
            'vc = valor_nf if pd.isna(valor_pago) else valor_pago\n    nova["valor_pago"] = -abs(valor_pago) if valor_pago is not None and not pd.isna(valor_pago) else pd.NA\n    nova["valor_conta"] = -abs(vc) if vc is not None and not pd.isna(vc) else pd.NA',
        )
        src = src.replace(
            'nova["data_nf"] = _pick(row, "data_nf", "emissao", "emissão", default="")',
            'nova["data_nf"] = parse_data_fechamento(_pick(row, "data_nf", "emissao", "emissão", default=""))',
        )
        src = src.replace(
            'nova["data_pagamento"] = _pick(row, "data_pagamento", "pagamento", default="")',
            'nova["data_pagamento"] = parse_data_fechamento(_pick(row, "data_pagamento", "pagamento", default=""))',
        )
        cell["source"] = [src]
    p.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("supply dates/vc", p.name)


def fix_despesas_conferencia() -> None:
    p = FECH / "normalizar_atua_despesas.ipynb"
    nb = json.loads(p.read_text(encoding="utf-8"))
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        if "_soma_valor_saida = pd.to_numeric(fechamento_df[\"valor_conta\"]" in src:
            src = src.replace(
                '_soma_valor_saida = pd.to_numeric(fechamento_df["valor_conta"], errors="coerce").sum()',
                '_soma_valor_saida = pd.to_numeric(fechamento_df["valor_conta"], errors="coerce").abs().sum()',
            )
            cell["source"] = [src]
    p.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("despesas conferencia", p.name)


if __name__ == "__main__":
    for nb in [
        "normalizar_atua_despesas.ipynb",
        "normalizar_atua_receitas.ipynb",
        "normalizar_atua_custo_frete.ipynb",
    ]:
        fix_save_imports(FECH / nb)
    fix_supply()
    fix_despesas_conferencia()
