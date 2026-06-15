"""
Leitura e tratamento da planilha operacional de abastecimento interno.

Fonte: 02-Referencias/Custos-Maquinas/Media_de_Consumo_de_Diesel_das_Maquinas.xlsx
Tratamento: coluna G (MÉDIA CONSUMO L/H) muito discrepante é zerada;
            média geral por placa = média dos G tratados > 0.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CUSTOS = ROOT / "02-Referencias" / "Custos-Maquinas"
XLSX_MEDIA = CUSTOS / "Media_de_Consumo_de_Diesel_das_Maquinas.xlsx"
SHEET_MEDIA = "Media Maquinas 2026"

LH_MIN_COL_G = 3.0
LH_MAX_COL_G = 40.0


def _norm_txt(val) -> str:
    if pd.isna(val):
        return ""
    return str(val).strip()


def parse_numero_br(val) -> float | None:
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().upper().replace("R$", "").replace(" ", "")
    if not s or s in {"-", "NAN"}:
        return None
    m_typo = re.match(r"^(\d+)\.(\d+),(\d+)$", s)
    if m_typo:
        s = f"{m_typo.group(1)}{m_typo.group(2)}.{m_typo.group(3)}"
    elif "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def parse_horas_trabalhadas(val) -> float | None:
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s:
        return None
    m = re.search(r"\((\d+(?:[.,]\d+)?)\)", s)
    if m:
        return parse_numero_br(m.group(1))
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*h", s, re.I)
    if m:
        return parse_numero_br(m.group(1))
    return parse_numero_br(s)


def inferir_marca_pela_placa(placa: str) -> str:
    p = _norm_txt(placa).upper()
    if p.startswith("EHL"):
        return "LIEBHERR"
    if p.startswith("EHH"):
        return "HYUNDAI"
    return ""


def media_col_g_discrepante(media_g: float | None) -> tuple[bool, str]:
    if media_g is None:
        return True, "coluna G vazia"
    if media_g < LH_MIN_COL_G:
        return True, f"G < {LH_MIN_COL_G} L/h"
    if media_g > LH_MAX_COL_G:
        return True, f"G > {LH_MAX_COL_G} L/h"
    return False, ""


def tratar_media_col_g(media_g: float | None) -> tuple[float | None, bool, str]:
    discrepante, motivo = media_col_g_discrepante(media_g)
    if discrepante:
        return 0.0, True, motivo
    return media_g, False, ""


def carregar_planilha_media(
    xlsx_path: Path = XLSX_MEDIA,
    sheet_name: str = SHEET_MEDIA,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Lê só a planilha de médias; retorna detalhe, resumo por placa e visão geral."""
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Planilha não encontrada: {xlsx_path}")

    raw = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=None)
    abastecimentos: list[dict] = []
    resumos_brutos: list[dict] = []
    placa_atual: str | None = None

    for _, row in raw.iterrows():
        cel0 = _norm_txt(row[0]).upper()
        is_placa = bool(re.match(r"^EH[LH]\d", cel0))

        if "GERAL" in str(row[5]).upper() and "=" in str(row[5]):
            placa_resumo = cel0 if is_placa else placa_atual
            if placa_resumo:
                resumos_brutos.append(
                    {
                        "placa": placa_resumo,
                        "media_geral_col_g_planilha_bruta": parse_numero_br(row[6]),
                    }
                )
            continue

        if is_placa and pd.isna(row[1]):
            placa_atual = cel0
            continue

        placa = cel0 if is_placa and pd.notna(row[1]) else placa_atual
        if not placa or not re.match(r"^EH[LH]\d", placa) or pd.isna(row[1]):
            continue

        horas = parse_horas_trabalhadas(row[5])
        volume = parse_numero_br(row[2])
        custo = parse_numero_br(row[3])
        media_col_g = parse_numero_br(row[6])
        ref_min, ref_max = parse_numero_br(row[7]), parse_numero_br(row[8])
        media_tratada, media_zerada, motivo_zero = tratar_media_col_g(media_col_g)

        consumo_calc = volume / horas if volume and horas and horas > 0 else None

        abastecimentos.append(
            {
                "placa": placa,
                "marca": inferir_marca_pela_placa(placa),
                "data_abastecimento": pd.to_datetime(row[1], dayfirst=True, errors="coerce"),
                "volume_litros": volume,
                "custo_abastecimento": custo,
                "horimetro": parse_numero_br(row[4]),
                "horas_trabalhadas": horas,
                "media_lh_col_g": media_col_g,
                "media_lh_col_g_tratada": media_tratada,
                "media_col_g_zerada": media_zerada,
                "motivo_zeragem_col_g": motivo_zero if media_zerada else "",
                "media_lh_vol_horas": consumo_calc,
                "ref_min_lh": ref_min,
                "ref_max_lh": ref_max,
            }
        )

    det = pd.DataFrame(abastecimentos)
    if det.empty:
        return det, pd.DataFrame(), pd.DataFrame()

    det = det.sort_values(["placa", "data_abastecimento"])

    if resumos_brutos:
        res_planilha = (
            pd.DataFrame(resumos_brutos)
            .dropna(subset=["placa"])
            .drop_duplicates(subset=["placa"], keep="last")
        )
    else:
        res_planilha = pd.DataFrame(columns=["placa", "media_geral_col_g_planilha_bruta"])

    def _agg_placa(g: pd.DataFrame) -> pd.Series:
        g_validos = g[g["media_lh_col_g_tratada"].fillna(0) > 0]
        return pd.Series(
            {
                "marca": g["marca"].iloc[0],
                "qtd_abastecimentos": len(g),
                "qtd_medias_col_g_zeradas": int(g["media_col_g_zerada"].sum()),
                "qtd_medias_col_g_validas": len(g_validos),
                "volume_total_litros": g["volume_litros"].sum(),
                "custo_total_abastecimento": g["custo_abastecimento"].sum(),
                "horas_totais_registradas": g["horas_trabalhadas"].sum(),
                "data_primeiro_abast": g["data_abastecimento"].min(),
                "data_ultimo_abast": g["data_abastecimento"].max(),
                "media_geral_lh_tratada": g_validos["media_lh_col_g_tratada"].mean()
                if len(g_validos)
                else None,
                "media_geral_lh_bruta": g["media_lh_col_g"].dropna().mean()
                if g["media_lh_col_g"].notna().any()
                else None,
            }
        )

    res_placa = (
        det.groupby("placa", as_index=False)
        .apply(_agg_placa, include_groups=False)
        .reset_index(drop=True)
        .merge(res_planilha, on="placa", how="left")
    )
    res_placa["delta_media_tratada_vs_planilha"] = (
        res_placa["media_geral_lh_tratada"] - res_placa["media_geral_col_g_planilha_bruta"]
    )
    res_placa = res_placa.sort_values("placa")

    resumo_geral = pd.DataFrame(
        [
            {
                "placas_com_abastecimento": res_placa["placa"].nunique(),
                "placas_com_media_tratada": int((res_placa["qtd_medias_col_g_validas"].fillna(0) > 0).sum()),
                "total_abastecimentos": len(det),
                "medias_col_g_zeradas": int(det["media_col_g_zerada"].sum()),
                "volume_total_litros": det["volume_litros"].sum(),
                "custo_total": det["custo_abastecimento"].sum(),
                "media_lh_tratada_ponderada_placas": res_placa["media_geral_lh_tratada"].mean(),
                "criterio_zeragem": f"col. G zerada se < {LH_MIN_COL_G} ou > {LH_MAX_COL_G} L/h",
                "fonte": xlsx_path.name,
            }
        ]
    )

    return det, res_placa, resumo_geral
