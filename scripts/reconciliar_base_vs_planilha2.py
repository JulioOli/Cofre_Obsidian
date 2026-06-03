# -*- coding: utf-8 -*-
"""Gera Excel com uma aba: Reconciliacao_08_base_vs_p2 (base vs Planilha2 evento 08)."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "02-Referencias" / "base_financeira2026.xlsx"
OUT_MAIN = ROOT / "02-Referencias" / "base_financeira2026_placas_manut_serv_ped.xlsx"
OUT_ALT = ROOT / "02-Referencias" / "base_financeira2026_placas_manut_serv_ped_atualizado.xlsx"

PLACA_RE = re.compile(r"\b([A-Z]{3}[0-9][A-Z0-9][0-9]{2}|[A-Z]{3}[0-9]{4})\b", re.I)
# Evento 08 Planilha2 = Manutencao com Pecas e Servicos (SAGI)
CONTAS_08_NORM = {
    "MANUTENCAO DE VEICULOS/MAQUINAS",
    "PECAS DE MANUTENCAO",
    "TRANSPORTE MANUTENCAO",
    "SERVICOS DE TERCEIROS",
}
CODCDC_08 = {"7.1.1", "7.1.2", "7.1.7", "7.1.16"}
TOL = 1.0


def norm_txt(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.upper().strip()


def parse_val(s) -> float:
    if pd.isna(s):
        return 0.0
    if isinstance(s, (int, float)):
        return float(s)
    t = str(s).strip()
    if t in ("", "-", "nan"):
        return 0.0
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return 0.0


def placas_do_combo(texto_placa: str) -> set[str]:
    """Extrai placas do texto da coluna Placa (Planilha2).

    Corrige typo sem espaco: 'GDA9J63e Julieta' (sem \\b apos a placa, GDA9J63 some).
    """
    t = str(texto_placa)
    t = re.sub(
        r"([A-Z]{3}[0-9][A-Z0-9][0-9]{2})e(\s+[Jj]ulieta)",
        r"\1 e\2",
        t,
        flags=re.I,
    )
    t = re.sub(
        r"([A-Z]{3}[0-9]{4})e(\s+[Jj]ulieta)",
        r"\1 e\2",
        t,
        flags=re.I,
    )
    return {m.upper() for m in PLACA_RE.findall(t)}


def placas_em_texto(*parts) -> set[str]:
    t = " ".join(str(p) for p in parts if pd.notna(p))
    return {m.upper() for m in PLACA_RE.findall(t)}


def linha_cita_placa_descen(row: pd.Series, placas: set[str]) -> bool:
    """Mesmo criterio do filtro manual: placa aparece em descen (col. B)."""
    d = norm_txt(row.get("descen", ""))
    return any(pl in d for pl in placas)


def eh_conta_evento_08(row: pd.Series) -> bool:
    """Contas SAGI que compoem o evento 08 da Planilha2."""
    if norm_txt(row.get("descdc", "")) in CONTAS_08_NORM:
        return True
    return str(row.get("codcdc", "")).strip() in CODCDC_08


def soma_base_manut(s1: pd.DataFrame, placas: set[str], mes: str) -> tuple[float, int]:
    """Soma todas as linhas 7.1.x com placa do combo em descen (inclui rateio ODBC)."""
    mask_mes = pd.to_datetime(s1["lancamento"]).dt.to_period("M").astype(str) == mes
    sub = s1[mask_mes]
    total = 0.0
    n = 0
    for _, row in sub.iterrows():
        if not eh_conta_evento_08(row) or not linha_cita_placa_descen(row, placas):
            continue
        total += -parse_val(row["valor_centro"])
        n += 1
    return round(total, 2), n


def valor_gasto_planilha2(raw) -> float:
    """Planilha2 pode vir negativa; comparar sempre em valor absoluto de gasto."""
    return round(abs(parse_val(raw)), 2)


def main() -> None:
    s1 = pd.read_excel(SRC, sheet_name="Planilha1")
    s2 = pd.read_excel(SRC, sheet_name="Planilha2")

    col_comp = [c for c in s2.columns if str(c).startswith("Compet") or "compet" in str(c).lower()][0]
    col_valor = "Valor" if "Valor" in s2.columns else [c for c in s2.columns if norm_txt(c) == "VALOR"][0]
    col_placa = "Placa" if "Placa" in s2.columns else "Placa"
    col_evento = "Evento"

    eventos = list(dict.fromkeys(s2[col_evento].dropna().astype(str)))
    ev08 = next((e for e in eventos if str(e).startswith("08.")), None)
    if not ev08:
        raise ValueError("Evento 08 nao encontrado na Planilha2.")

    s2["competencia"] = pd.to_datetime(s2[col_comp])
    s2["mes"] = s2["competencia"].dt.to_period("M").astype(str)

    reconciliacao = []

    for combo in s2[col_placa].dropna().unique():
        combo = str(combo)
        placas = placas_do_combo(combo)
        if not placas:
            continue

        p2_08 = s2[(s2[col_placa] == combo) & (s2[col_evento] == ev08)]
        meses = sorted(p2_08["mes"].dropna().unique())

        for mes in meses:
            v08_p2 = (
                valor_gasto_planilha2(p2_08[p2_08["mes"] == mes][col_valor].iloc[0])
                if len(p2_08[p2_08["mes"] == mes])
                else 0.0
            )
            base08, n_lin = soma_base_manut(s1, placas, mes)
            reconciliacao.append(
                {
                    "placa_combo": combo,
                    "placas": ", ".join(sorted(placas)),
                    "competencia": mes,
                    "evento": ev08,
                    "valor_planilha2": v08_p2,
                    "valor_base_referencia": base08,
                    "diferenca_p2_menos_base": round(v08_p2 - base08, 2),
                    "bate_com_base": abs(v08_p2 - base08) <= TOL,
                    "linhas_base": n_lin,
                    "conta_base": "7.1.1 + 7.1.2 + 7.1.7 + 7.1.16 SERV. TERCEIROS",
                    "fonte_correta": "Planilha1 (base)",
                }
            )

    recon = pd.DataFrame(reconciliacao)

    def write_to(path: Path) -> bool:
        try:
            with pd.ExcelWriter(path, engine="openpyxl") as w:
                recon.to_excel(w, sheet_name="Reconciliacao_08_base_vs_p2", index=False)
            return True
        except PermissionError:
            return False

    if write_to(OUT_MAIN):
        print("Atualizado:", OUT_MAIN)
    elif write_to(OUT_ALT):
        print("Salvo em:", OUT_ALT)
    else:
        raise PermissionError("Feche o Excel.")

    r26 = recon[recon["competencia"].str.startswith("2026")]
    print("2026 - total pares:", len(r26))
    print("Planilha2 = base:", int(r26["bate_com_base"].sum()))
    print("Planilha2 > base:", int((r26["diferenca_p2_menos_base"] > TOL).sum()))
    print("Planilha2 < base:", int((r26["diferenca_p2_menos_base"] < -TOL).sum()))
    ex = r26[r26["placa_combo"].astype(str).str.contains("QAO4A53", na=False)]
    print(ex[["competencia", "valor_planilha2", "valor_base_referencia", "diferenca_p2_menos_base", "bate_com_base", "linhas_base"]].to_string(index=False))


if __name__ == "__main__":
    main()
