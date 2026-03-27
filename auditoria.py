"""
Auditoria de Lancamentos Incorretos — G3S / Cofre Trabalho
===========================================================
Executa as 8 regras de deteccao definidas no .cursorrules contra o base.csv
e gera um relatorio Markdown em 02-Referencias/.

Uso:
    python auditoria.py                    # auditoria completa
    python auditoria.py --mes 03/2026      # filtrar por mes de vencimento
    python auditoria.py --apenas-alta      # somente severidade ALTA
    python auditoria.py --saida meu.md     # nome customizado para o relatorio

Para adicionar uma nova regra:
    1. Defina a funcao regra_N(df) -> list[dict] seguindo o contrato padrao
    2. Registre-a em REGRAS com id, descricao e severidade padrao
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

# ---------------------------------------------------------------------------
# Configuracao
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "02-Referencias" / "base.csv"
OUTPUT_DIR = BASE_DIR / "02-Referencias"
CSV_ENCODING = "latin-1"
VALOR_ALTO = 100_000.0

# Cores ANSI para terminal (desativadas em ambientes sem suporte)
_USE_COLOR = sys.stdout.isatty()
VERMELHO = "\033[31m" if _USE_COLOR else ""
AMARELO  = "\033[33m" if _USE_COLOR else ""
VERDE    = "\033[32m" if _USE_COLOR else ""
NEGRITO  = "\033[1m"  if _USE_COLOR else ""
RESET    = "\033[0m"  if _USE_COLOR else ""

SEV_CORES = {"ALTA": VERMELHO, "MEDIA": AMARELO, "BAIXA": VERDE}
SEV_EMOJI = {"ALTA": "🔴", "MEDIA": "🟡", "BAIXA": "🟢"}
SEV_SIGLA = {"ALTA": "[!]", "MEDIA": "[~]", "BAIXA": "[i]"}

# ---------------------------------------------------------------------------
# Carga e limpeza da base
# ---------------------------------------------------------------------------

def carregar_base(mes: str | None = None) -> pd.DataFrame:
    """
    Le o base.csv e retorna um DataFrame limpo.

    Args:
        mes: Periodo no formato 'MM/AAAA'. Quando informado, filtra registros
             cujo campo ite_pagrec_vencimento pertence ao mes/ano indicado.
             Exemplo: '03/2026'

    Returns:
        DataFrame com coluna auxiliar `valor_num` (float) alem das originais.
    """
    tmp = Path(os.environ.get("TEMP", "/tmp")) / "base_auditoria.csv"
    shutil.copy2(CSV_PATH, tmp)
    df = pd.read_csv(tmp, delimiter=";", encoding=CSV_ENCODING, dtype=str)

    # Coluna auxiliar numerica
    df["valor_num"] = pd.to_numeric(
        df["valor_bruto"].str.replace(",", ".", regex=False), errors="coerce"
    )

    # Filtro de periodo opcional
    if mes:
        mes_num, ano = mes.strip().split("/")
        prefixo = f"{ano}-{mes_num}"
        df = df[df["ite_pagrec_vencimento"].str.startswith(prefixo, na=False)]

    return df


def _achado(
    *,
    regra: str,
    severidade: str,
    documento: str,
    filial: str,
    codcdc: str,
    descdc: str,
    codcen: str,
    valor_bruto: str,
    vencimento: str,
    evidencia: str,
    correcao: str,
    valor_num: float = 0.0,
) -> dict[str, Any]:
    """Fabrica um dicionario de achado com schema padrao."""
    return {
        "regra": regra,
        "severidade": severidade,
        "documento": documento,
        "filial": filial,
        "codcdc": codcdc,
        "descdc": descdc,
        "codcen": codcen,
        "valor_bruto": valor_bruto,
        "vencimento": vencimento,
        "evidencia": evidencia,
        "correcao": correcao,
        "valor_num": valor_num,
    }


def _rows_to_achados(
    rows: pd.DataFrame,
    regra: str,
    severidade: str,
    evidencia: str,
    correcao: str,
) -> list[dict]:
    """Converte linhas do DataFrame em lista de achados usando o schema padrao."""
    result = []
    for _, r in rows.iterrows():
        result.append(
            _achado(
                regra=regra,
                severidade=severidade,
                documento=str(r.get("documento", "")),
                filial=str(r.get("filial", "")),
                codcdc=str(r.get("codcdc", "")),
                descdc=str(r.get("descdc", "")),
                codcen=str(r.get("codcen", "")),
                valor_bruto=str(r.get("valor_bruto", "")),
                vencimento=str(r.get("ite_pagrec_vencimento", "")),
                evidencia=evidencia,
                correcao=correcao,
                valor_num=float(r.get("valor_num", 0) or 0),
            )
        )
    return result


# ---------------------------------------------------------------------------
# Regras de deteccao
# ---------------------------------------------------------------------------

def regra_1(df: pd.DataFrame) -> list[dict]:
    """
    Tipo de documento incompativel com a conta.

    - ADT em 4.1.1 (deve ser 4.2.1)
    - DEV.BOLV fora de 4.3.x (deve ser 4.3.1)
    - BOLV fora de 4.1.1 (deve ser 4.1.1)
    """
    achados: list[dict] = []

    # 1a: ADT em 4.1.1
    mask = df["documento"].str.startswith("ADT", na=False) & (df["codcdc"] == "4.1.1")
    achados += _rows_to_achados(
        df[mask],
        regra="R1a — ADT em 4.1.1",
        severidade="ALTA",
        evidencia="Prefixo ADT indica adiantamento; conta correta e 4.2.1",
        correcao="Trocar conta 4.1.1 -> 4.2.1 via Troca de Plano de Contas em Lote no SAGI",
    )

    # 1b: DEV.BOLV fora de 4.3.x
    mask = df["documento"].str.startswith("DEV.BOLV", na=False) & ~df["codcdc"].str.startswith("4.3", na=False)
    achados += _rows_to_achados(
        df[mask],
        regra="R1b — DEV.BOLV fora de 4.3.x",
        severidade="ALTA",
        evidencia="Prefixo DEV.BOLV indica devolucao de venda; conta correta e 4.3.1",
        correcao="Trocar conta para 4.3.1 via Troca em Lote no SAGI",
    )

    # 1c: BOLV fora de 4.1.1
    mask = df["documento"].str.startswith("BOLV", na=False) & (df["codcdc"] != "4.1.1")
    achados += _rows_to_achados(
        df[mask],
        regra="R1c — BOLV fora de 4.1.1",
        severidade="ALTA",
        evidencia="Prefixo BOLV indica boleto de venda; conta correta e 4.1.1",
        correcao="Trocar conta para 4.1.1 via Troca em Lote no SAGI",
    )

    return achados


def regra_2(df: pd.DataFrame) -> list[dict]:
    """
    Conta incompativel com a natureza do CC (D/R invertidos).

    - Despesa (6-9.x) em CC de Receita (2.x) — exceto ADTs de compra em CC comercial
    - Receita (4-5.x) em CC de Despesa (1.x)

    ADTs de compra (6.1.1) em CCs 2.x sao padrao do sistema e ignorados aqui.
    """
    achados: list[dict] = []

    # 2a: despesa em CC receita
    mask_2a = (
        df["codcen"].str.startswith("2.", na=False)
        & df["codcdc"].str.match(r"^[6789]\.", na=False)
    )
    # excluir ADTs de compra que sao padrao do sistema (6.1.1 em 2.x com doc ADT)
    excluir = (
        df["documento"].str.startswith("ADT", na=False)
        & (df["codcdc"] == "6.1.1")
    )
    candidatos_2a = df[mask_2a & ~excluir]
    achados += _rows_to_achados(
        candidatos_2a,
        regra="R2a — Despesa em CC Receita",
        severidade="MEDIA",
        evidencia="Conta de despesa (6-9.x) lancada em CC de Receita (2.x)",
        correcao="Trocar CC para o equivalente de Despesa (1.x mesmo nivel)",
    )

    # 2b: receita em CC despesa
    mask_2b = (
        df["codcen"].str.startswith("1.", na=False)
        & df["codcdc"].str.match(r"^[45]\.", na=False)
    )
    achados += _rows_to_achados(
        df[mask_2b],
        regra="R2b — Receita em CC Despesa",
        severidade="MEDIA",
        evidencia="Conta de receita (4-5.x) lancada em CC de Despesa (1.x)",
        correcao="Trocar CC para o equivalente de Receita (2.x mesmo nivel)",
    )

    return achados


def regra_3(df: pd.DataFrame) -> list[dict]:
    """
    Registros duplicados: mesmo documento + filial + valor + data de vencimento.

    Destaca especialmente quando os CCs duplicados sao diferentes (mais grave).
    """
    chaves = ["documento", "filial", "valor_bruto", "ite_pagrec_vencimento"]
    mask_dup = df.duplicated(subset=chaves, keep=False)
    duplicatas = df[mask_dup].sort_values(chaves)

    achados: list[dict] = []
    for _nome, grupo in duplicatas.groupby(chaves, sort=False):
        ccs_distintos = grupo["codcen"].nunique()
        sev = "ALTA" if ccs_distintos == 1 else "ALTA"  # ambos sao alta
        evidencia = (
            f"Aparece {len(grupo)}x com mesmo doc+filial+valor+data"
            + (f" — CCs DIFERENTES ({', '.join(grupo['codcen'].unique())})" if ccs_distintos > 1 else f" — mesmo CC ({grupo['codcen'].iloc[0]})")
        )
        correcao = (
            "Verificar qual lancamento e legitimo e estornar os demais; "
            "escalar para o gestor antes de qualquer acao se valor > R$100.000"
        )
        achados += _rows_to_achados(
            grupo,
            regra="R3 — Duplicata",
            severidade=sev,
            evidencia=evidencia,
            correcao=correcao,
        )

    return achados


def regra_4(df: pd.DataFrame) -> list[dict]:
    """
    Multi-lancamento suspeito de ADT: mesmo valor + filial + data com 2+ ocorrencias.

    Detecta ADTs que provavelmente representam o mesmo adiantamento lancado
    mais de uma vez com numeros de documento levemente diferentes.
    """
    adts = df[df["documento"].str.startswith("ADT", na=False)]
    grupos_chave = ["filial", "valor_bruto", "ite_pagrec_vencimento"]
    achados: list[dict] = []

    for _nome, grupo in adts.groupby(grupos_chave, sort=False):
        if len(grupo) < 2:
            continue
        docs = " / ".join(grupo["documento"].tolist())
        evidencia = (
            f"ADT aparece {len(grupo)}x com mesmo valor+filial+data — "
            f"documentos: {docs}"
        )
        correcao = (
            "Confirmar qual ADT e o correto; estornar os extras com novo "
            "lancamento correto; escalar para o gestor antes de qualquer acao"
        )
        achados += _rows_to_achados(
            grupo,
            regra="R4 — ADT Multi-lancamento",
            severidade="ALTA",
            evidencia=evidencia,
            correcao=correcao,
        )

    return achados


def regra_5(df: pd.DataFrame) -> list[dict]:
    """
    Conta de legado/migracao usada em lancamentos recentes (ultimos 90 dias).

    Contas do grupo 1 (ex: 1.35.43) sao de migracao e nao devem ser
    usadas em novos lancamentos.
    """
    referencia = (date.today() - timedelta(days=90)).strftime("%Y-%m-%d")
    recentes = df[df["ite_pagrec_vencimento"] >= referencia]
    contas_legado = recentes[
        recentes["codcdc"].str.match(r"^1\.", na=False)
        & ~recentes["codcdc"].str.match(r"^1\.(2|3|4|5|6|7|8|9)\.", na=False)
    ]

    return _rows_to_achados(
        contas_legado,
        regra="R5 — Conta Legado",
        severidade="BAIXA",
        evidencia="Conta do grupo 1 (legado/migracao) usada em lancamento recente",
        correcao="Substituir pela conta correta no Plano de Contas vigente; ex: 1.35.43 -> 5.4.8",
    )


def regra_6(df: pd.DataFrame) -> list[dict]:
    """
    Pesagem avulsa potencialmente lancada como venda (4.1.1).

    Documentos com prefixo 'B-' ou sem prefixo BOLV, com valor < R$5.000,
    em 4.1.1 inflariam a receita de vendas de sucata.
    """
    mask = (
        (df["codcdc"] == "4.1.1")
        & ~df["documento"].str.startswith("BOLV", na=False)
        & (df["valor_num"] < 5_000)
    )
    return _rows_to_achados(
        df[mask],
        regra="R6 — Pesagem em 4.1.1",
        severidade="MEDIA",
        evidencia="Nao-BOLV em 4.1.1 com valor < R$5.000 (possivel pesagem avulsa)",
        correcao="Confirmar se e pesagem; se sim, trocar conta 4.1.1 -> 5.4.3 (PESAGENS AVULSAS) em Lote",
    )


def regra_7(df: pd.DataFrame) -> list[dict]:
    """
    Manutenção de veiculos/maquinas (7.1.2) em CC de departamento generico.

    Deve estar no CC do ativo (nivel 5, ex: 1.2.5.6.7).
    CCs de nivel 4 terminando em .2/.3/.4/.5 sao departamentos genericos
    (Comercial, Operacional, Logistica, Prensa) — nao permitem rastrear TCO.
    """
    mask = (
        (df["codcdc"] == "7.1.2")
        & df["codcen"].str.match(r"^\d+\.\d+\.\d+\.[2-5]$", na=False)
    )
    return _rows_to_achados(
        df[mask],
        regra="R7 — Manutencao em CC Generico",
        severidade="MEDIA",
        evidencia="Conta 7.1.2 em CC de departamento (nivel 4) em vez de CC do ativo (nivel 5)",
        correcao="Trocar CC para o ativo especifico (placa/codigo da maquina) via Troca em Lote",
    )


def regra_8(df: pd.DataFrame) -> list[dict]:
    """
    Locacao de maquinas (5.6.1 ou 7.1.3) em CC de filial Seletiva.

    Essas contas devem ocorrer em CCs da Ekipa (1.6.x, 1.7.x) ou
    em clientes externos. Em 1.2.x / 2.2.x exige investigacao.
    """
    mask = df["codcdc"].isin(["5.6.1", "7.1.3"]) & (
        df["codcen"].str.startswith("1.2.", na=False)
        | df["codcen"].str.startswith("2.2.", na=False)
    )
    return _rows_to_achados(
        df[mask],
        regra="R8 — Locacao em Seletiva",
        severidade="BAIXA",
        evidencia="Conta 5.6.1/7.1.3 em CC da Seletiva (sem contrato de locacao esperado)",
        correcao="Verificar se ha contrato formal; se nao, reclassificar para CC correto da Ekipa (1.6.x/1.7.x)",
    )


# ---------------------------------------------------------------------------
# Catalogo de regras
# (Para adicionar nova regra: inclua uma entrada nesta lista)
# ---------------------------------------------------------------------------

REGRAS: list[dict[str, Any]] = [
    {"fn": regra_1, "id": "R1"},
    {"fn": regra_2, "id": "R2"},
    {"fn": regra_3, "id": "R3"},
    {"fn": regra_4, "id": "R4"},
    {"fn": regra_5, "id": "R5"},
    {"fn": regra_6, "id": "R6"},
    {"fn": regra_7, "id": "R7"},
    {"fn": regra_8, "id": "R8"},
]


# ---------------------------------------------------------------------------
# Motor de auditoria
# ---------------------------------------------------------------------------

def _elevar_severidade(achados: list[dict]) -> list[dict]:
    """Eleva para ALTA qualquer achado com valor_num > VALOR_ALTO."""
    for a in achados:
        if a["valor_num"] > VALOR_ALTO and a["severidade"] != "ALTA":
            a["severidade"] = "ALTA"
            a["evidencia"] += f" [ALTO VALOR > R${VALOR_ALTO:,.0f}]"
    return achados


def executar_auditoria(df: pd.DataFrame) -> pd.DataFrame:
    """
    Executa todas as regras registradas e retorna DataFrame consolidado.

    O DataFrame resultado tem as colunas do schema padrao de achados,
    ordenado por severidade (ALTA -> MEDIA -> BAIXA) e valor decrescente.
    """
    todos: list[dict] = []
    for regra_cfg in REGRAS:
        fn = regra_cfg["fn"]
        try:
            achados = fn(df)
            todos.extend(achados)
        except Exception as exc:  # noqa: BLE001
            print(f"{AMARELO}[AVISO] {fn.__name__} falhou: {exc}{RESET}")

    if not todos:
        return pd.DataFrame()

    resultado = pd.DataFrame(todos)
    _elevar_severidade(resultado.to_dict("records"))  # in-place via lista
    resultado = pd.DataFrame(todos)  # rebuild apos elevacao

    ordem_sev = {"ALTA": 0, "MEDIA": 1, "BAIXA": 2}
    resultado["_ord_sev"] = resultado["severidade"].map(ordem_sev).fillna(9)
    resultado = resultado.sort_values(
        ["_ord_sev", "valor_num"], ascending=[True, False]
    ).drop(columns=["_ord_sev"])

    return resultado.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Gerador de relatorio Markdown
# ---------------------------------------------------------------------------

def _fmt_valor(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _tabela_md(rows: pd.DataFrame, colunas: list[str]) -> str:
    """Gera tabela Markdown a partir de um subset de colunas."""
    header = "| " + " | ".join(colunas) + " |"
    sep    = "| " + " | ".join(["---"] * len(colunas)) + " |"
    linhas = [header, sep]
    for _, r in rows.iterrows():
        cells = []
        for c in colunas:
            val = str(r.get(c, "")).replace("|", "\\|")
            cells.append(val)
        linhas.append("| " + " | ".join(cells) + " |")
    return "\n".join(linhas)


def gerar_relatorio(
    resultado: pd.DataFrame,
    df_base: pd.DataFrame,
    mes: str | None,
    apenas_alta: bool,
    caminho_saida: Path,
) -> None:
    """Gera o arquivo Markdown de relatorio de auditoria."""
    hoje = date.today().strftime("%d/%m/%Y")
    periodo_label = f"Mes {mes}" if mes else "Base completa"

    linhas: list[str] = []

    # Cabecalho
    linhas += [
        f"# Relatorio de Auditoria de Lancamentos",
        f"",
        f"**Data:** {hoje}  ",
        f"**Periodo analisado:** {periodo_label}  ",
        f"**Total de registros na base:** {len(df_base):,}  ",
        f"**Total de achados:** {len(resultado):,}  ",
        f"",
        "---",
        "",
    ]

    if resultado.empty:
        linhas.append("> Nenhum achado encontrado para os criterios selecionados.")
        caminho_saida.write_text("\n".join(linhas), encoding="utf-8")
        return

    # Resumo executivo
    linhas.append("## Resumo Executivo")
    linhas.append("")

    por_sev = resultado.groupby("severidade")
    tabela_res: list[str] = ["| Severidade | Achados | Impacto estimado (valor total) |",
                              "|---|---|---|"]
    for sev in ["ALTA", "MEDIA", "BAIXA"]:
        if sev in por_sev.groups:
            g = por_sev.get_group(sev)
            total_val = g["valor_num"].sum()
            emoji = SEV_EMOJI.get(sev, "")
            tabela_res.append(f"| {emoji} {sev} | {len(g)} | {_fmt_valor(total_val)} |")
    linhas += tabela_res
    linhas += ["", "---", ""]

    # Detalhamento por regra
    colunas_tabela = ["documento", "filial", "codcdc", "codcen", "valor_bruto", "vencimento"]

    for regra_id in resultado["regra"].unique():
        grupo = resultado[resultado["regra"] == regra_id]
        if apenas_alta and grupo["severidade"].iloc[0] != "ALTA":
            continue

        sev = grupo["severidade"].iloc[0]
        emoji = SEV_EMOJI.get(sev, "")
        evidencia_ex = grupo["evidencia"].iloc[0]
        correcao_ex  = grupo["correcao"].iloc[0]

        linhas += [
            f"### {emoji} {regra_id}",
            "",
            f"**Severidade:** {sev}  ",
            f"**Total de achados:** {len(grupo)}  ",
            f"**Evidencia:** {evidencia_ex}  ",
            f"**Correcao sugerida:** {correcao_ex}  ",
            "",
        ]

        # Para R3 e R4, agrupa por grupo de duplicata para melhor leitura
        if regra_id.startswith("R3") or regra_id.startswith("R4"):
            for _, g_dup in grupo.groupby(
                ["filial", "valor_bruto", "vencimento"], sort=False
            ):
                docs = " / ".join(g_dup["documento"].tolist())
                linhas.append(
                    f"- **{len(g_dup)}x** | filial: `{g_dup['filial'].iloc[0]}` "
                    f"| valor: `{g_dup['valor_bruto'].iloc[0]}` "
                    f"| venc: `{g_dup['vencimento'].iloc[0]}` "
                    f"| docs: `{docs}`"
                )
                for _, row in g_dup.iterrows():
                    linhas.append(
                        f"  - cc: `{row['codcen']}` conta: `{row['codcdc']}` ({row['descdc']})"
                    )
            linhas.append("")
        else:
            # Limitar tabela a 100 linhas para nao poluir o relatorio
            amostrar = grupo.head(100)
            linhas.append(_tabela_md(amostrar, colunas_tabela))
            if len(grupo) > 100:
                linhas.append(f"")
                linhas.append(f"> *(... e mais {len(grupo) - 100} achados nao exibidos)*")
            linhas.append("")

        linhas += ["---", ""]

    # Rodape
    linhas += [
        "## Instrucoes Gerais de Correcao no SAGI",
        "",
        "- **Troca de Plano de Contas em Lote:** Menu financeiro > Troca de Conta > selecionar "
        "periodo e conta incorreta, escolher conta correta.",
        "- **Troca de CC em Lote:** Menu financeiro > Troca de CC > mesmo procedimento.",
        "- **Nunca excluir diretamente** — sempre estornar com novo lancamento correto.",
        "- **ADTs duplicados/triplicados:** escalar para o gestor antes de qualquer estorno.",
        "",
        f"*Relatorio gerado automaticamente por `auditoria.py` em {hoje}.*",
    ]

    caminho_saida.write_text("\n".join(linhas), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_resumo_terminal(resultado: pd.DataFrame, caminho_saida: Path) -> None:
    """Imprime um resumo colorido no terminal."""
    print()
    print(f"{NEGRITO}{'='*60}{RESET}")
    print(f"{NEGRITO}  AUDITORIA DE LANCAMENTOS — RESUMO{RESET}")
    print(f"{NEGRITO}{'='*60}{RESET}")

    if resultado.empty:
        print(f"  {VERDE}Nenhum achado encontrado.{RESET}")
    else:
        for sev in ["ALTA", "MEDIA", "BAIXA"]:
            cor = SEV_CORES.get(sev, "")
            sigla = SEV_SIGLA.get(sev, "")
            grupo = resultado[resultado["severidade"] == sev]
            if grupo.empty:
                continue
            total_val = grupo["valor_num"].sum()
            print(
                f"  {cor}{sigla} {sev:<6}{RESET}  "
                f"{len(grupo):>4} achados  |  "
                f"impacto: {_fmt_valor(total_val)}"
            )

        print()
        print("  Por regra:")
        for regra_id, g in resultado.groupby("regra"):
            sev = g["severidade"].iloc[0]
            cor = SEV_CORES.get(sev, "")
            sigla = SEV_SIGLA.get(sev, "")
            print(f"    {cor}{sigla} {regra_id:<28}{RESET}  {len(g):>4} achados")

    print()
    print(f"  Relatorio salvo em: {caminho_saida}")
    print(f"{NEGRITO}{'='*60}{RESET}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auditoria de lancamentos incorretos no base.csv — G3S"
    )
    parser.add_argument(
        "--mes",
        metavar="MM/AAAA",
        help="Filtrar por mes de vencimento (ex: 03/2026). Padrao: base completa.",
        default=None,
    )
    parser.add_argument(
        "--apenas-alta",
        action="store_true",
        help="Incluir no relatorio somente achados de severidade ALTA.",
    )
    parser.add_argument(
        "--saida",
        metavar="ARQUIVO.md",
        help="Nome do arquivo de saida. Padrao: auditoria_YYYYMMDD.md",
        default=None,
    )
    args = parser.parse_args()

    # Valida CSV
    if not CSV_PATH.exists():
        print(f"{VERMELHO}[ERRO] Arquivo nao encontrado: {CSV_PATH}{RESET}")
        sys.exit(1)

    # Carrega base
    print(f"Carregando {CSV_PATH.name}...", end=" ", flush=True)
    df = carregar_base(mes=args.mes)
    print(f"{len(df):,} registros carregados.")

    # Executa auditoria
    print("Executando regras de auditoria...")
    resultado = executar_auditoria(df)

    # Define caminho de saida
    if args.saida:
        caminho_saida = OUTPUT_DIR / args.saida
    else:
        hoje_str = date.today().strftime("%Y%m%d")
        sufixo = f"_{args.mes.replace('/', '')}" if args.mes else ""
        caminho_saida = OUTPUT_DIR / f"auditoria{sufixo}_{hoje_str}.md"

    # Gera relatorio
    gerar_relatorio(
        resultado=resultado,
        df_base=df,
        mes=args.mes,
        apenas_alta=args.apenas_alta,
        caminho_saida=caminho_saida,
    )

    # Resumo no terminal
    _print_resumo_terminal(resultado, caminho_saida)


if __name__ == "__main__":
    main()
