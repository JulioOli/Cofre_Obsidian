# -*- coding: utf-8 -*-
"""
Soma gastos SAGI (Planilha1) por combo/placa e mes, classificados nos eventos
08 e 09 da Planilha2. Multas e demais contas ficam fora da soma.

Reconciliacao: por combo (texto coluna Placa Planilha2) + mes, SAGI deve bater com
Planilha2 para 08. Manutencao e 09. Outras Despesas.

Regras:
  - EXCLUIR: multas (nao entram em 08 nem 09)
  - 08: manutencao veiculos/maquinas, pecas, transporte manutencao (sem patio)
  - 09: servicos terceiros/contratados, CSRF, fretes, ISS, consultoria, manutencao patio
  - 08: deduplicar por documento (rateio ODBC gera varias linhas por CC)
  - 09: fretes deduplicados por documento; demais contas 09 somam todas as linhas
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC_BASE = ROOT / "02-Referencias" / "base_financeira2026.xlsx"
OUT_MAIN = ROOT / "02-Referencias" / "base_financeira2026_placas_manut_serv_ped.xlsx"
OUT_ALT = ROOT / "02-Referencias" / "base_financeira2026_placas_manut_serv_ped_atualizado.xlsx"

PLACA_RE = re.compile(r"\b([A-Z]{3}[0-9][A-Z0-9][0-9]{2}|[A-Z]{3}[0-9]{4})\b", re.I)
TOL = 1.0  # tolerancia R$ para bater com Planilha2


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


def placas_em_texto(*parts) -> set[str]:
    t = " ".join(str(p) for p in parts if pd.notna(p))
    return {m.upper() for m in PLACA_RE.findall(t)}


def placa_do_descen(descen: str) -> str | None:
    s = norm_txt(descen).replace("_X000D_", " ")
    if "/ VEICULOS /" in s:
        m = PLACA_RE.search(s.split("/ VEICULOS /")[-1])
        return m.group(1).upper() if m else None
    last = s.split("/")[-1].strip()
    m = PLACA_RE.search(last)
    return m.group(1).upper() if m else None


def combo_da_linha(row: pd.Series, placas_hit: set[str], combo_por_placa: dict[str, str]) -> str:
    """Combo Planilha2 da linha: prioriza placa do CC em descen."""
    p_cc = placa_do_descen(row["descen"])
    if p_cc and p_cc in placas_hit:
        return combo_por_placa.get(p_cc, "")
    if len(placas_hit) == 1:
        pl = next(iter(placas_hit))
        return combo_por_placa.get(pl, "")
    for pl in sorted(placas_hit):
        c = combo_por_placa.get(pl, "")
        if c:
            return c
    return ""


def pick_ev(eventos: list[str], prefix: str) -> str:
    for ev in eventos:
        if ev.startswith(prefix):
            return ev
    return prefix


def classificar_lancamento(descdc: str) -> str:
    """Retorna 08, 09, EXCLUIR (multas) ou FORA (fora da reconciliacao 08/09)."""
    d = norm_txt(descdc)
    if "MULTA" in d:
        return "EXCLUIR"
    if (
        ("MANUTEN" in d and "PATIO" not in d)
        or "PECAS DE MANUTEN" in d
        or "TRANSPORTE MANUTEN" in d
        or d == "SERVICOS DE TERCEIROS"
    ):
        return "08"
    if any(k in d for k in ("SERVICO", "CSRF", "FRETES", "ISS", "CONSULTORIA")) or "PATIO" in d:
        return "09"
    return "FORA"


def soma_evento_combo(df_mes_cat: pd.DataFrame, cat: str) -> float:
    if df_mes_cat.empty:
        return 0.0
    if cat == "09":
        frete = df_mes_cat[df_mes_cat["descdc_norm"].str.contains("FRETES", na=False)]
        outros = df_mes_cat[~df_mes_cat["descdc_norm"].str.contains("FRETES", na=False)]
        total = outros["gasto"].sum()
        if not frete.empty:
            total += -frete.groupby("documento")["valor_raw"].first().sum()
        return round(total, 2)
    # 08: um valor por documento no combo
    return round(-df_mes_cat.groupby("documento")["valor_raw"].first().sum(), 2)


def main() -> None:
    s1 = pd.read_excel(SRC_BASE, sheet_name="Planilha1")
    s2 = pd.read_excel(SRC_BASE, sheet_name="Planilha2")
    eventos = list(dict.fromkeys(s2["Evento"].dropna().astype(str)))
    ev08 = pick_ev(eventos, "08.")
    ev09 = pick_ev(eventos, "09.")

    comp_col = next(c for c in s2.columns if "ompet" in c.lower() or "ompet" in norm_txt(c).lower())
    s2["mes"] = pd.to_datetime(s2[comp_col]).dt.to_period("M").astype(str)

    combo_por_placa: dict[str, str] = {}
    placas_oficiais: set[str] = set()
    for txt in s2["Placa"].dropna().unique():
        for pl in placas_em_texto(txt):
            placas_oficiais.add(pl)
            combo_por_placa[pl] = str(txt)

    mask = s1.apply(
        lambda r: bool(placas_em_texto(r["descen"], r["observacao"]) & placas_oficiais),
        axis=1,
    )

    linhas_det = []
    linhas_agg = []
    for _, row in s1[mask].iterrows():
        cat = classificar_lancamento(row["descdc"])
        placas_hit_row = placas_em_texto(row["descen"], row["observacao"]) & placas_oficiais
        if cat == "EXCLUIR":
            linhas_det.append(
                {
                    "combo": combo_da_linha(row, placas_hit_row, combo_por_placa),
                    "mes": pd.to_datetime(row["lancamento"]).to_period("M").strftime("%Y-%m"),
                    "evento": "EXCLUIDO - Multas",
                    "gasto": round(-parse_val(row["valor_centro"]), 2),
                    "descdc": row["descdc"],
                    "documento": row.get("documento", ""),
                    "incluido_soma_08_09": "NAO",
                }
            )
            continue
        if cat == "FORA":
            continue

        mes = pd.to_datetime(row["lancamento"]).to_period("M").strftime("%Y-%m")
        placas_hit = placas_hit_row
        combo = combo_da_linha(row, placas_hit, combo_por_placa)
        evento = ev08 if cat == "08" else ev09
        v = parse_val(row["valor_centro"])
        linhas_agg.append(
            {
                "combo": combo,
                "mes": mes,
                "cat": cat,
                "evento": evento,
                "gasto": round(-v, 2),
                "descdc_norm": norm_txt(row["descdc"]),
                "descdc": row["descdc"],
                "documento": str(row.get("documento", "")),
                "valor_raw": v,
            }
        )

    agg_raw = pd.DataFrame(linhas_agg)
    reconciliacao = []
    for combo in s2["Placa"].dropna().unique():
        combo = str(combo)
        df_c = agg_raw[agg_raw["combo"] == combo]
        meses = set(df_c["mes"].unique()) | set(
            s2[(s2["Placa"] == combo)]["mes"].unique()
        )
        for mes in sorted(meses):
            if not str(mes).startswith("20"):
                continue
            p2 = s2[(s2["Placa"] == combo) & (s2["mes"] == mes)]
            v08_p2 = (
                parse_val(p2[p2["Evento"] == ev08]["Valor"].iloc[0])
                if len(p2[p2["Evento"] == ev08])
                else 0.0
            )
            v09_p2 = (
                parse_val(p2[p2["Evento"] == ev09]["Valor"].iloc[0])
                if len(p2[p2["Evento"] == ev09])
                else 0.0
            )
            d = df_c[df_c["mes"] == mes]
            g08 = soma_evento_combo(d[d["cat"] == "08"], "08")
            g09 = soma_evento_combo(d[d["cat"] == "09"], "09")
            reconciliacao.append(
                {
                    "combo_veiculo": combo,
                    "mes": mes,
                    "evento": ev08,
                    "gasto_sagi": g08,
                    "gasto_planilha2": round(v08_p2, 2),
                    "diferenca": round(g08 - v08_p2, 2),
                    "bate": abs(g08 - v08_p2) <= TOL,
                }
            )
            reconciliacao.append(
                {
                    "combo_veiculo": combo,
                    "mes": mes,
                    "evento": ev09,
                    "gasto_sagi": g09,
                    "gasto_planilha2": round(v09_p2, 2),
                    "diferenca": round(g09 - v09_p2, 2),
                    "bate": abs(g09 - v09_p2) <= TOL,
                }
            )

    recon = pd.DataFrame(reconciliacao)

    # Tabela mensal por placa (proporcional ao combo: rateio do total do combo entre placas do conjunto)
    linhas_placa = []
    for _, r in recon.iterrows():
        combo = r["combo_veiculo"]
        pls = sorted(placas_em_texto(combo))
        n = len(pls) or 1
        parte = round(r["gasto_sagi"] / n, 2)
        for pl in pls:
            linhas_placa.append(
                {
                    "placa": pl,
                    "combo_veiculo": combo,
                    "mes": r["mes"],
                    "evento": r["evento"],
                    "gasto_rateado": parte,
                    "gasto_combo": r["gasto_sagi"],
                }
            )

    placa_long = pd.DataFrame(linhas_placa)
    pivot_placa = placa_long.pivot_table(
        index=["placa", "combo_veiculo"],
        columns=["mes", "evento"],
        values="gasto_rateado",
        aggfunc="sum",
        fill_value=0,
    )
    if not pivot_placa.empty:
        pivot_placa.columns = [f"{m} | {e}" for m, e in pivot_placa.columns]

    mapa = pd.DataFrame(
        [
            ("MULTAS DE TRANSITO / MULTAS", "EXCLUIR", "Nao entra na soma"),
            ("MANUTENCAO DE VEICULOS/MAQUINAS", ev08, "Dedupe por documento no combo"),
            ("PECAS DE MANUTENCAO", ev08, "Dedupe por documento no combo"),
            ("TRANSPORTE MANUTENCAO", ev08, "Dedupe por documento no combo"),
            ("SERVICOS DE TERCEIROS / CONTRATADOS", ev09, "Soma linhas"),
            ("CSRF", ev09, "Soma linhas"),
            ("FRETES E CARRETOS", ev09, "Dedupe por documento no combo"),
            ("ISS / CONSULTORIA / MANUTENCAO PATIO", ev09, "Soma linhas"),
            ("PEDAGIO, SEGURO, DIESEL, LOCACAO, etc.", "FORA", "Outros eventos Planilha2"),
        ],
        columns=["conta_sagi", "evento_planilha2", "regra_soma"],
    )

    excl_multas = pd.DataFrame(linhas_det) if linhas_det else pd.DataFrame()

    base_wb = OUT_ALT if OUT_ALT.exists() else OUT_MAIN
    sheets_keep = {}
    if base_wb.exists():
        skip = {
            "Gasto_mensal_por_placa",
            "Gasto_mensal_long",
            "Placas_resumo_total",
            "Gasto_mensal_por_placa_evento",
            "Gasto_mensal_placa_evento_long",
            "Gasto_mensal_placa_evento_pivot",
            "Mapa_conta_evento",
            "Lancamentos_por_evento",
            "Reconciliacao_planilha2",
            "Gasto_mensal_placa_08_09",
            "Multas_excluidas",
        }
        for sh in pd.ExcelFile(base_wb).sheet_names:
            if sh not in skip:
                sheets_keep[sh] = pd.read_excel(base_wb, sheet_name=sh)

    def write_to(path: Path) -> bool:
        try:
            with pd.ExcelWriter(path, engine="openpyxl") as w:
                for sh, df in sheets_keep.items():
                    df.to_excel(w, sheet_name=sh, index=False)
                recon.to_excel(w, sheet_name="Reconciliacao_planilha2", index=False)
                placa_long.to_excel(w, sheet_name="Gasto_mensal_placa_08_09", index=False)
                if not pivot_placa.empty:
                    pivot_placa.reset_index().to_excel(
                        w, sheet_name="Gasto_mensal_por_placa_evento", index=False
                    )
                mapa.to_excel(w, sheet_name="Mapa_conta_evento", index=False)
                if not excl_multas.empty:
                    excl_multas.to_excel(w, sheet_name="Multas_excluidas", index=False)
            return True
        except PermissionError:
            return False

    if write_to(OUT_MAIN):
        print("Atualizado:", OUT_MAIN)
    elif write_to(OUT_ALT):
        print("Salvo em:", OUT_ALT)
    else:
        raise PermissionError("Feche o Excel e execute novamente.")

    ok = recon["bate"].sum()
    tot = len(recon)
    print(f"Reconciliacao: {ok}/{tot} pares combo/mes/evento dentro de R$ {TOL}")
    if tot - ok > 0:
        print("\nDiferencas > tolerancia:")
        print(
            recon[~recon["bate"]][
                ["combo_veiculo", "mes", "evento", "gasto_sagi", "gasto_planilha2", "diferenca"]
            ]
            .head(20)
            .to_string(index=False)
        )


if __name__ == "__main__":
    main()
