"""
Filtra fechamento2025.xlsx por placas de equipamentos locados (Resende, Piracicaba, Joinville).

Processa Planilha1 (2025), Planilha2 (2024) e Planilha3 (2026) com a mesma regra de busca.
Colunas de varredura: n4_centro_custo (ou equivalentes de CC), observacao/observação, Dados auxiliares.
Aceita placas compactas (PHH0044) e com traço (PHH-0044), incluindo variantes EHH/EHL.

Saída: uma aba filtrada por planilha de entrada, mesmas colunas + Cliente + Equipamento Locado.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
ENTRADA = REPO / "02-Referencias" / "fechamento2025.xlsx"
SAIDA = REPO / "02-Referencias" / "fechamento2025_placas_por_cliente.xlsx"

# Ordem de processamento e rótulo do período (para log)
ABAS_ENTRADA: list[tuple[str, str]] = [
    ("Planilha1", "2025"),
    ("Planilha2", "2024"),
    ("Planilha3", "2026"),
]

# Candidatos por papel (primeiro nome encontrado na planilha é usado por grupo)
COL_CANDIDATOS_CC = [
    "n4_centro_custo",
    "n4_cc",
    "n4_cod_centro_custo",
    "n3_centro_custo",
    "n3_cc",
]
COL_CANDIDATOS_OBS = ["observacao", "observação"]
COL_CANDIDATOS_AUX = ["dados auxiliares"]

MAPA_PLACA_CLIENTE = {
    "PHH0044": "Resende",
    "PHH0049": "Piracicaba",
    "EHH0044": "Joinville",
    "EHL0044": "Joinville",
    "EHH0043": "Joinville",
    "EHL0043": "Joinville",
    "EHH0041": "Joinville",
    "EHL0041": "Joinville",
}

EQUIPAMENTO_POR_CLIENTE = {
    "Resende": "PHH0044",
    "Piracicaba": "PHH0049",
    "Joinville": "EHH0044; EHL0043; EHL0041",
}

ORDEM_CLIENTE = {"Resende": 0, "Piracicaba": 1, "Joinville": 2}


def _norm_col(name: str) -> str:
    s = unicodedata.normalize("NFKD", str(name).strip())
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def _resolver_colunas_busca(columns: list) -> list[str]:
    """Retorna lista de nomes reais de colunas a varrer (sem duplicar)."""
    norm_map = {_norm_col(c): c for c in columns}
    escolhidas: list[str] = []

    def _pick(candidatos: list[str]) -> str | None:
        for cand in candidatos:
            key = _norm_col(cand)
            if key in norm_map:
                return norm_map[key]
        return None

    for grupo in (COL_CANDIDATOS_CC, COL_CANDIDATOS_OBS, COL_CANDIDATOS_AUX):
        col = _pick(grupo)
        if col and col not in escolhidas:
            escolhidas.append(col)
    return escolhidas


def _placa_canonica(codigo: str) -> str:
    c = codigo.upper().replace("-", "")
    aliases = {"EHL0044": "EHH0044", "EHL0043": "EHH0043", "EHL0041": "EHH0041"}
    return aliases.get(c, c)


def _variantes_busca(codigo: str) -> list[str]:
    c = codigo.upper().replace("-", "")
    vals = [c]
    if len(c) >= 7:
        vals.append(f"{c[:3]}-{c[3:]}")
    return vals


def _build_search_patterns() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for codigo in MAPA_PLACA_CLIENTE:
        can = _placa_canonica(codigo)
        for pat in _variantes_busca(codigo):
            if pat not in seen:
                seen.add(pat)
                out.append((pat, can))
    return sorted(out, key=lambda x: len(x[0]), reverse=True)


PATTERNS = _build_search_patterns()


def _norm_text(v) -> str:
    if pd.isna(v):
        return ""
    return str(v).upper()


def placas_no_texto(texto: str) -> list[tuple[str, str]]:
    t = _norm_text(texto)
    found: list[tuple[str, str]] = []
    seen_can: set[str] = set()
    for pat, can in PATTERNS:
        if re.search(r"(?<![A-Z0-9])" + re.escape(pat) + r"(?![A-Z0-9])", t):
            if can not in seen_can:
                seen_can.add(can)
                found.append((can, MAPA_PLACA_CLIENTE[can]))
    return found


def placas_na_linha(row: pd.Series, cols_busca: list[str]) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    seen_can: set[str] = set()
    for col in cols_busca:
        for can, cli in placas_no_texto(str(row[col])):
            if can not in seen_can:
                seen_can.add(can)
                found.append((can, cli))
    return found


def classificar_linha(row: pd.Series, cols_busca: list[str]) -> tuple[str, str]:
    hits = placas_na_linha(row, cols_busca)
    if not hits:
        return "", ""
    clientes: list[str] = []
    placas: list[str] = []
    seen_cli: set[str] = set()
    for can, cli in hits:
        placas.append(can)
        if cli not in seen_cli:
            seen_cli.add(cli)
            clientes.append(cli)
    clientes.sort(key=lambda c: ORDEM_CLIENTE.get(c, 9))
    cliente_str = "; ".join(clientes)
    if len(clientes) == 1:
        equip_str = EQUIPAMENTO_POR_CLIENTE[clientes[0]]
    else:
        equip_str = "; ".join(placas)
    return cliente_str, equip_str


def filtrar_planilha(df: pd.DataFrame, cols_busca: list[str]) -> pd.DataFrame:
    if not cols_busca:
        return df.iloc[0:0].copy()

    classif = df.apply(lambda r: classificar_linha(r, cols_busca), axis=1, result_type="expand")
    classif.columns = ["Cliente", "Equipamento Locado"]
    mask = classif["Cliente"].astype(str).str.strip() != ""

    out = df.loc[mask].copy()
    out["Cliente"] = classif.loc[mask, "Cliente"].values
    out["Equipamento Locado"] = classif.loc[mask, "Equipamento Locado"].values
    return out


def main() -> None:
    if not ENTRADA.exists():
        raise FileNotFoundError(f"Entrada não encontrada: {ENTRADA}")

    xl = pd.ExcelFile(ENTRADA)
    sheets_out: dict[str, pd.DataFrame] = {}
    meta: list[str] = []

    for sheet_name, ano in ABAS_ENTRADA:
        if sheet_name not in xl.sheet_names:
            raise FileNotFoundError(
                f"Aba '{sheet_name}' não encontrada em {ENTRADA.name}. Abas: {xl.sheet_names}"
            )

        df = pd.read_excel(ENTRADA, sheet_name=sheet_name, dtype=object)
        cols_busca = _resolver_colunas_busca(list(df.columns))
        out = filtrar_planilha(df, cols_busca)
        sheets_out[sheet_name] = out

        meta.append(
            f"\n=== {sheet_name} (fechamento {ano}) ===\n"
            f"  Entrada: {len(df):,} linhas, {len(df.columns)} colunas\n"
            f"  Colunas de busca: {cols_busca}\n"
            f"  Saída:   {len(out):,} linhas, {len(out.columns)} colunas\n"
            f"  Por Cliente:\n{out.groupby('Cliente', dropna=False).size().to_string()}"
        )

    destino = SAIDA
    for tentativa in (destino, SAIDA.with_stem(f"{SAIDA.stem}_novo")):
        try:
            with pd.ExcelWriter(tentativa, engine="openpyxl") as writer:
                for sheet_name, out in sheets_out.items():
                    out.to_excel(writer, sheet_name=sheet_name, index=False)
            destino = tentativa
            break
        except PermissionError:
            if tentativa == SAIDA.with_stem(f"{SAIDA.stem}_novo"):
                raise
            print(f"[AVISO] {SAIDA.name} em uso. Tentando arquivo alternativo...")

    print(f"Arquivo gerado: {destino.resolve()}")
    resumos = meta
    print("".join(resumos))


if __name__ == "__main__":
    main()
