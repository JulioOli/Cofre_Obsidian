"""Gera figuras faltantes e copia para ./figuras/ (caminho local do LaTeX)."""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "outputs" / "relatorios" / "comparativo_liebherr_hyundai") not in sys.path:
    sys.path.insert(0, str(ROOT / "outputs" / "relatorios" / "comparativo_liebherr_hyundai"))

from export_dashboard_excel import (  # noqa: E402
    CONTAS_ANALISE,
    PARQUE,
    QTD_PARQUE,
    carregar_df_maq,
    meses_analisados,
    meses_totais_periodo,
)

OUT_DIR = Path(__file__).resolve().parent
FIG_SRC = ROOT / "outputs" / "figuras" / "liebherr_hyundai"
FIG_LOCAL = OUT_DIR / "figuras"

CORES = {"LIEBHERR": "#F4C430", "HYUNDAI": "#004B8D"}
MARCAS = ["LIEBHERR", "HYUNDAI"]
YLABEL_MAQ = "R$ médio / máquina"

ROTULOS_CONTA = {
    "7.1.1": "7.1.1 Peças de manutenção",
    "7.1.18": "7.1.18 Fretes e carretos",
    "7.1.2": "7.1.2 Manutenção veíc./máq.",
    "7.1.22": "7.1.22 Diesel (interno)",
    "7.1.4": "7.1.4 Diesel (posto)",
}

# Arquivos referenciados em main.tex
REQUERIDOS = [
    "01_volume_por_ano.png",
    "02_mix_contas_pct.png",
    "03_volume_por_conta.png",
    "04_serie_mensal_2025.png",
    "04_serie_mensal_2026.png",
    "05_top_maquinas.png",
    "05_top_maquinas_2025.png",
    "05_top_maquinas_2026.png",
    "09_mes_maquinas_liebherr.png",
    "09_mes_maquinas_hyundai.png",
]

ALIASES = {
    "01_volume_por_ano.png": "07_custo_medio_maquina.png",
}


def carregar_df() -> tuple[pd.DataFrame, pd.DataFrame]:
    df_maq = carregar_df_maq()
    return df_maq, df_maq.copy()


def ranking_maquinas_parque(df_maq: pd.DataFrame, ano: int | None = None) -> pd.DataFrame:
    sub = df_maq if ano is None else df_maq[df_maq["ano_nf"] == ano]
    agg = (
        sub.groupby(["MARCA", "maq_id"], observed=True)["gasto_abs"]
        .sum()
        .reset_index(name="volume")
    )
    rows: list[dict] = []
    for marca in MARCAS:
        for mid in PARQUE.get(marca, []):
            v = agg.loc[(agg["MARCA"] == marca) & (agg["maq_id"] == mid), "volume"]
            row = {"MARCA": marca, "maq_id": mid, "volume": float(v.iloc[0]) if len(v) else 0.0}
            if ano is not None:
                row["ano_nf"] = int(ano)
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["MARCA", "volume"], ascending=[True, False])


def plot_maquinas_parque(df_rank: pd.DataFrame, sufixo: str, outfile: Path, marcas_ord: list[str]) -> None:
    max_maq_parque = max(QTD_PARQUE[m] for m in marcas_ord)
    fig_h = max(6, max_maq_parque * 0.38)
    fig, axes = plt.subplots(1, len(marcas_ord), figsize=(6 * len(marcas_ord), fig_h), squeeze=False)
    for ax, marca in zip(axes[0], marcas_ord):
        top = df_rank[df_rank["MARCA"] == marca].head(16)
        ax.barh(top["maq_id"].astype(str), top["volume"], color=CORES[marca])
        ax.invert_yaxis()
        ax.set_title(f"Máquinas do parque — {marca}\n{sufixo} ({len(top)} máq.)")
        ax.set_xlabel("R$")
    plt.tight_layout()
    fig.savefig(outfile, dpi=130)
    plt.close(fig)


def rotulo_conta_grafico(cod: str, conta: str) -> str:
    cod = str(cod).strip()
    if cod in ROTULOS_CONTA:
        return ROTULOS_CONTA[cod]
    return f"{cod} {str(conta)[:35]}"


def gerar_figuras(df: pd.DataFrame, df_maq: pd.DataFrame) -> None:
    FIG_SRC.mkdir(parents=True, exist_ok=True)
    marcas_ord = MARCAS

    por_ano_vol_maq = (
        df_maq.groupby(["MARCA", "ano_nf"])["gasto_abs"].sum().reset_index(name="volume_parque")
    )
    por_ano_vol_maq["parque"] = por_ano_vol_maq["MARCA"].map(QTD_PARQUE)
    por_ano_vol_maq["meses_ano"] = por_ano_vol_maq["ano_nf"].map(meses_analisados)
    por_ano_vol_maq["custo_por_maquina_parque"] = (
        por_ano_vol_maq["volume_parque"]
        / por_ano_vol_maq["parque"]
        / por_ano_vol_maq["meses_ano"]
    )

    anos_ord = sorted(por_ano_vol_maq["ano_nf"].dropna().unique())
    piv_ano_maq = por_ano_vol_maq.pivot(
        index="ano_nf", columns="MARCA", values="custo_por_maquina_parque"
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(anos_ord))
    w = 0.35
    for i, m in enumerate(marcas_ord):
        if m not in piv_ano_maq.columns:
            continue
        vals = piv_ano_maq.loc[anos_ord, m].values
        bars = ax.bar(
            x + i * w,
            vals,
            width=w,
            label=f"{m} ({QTD_PARQUE[m]} máq.)",
            color=CORES[m],
            edgecolor="#333",
        )
        for b, v in zip(bars, vals):
            if v > 0:
                ax.text(
                    b.get_x() + b.get_width() / 2,
                    b.get_height(),
                    f"R${v/1e3:.0f}k",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )
    ax.set_xticks(x + w / 2)
    ax.set_xticklabels([str(int(a)) for a in anos_ord])
    ax.set_title("Custo médio mensal por máquina do parque — por ano")
    ax.set_ylabel(YLABEL_MAQ)
    ax.legend(fontsize=8)
    plt.tight_layout()
    fig.savefig(FIG_SRC / "01_volume_por_ano.png", dpi=130)
    plt.close(fig)

    por_conta = (
        df_maq.groupby(["MARCA", "cod_conta", "conta"], observed=True)["gasto_abs"]
        .sum()
        .reset_index(name="volume")
    )
    por_conta["volume_por_maq"] = (
        por_conta["volume"]
        / por_conta["MARCA"].map(QTD_PARQUE)
        / meses_totais_periodo(df_maq)
    )

    top_contas = (
        por_conta.groupby("conta", observed=True)["volume"].sum().nlargest(6).index.tolist()
    )
    comp = por_conta[por_conta["conta"].isin(top_contas)].copy()
    comp["conta_curta"] = comp.apply(
        lambda r: rotulo_conta_grafico(r["cod_conta"], r["conta"]), axis=1
    )

    pivot_comp = comp.pivot(index="conta_curta", columns="MARCA", values="volume").fillna(0)
    pivot_pct = pivot_comp.div(pivot_comp.sum(axis=0), axis=1) * 100
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(pivot_pct))
    w = 0.35
    for i, m in enumerate(marcas_ord):
        if m in pivot_pct.columns:
            ax.bar(x + i * w, pivot_pct[m].values, width=w, label=m, color=CORES[m])
    ax.set_xticks(x + w / 2)
    ax.set_xticklabels(pivot_pct.index, rotation=35, ha="right")
    ax.set_ylabel("% do volume da marca")
    ax.set_title("Mix de gastos por tipo de conta (top 6 rubricas)")
    ax.legend()
    plt.tight_layout()
    fig.savefig(FIG_SRC / "02_mix_contas_pct.png", dpi=130)
    plt.close(fig)

    pivot_vol = comp.pivot(index="conta_curta", columns="MARCA", values="volume_por_maq").fillna(0)
    fig, ax = plt.subplots(figsize=(11, 6))
    pivot_vol.plot(kind="barh", ax=ax, color=[CORES.get(m) for m in pivot_vol.columns])
    ax.set_title("Gasto por conta — custo médio por máquina")
    ax.set_xlabel(YLABEL_MAQ)
    ax.legend(title="Marca")
    plt.tight_layout()
    fig.savefig(FIG_SRC / "03_volume_por_conta.png", dpi=130)
    plt.close(fig)

    por_mes = (
        df_maq.groupby(["mes_nf", "MARCA", "ano_nf"], observed=True)["gasto_abs"]
        .sum()
        .reset_index(name="volume")
    )
    por_mes["volume_por_maq"] = por_mes["volume"] / por_mes["MARCA"].map(QTD_PARQUE)

    for ano in anos_ord:
        sub = por_mes[por_mes["ano_nf"] == ano]
        piv = sub.pivot(index="mes_nf", columns="MARCA", values="volume_por_maq").fillna(0)
        fig, ax = plt.subplots(figsize=(10, 4.5))
        for m in marcas_ord:
            if m in piv.columns:
                ax.plot(
                    piv.index.astype(str),
                    piv[m],
                    marker="o",
                    label=f"{m} ({QTD_PARQUE[m]} máq.)",
                    color=CORES[m],
                    lw=2,
                )
        ax.set_title(f"Custo médio mensal por máquina — {int(ano)}")
        ax.set_ylabel(YLABEL_MAQ)
        ax.tick_params(axis="x", rotation=45)
        ax.legend(fontsize=8)
        plt.tight_layout()
        fig.savefig(FIG_SRC / f"04_serie_mensal_{int(ano)}.png", dpi=130)
        plt.close(fig)

    ranking_geral = ranking_maquinas_parque(df_maq)
    plot_maquinas_parque(ranking_geral, "período completo", FIG_SRC / "05_top_maquinas.png", marcas_ord)
    for ano in anos_ord:
        rank_ano = ranking_maquinas_parque(df_maq, ano=int(ano))
        plot_maquinas_parque(rank_ano, str(int(ano)), FIG_SRC / f"05_top_maquinas_{int(ano)}.png", marcas_ord)

    por_maquina = ranking_geral.copy()

    por_maquina_mes = (
        df_maq.groupby(["MARCA", "maq_id", "mes_nf"])["gasto_abs"].sum().reset_index(name="volume")
    )
    for marca in marcas_ord:
        ids_parque = PARQUE.get(marca, [])
        sub = por_maquina_mes[por_maquina_mes["MARCA"] == marca]
        if sub.empty:
            continue
        piv = (
            sub.pivot(index="mes_nf", columns="maq_id", values="volume")
            .reindex(columns=ids_parque)
            .fillna(0)
            .sort_index()
        )
        n_maq = len(ids_parque)
        fig_h = 7 if n_maq > 10 else 5.5
        fig, ax = plt.subplots(figsize=(14, fig_h))
        for col in piv.columns:
            ax.plot(piv.index.astype(str), piv[col], marker="o", markersize=3, label=col, lw=1.2)
        ax.set_title(
            f"Gasto mensal — parque completo {marca} ({n_maq} máq.)"
        )
        ax.set_ylabel("R$")
        ax.tick_params(axis="x", rotation=45)
        ax.legend(
            fontsize=7,
            ncol=min(4, max(2, (n_maq + 3) // 4)),
            loc="upper center",
            bbox_to_anchor=(0.5, -0.22),
            frameon=False,
        )
        plt.tight_layout()
        fig.savefig(FIG_SRC / f"09_mes_maquinas_{marca.lower()}.png", dpi=130, bbox_inches="tight")
        plt.close(fig)


def copiar_para_local() -> list[str]:
    FIG_LOCAL.mkdir(parents=True, exist_ok=True)
    faltando: list[str] = []
    for nome in REQUERIDOS:
        src = FIG_SRC / nome
        if not src.exists() and nome in ALIASES:
            alt = FIG_SRC / ALIASES[nome]
            if alt.exists():
                src = alt
        if not src.exists():
            faltando.append(nome)
            continue
        shutil.copy2(src, FIG_LOCAL / nome)
    return faltando


def sincronizar(gerar: bool = True) -> None:
    if gerar:
        df, df_maq = carregar_df()
        gerar_figuras(df, df_maq)
    faltando = copiar_para_local()
    if faltando:
        raise FileNotFoundError(f"Figuras ainda ausentes: {faltando}")
    print(f"Figuras OK em: {FIG_LOCAL.resolve()} ({len(REQUERIDOS)} arquivos)")


if __name__ == "__main__":
    sincronizar(gerar=True)
