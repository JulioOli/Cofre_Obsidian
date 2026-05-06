"""
Auditoria semanal de lancamentos (ODBC export -> base.csv).

Le o CSV exportado do ODBC (campo ; como separador) e aplica regras
configuraveis em arquivo de configuracao (regras_auditoria.yaml).

Saida: relatorio Excel com abas por tipo de anomalia.

Observacao: registros com `ite_pagrec_vencimento = 1800-01-01` sao considerados
"migrados" e ficam fora das analises de padrao temporal.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


# ---------------------------------------------------------------------------
# Configuracao padrao
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV_PATH = (
    PROJECT_ROOT / "02-Referencias" / "Meus_Dados" / "base.csv"
)
DEFAULT_RULES_PATH = (
    PROJECT_ROOT / "02-Referencias" / "Meus_Dados" / "regras_auditoria.yaml"
)
DEFAULT_OUT_DIR = PROJECT_ROOT / "02-Referencias"
DEFAULT_FECHAMENTO_PATH = (
    PROJECT_ROOT
    / "02-Referencias"
    / "Meus_Dados"
    / "Lancamentos_CustosFixos_e_DespesasFixas_Fechamento2026.xlsx"
)
DEFAULT_CANVAS_PATH = (
    Path.home()
    / ".cursor"
    / "projects"
    / "c-Users-julio-santana-Documents-Projects-Cofre-Trabalho"
    / "canvases"
    / "auditoria-lacunas.canvas.tsx"
)

NOMES_CONTAS = {
    "7.1.4": "COMBUSTIVEL - DIESEL (POSTO)",
    "7.1.20": "RASTREADOR/ MONITORAMENTO",
    "7.1.23": "COMBUSTIVEL - DIESEL (ESTOQUE)",
    "7.3.2": "FGTS",
    "7.3.3": "INSS",
    "7.3.4": "EXAMES MEDICOS",
    "7.3.5": "ALIMENTACAO DO TRABALHADOR",
    "7.3.6": "PLANO DE SAUDE",
    "7.3.7": "ALUGUEL DE FUNCIONARIO",
    "7.3.12": "PRO LABORE",
    "7.3.13": "SINDICATOS",
    "7.3.14": "TREINAMENTOS E DESENVOLVIMENTO",
    "7.3.15": "SEGURO DE VIDA",
    "5.1": "LOCACAO DE MAQUINAS E EQUIPAMENTOS",
    "7.3.23": "HONORARIOS PJ",
    "7.3.25": "BENEFICIOS DIVERSOS",
    "7.5.1": "AGUA E ESGOTO",
    "7.5.10": "SEGURANCA E VIGILANCIA",
    "7.5.13": "SEGUROS",
    "7.5.16": "ALARME E MONITORAMENTO",
    "7.5.18": "SISTEMAS",
    "7.5.2": "ENERGIA ELETRICA",
    "7.5.3": "TELECOMUNICACOES",
    "7.5.20": "INTERNET",
    "7.5.28": "SERVICO DE LIMPEZA DO ESCRITORIO",
    "7.5.31": "ALUGUEIS ADMINISTRATIVO",
    "7.5.7": "HONORARIOS CONTABEIS",
    "7.5.8": "HONORARIOS ADVOCATICIOS",
    "7.5.9": "CONSULTORIA",
    "7.6.5": "IPTU PATIO",
    "9.2.6": "CONDOMINIO",
}


SUPPORTED_TIPOS = {
    "ausencia_mensal",
    "desvio_valor",
    "duplicata",
    "fornecedor_inesperado",
    "frequencia",
    "valor_zero",
}

SEV_DEFAULT = "ALTA"
SEV_ORDER = {"ALTA": 0, "MEDIA": 1, "BAIXA": 2}


# ---------------------------------------------------------------------------
# Parsing de regras (YAML simplificado)
# ---------------------------------------------------------------------------


def _strip_inline_comment(line: str) -> str:
    """
    Remove comentarios do tipo # ... sem suportar YAML completo.
    Funciona bem para o formato planejado (valores escalares).
    """
    in_quote: str | None = None
    for i, ch in enumerate(line):
        if ch in ("'", '"'):
            if in_quote is None:
                in_quote = ch
            elif in_quote == ch:
                in_quote = None
        if ch == "#" and in_quote is None:
            return line[:i]
    return line


_RE_INT = re.compile(r"^-?\d+$")
_RE_FLOAT = re.compile(r"^-?\d+(?:\.\d+)?$")


def _coerce_scalar(value: str) -> Any:
    v = value.strip()
    if v == "":
        return ""
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        v = v[1:-1]

    lower = v.lower()
    if lower in {"true", "false"}:
        return lower == "true"

    if _RE_INT.match(v):
        try:
            return int(v)
        except ValueError:
            pass
    if _RE_FLOAT.match(v):
        try:
            return float(v)
        except ValueError:
            pass
    return v


def load_rules_yaml(path: Path) -> list[dict[str, Any]]:
    """
    L e um subconjunto do YAML esperado para o projeto.

    Formato esperado:
      regras:
        - nome: ...
          tipo: ...
          codcdc: ...
          filial: ...
          ...
    """
    text = path.read_text(encoding="utf-8")
    lines = []
    for raw in text.splitlines():
        raw = raw.rstrip("\n\r")
        raw = _strip_inline_comment(raw).rstrip()
        if raw.strip():
            lines.append(raw)

    if not lines:
        return []

    current_item: dict[str, Any] | None = None
    items: list[dict[str, Any]] = []
    in_regras = False
    regras_indent: int | None = None
    item_indent: int | None = None

    for line in lines:
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        if not in_regras:
            if stripped == "regras:":
                in_regras = True
                regras_indent = indent
                continue
            continue

        # Qualquer coisa fora de indentacao compatível: ignorar.
        if regras_indent is not None and indent <= regras_indent and stripped != "regras:":
            break

        m_item = re.match(r"^-\s*(.+)$", stripped)
        if m_item:
            # Novo item
            if item_indent is None:
                item_indent = indent

            remainder = m_item.group(1).strip()
            current_item = {}
            items.append(current_item)

            # Caso "- chave: valor" no mesmo linha
            if ":" in remainder:
                key, value = remainder.split(":", 1)
                current_item[key.strip()] = _coerce_scalar(value)
            continue

        if current_item is None:
            continue

        # Linhas do tipo "  chave: valor"
        if ":" not in stripped:
            continue

        key, value = stripped.split(":", 1)
        current_item[key.strip()] = _coerce_scalar(value)

    return items


# ---------------------------------------------------------------------------
# Loader (CSV -> DataFrame tipado)
# ---------------------------------------------------------------------------


def _parse_date_series(s: pd.Series) -> pd.Series:
    # Evita warning de inferencia automatica: tenta formatos conhecidos primeiro.
    s_norm = s.astype(str).str.strip()
    dt = pd.to_datetime(s_norm, format="%Y-%m-%d", errors="coerce")
    miss = dt.isna()
    if miss.any():
        dt2 = pd.to_datetime(
            s_norm[miss], format="%d/%m/%Y", errors="coerce", dayfirst=True
        )
        dt.loc[miss] = dt2
    return dt


def _to_money_num(serie: pd.Series) -> pd.Series:
    # Converte formato pt-BR: "1.234,56" -> 1234.56
    # Observacao: alguns valores ja podem vir como "100" (sem separadores).
    return pd.to_numeric(
        serie.astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .replace({"nan": None}),
        errors="coerce",
    )


@dataclass(frozen=True)
class LoadedData:
    df: pd.DataFrame
    ref_date: date


@dataclass(frozen=True)
class ReferenceProfiles:
    # (codcdc, filial_ou_vazio) -> perfil
    by_key: dict[tuple[str, str], dict[str, Any]]


def carregar_base(
    csv_path: Path,
    *,
    reference_date: date,
    ignore_migrados: bool = True,
) -> LoadedData:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV nao encontrado: {csv_path}")

    # Base costuma vir em latin-1.
    df = pd.read_csv(
        csv_path,
        delimiter=";",
        encoding="latin-1",
        dtype=str,
        engine="python",  # tolera campos multi-linha entre aspas
        quoting=csv.QUOTE_MINIMAL,
    )

    # Normaliza nomes (mantem os mesmos do header do CSV)
    expected_cols = {
        "codcen",
        "descen",
        "codcdc",
        "descdc",
        "lancamento",
        "ite_pagrec_vencimento",
        "iterea_pagamento",
        "iterea_valpago",
        "documento",
        "codigo_pessoa",
        "nome",
        "valor_plano",
        "valor_centro",
        "observacao",
        "nota",
        "cab_pagrec_id",
        "valor_bruto",
        "filial",
    }
    faltando = [c for c in expected_cols if c not in df.columns]
    if faltando:
        raise ValueError(
            "CSV com colunas inesperadas; faltando: "
            f"{faltando}. Colunas presentes: {list(df.columns)}"
        )

    # Datas
    df["dt_lancamento"] = _parse_date_series(df["lancamento"])
    df["dt_vencimento"] = _parse_date_series(df["ite_pagrec_vencimento"])
    df["dt_pagamento"] = _parse_date_series(df["iterea_pagamento"])

    if ignore_migrados:
        # Registros migrados na base (padrão do projeto).
        df = df[df["dt_vencimento"].dt.year != 1800]

    # Numericos
    df["valor_bruto_num"] = _to_money_num(df["valor_bruto"])
    df["valor_plano_num"] = _to_money_num(df["valor_plano"])
    df["valor_centro_num"] = _to_money_num(df["valor_centro"])
    df["iterea_valpago_num"] = _to_money_num(df["iterea_valpago"])

    # normaliza strings chave
    df["codcdc"] = df["codcdc"].astype(str).str.strip()
    df["descdc"] = df["descdc"].astype(str).str.strip()
    df["codcen"] = df["codcen"].astype(str).str.strip()
    df["filial"] = df["filial"].astype(str).str.strip()
    df["documento"] = df["documento"].astype(str).fillna("").str.strip()
    df["codigo_pessoa"] = df["codigo_pessoa"].astype(str).fillna("").str.strip()
    df["nome"] = df["nome"].astype(str).fillna("").str.strip()

    # Evita linha vazia de documento/codigo_pessoa quebrar duplicatas
    df["codigo_pessoa_norm"] = df["codigo_pessoa"].replace({"": None})

    return LoadedData(df=df.reset_index(drop=True), ref_date=reference_date)


# ---------------------------------------------------------------------------
# Utilitarios de match / agrupamentos / referencia de fechamento
# ---------------------------------------------------------------------------


def codcdc_pattern_to_regex(pattern: str) -> str:
    r"""
    Converte um padrao simples com X e * para regex.

    Exemplos:
      7.X.XX -> ^7\.\d\.\d\d$
      7.5.*  -> ^7\.5\..*$
    """
    pat = pattern.strip()
    if pat == "":
        return r"^$"

    out = ["^"]
    for ch in pat:
        if ch == "X":
            out.append(r"\d")
        elif ch == "*":
            out.append(r".*")
        else:
            out.append(re.escape(ch))
    out.append("$")
    return "".join(out)


def filtro_codcdc(df: pd.DataFrame, codcdc_pattern: str) -> pd.Series:
    regex = codcdc_pattern_to_regex(codcdc_pattern)
    return df["codcdc"].astype(str).str.match(regex, na=False)


def _sheet_name(tipo: str) -> str:
    # Excel: max 31 chars e nao pode conter : \ / ? * [ ]
    clean = re.sub(r"[:\\/?*\[\]]", "_", tipo)
    return clean[:31] if len(clean) > 31 else clean


def _get_severidade(rule_cfg: dict[str, Any]) -> str:
    sev = str(rule_cfg.get("severidade", "")).strip().upper()
    if sev in SEV_ORDER:
        return sev
    return SEV_DEFAULT


def _norm_colname(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _find_column(columns: list[str], aliases: set[str]) -> str | None:
    col_map = {_norm_colname(c): c for c in columns}
    for alias in aliases:
        key = _norm_colname(alias)
        if key in col_map:
            return col_map[key]
    return None


def _carregar_fechamento_normalizado(path: Path) -> pd.DataFrame:
    """
    Carrega o arquivo de fechamento (xlsx/csv) e normaliza colunas-chave.
    """
    if not path.exists():
        return pd.DataFrame()

    dfs: list[pd.DataFrame] = []
    if path.suffix.lower() in {".xlsx", ".xlsm", ".xls"}:
        xls = pd.ExcelFile(path)
        for sheet in xls.sheet_names:
            df_sheet = pd.read_excel(xls, sheet_name=sheet, dtype=str)
            if not df_sheet.empty:
                dfs.append(df_sheet)
    elif path.suffix.lower() == ".csv":
        dfs.append(pd.read_csv(path, sep=";", encoding="latin-1", dtype=str))
    else:
        return pd.DataFrame()

    if not dfs:
        return pd.DataFrame()

    raw = pd.concat(dfs, ignore_index=True)
    cols = [str(c) for c in raw.columns]

    col_codcdc = _find_column(
        cols,
        {
            "codcdc",
            "codigo_plano",
            "cod_plano",
            "plano_conta",
            "conta",
            "codigo_conta",
        },
    )
    col_filial = _find_column(cols, {"filial", "empresa", "unidade"})
    col_cod_pessoa = _find_column(
        cols,
        {
            "codigo_pessoa",
            "cod_pessoa",
            "id_pessoa",
            "codigo_credor",
            "cod_credor",
            "codigo_fornecedor",
        },
    )
    col_nome = _find_column(
        cols,
        {"nome", "credor", "fornecedor", "favorecido", "pessoa"},
    )
    col_valor = _find_column(
        cols,
        {
            "valor_bruto",
            "valor",
            "valor_pago",
            "valor_lancamento",
            "iterea_valpago",
            "valor_plano",
        },
    )

    if not col_codcdc:
        return pd.DataFrame()

    out = pd.DataFrame()
    out["codcdc"] = raw[col_codcdc].astype(str).str.strip()
    out["filial"] = raw[col_filial].astype(str).str.strip() if col_filial else ""
    out["codigo_pessoa"] = (
        raw[col_cod_pessoa].astype(str).str.strip() if col_cod_pessoa else ""
    )
    out["nome"] = raw[col_nome].astype(str).str.strip() if col_nome else ""
    out["valor_bruto_num"] = (
        _to_money_num(raw[col_valor]) if col_valor else pd.Series([None] * len(raw))
    )

    out = out[out["codcdc"].str.match(r"^\d+(?:\.\d+)*$", na=False)]
    return out.reset_index(drop=True)


def build_reference_profiles(df_ref: pd.DataFrame) -> ReferenceProfiles:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    if df_ref.empty:
        return ReferenceProfiles(by_key=by_key)

    for (codcdc, filial), g in df_ref.groupby(["codcdc", "filial"], dropna=False):
        vals = g["valor_bruto_num"].dropna().astype(float)
        if vals.empty:
            valor_min = None
            valor_max = None
        else:
            p10 = float(vals.quantile(0.10))
            p90 = float(vals.quantile(0.90))
            valor_min = p10
            valor_max = p90

        by_key[(str(codcdc), str(filial or "").strip())] = {
            "codigo_pessoa_set": {
                str(x).strip() for x in g["codigo_pessoa"].dropna().astype(str) if str(x).strip()
            },
            "nome_set": {
                str(x).strip().upper()
                for x in g["nome"].dropna().astype(str)
                if str(x).strip()
            },
            "valor_min": valor_min,
            "valor_max": valor_max,
            "qtd_ref": int(len(g)),
        }

    return ReferenceProfiles(by_key=by_key)


def _pick_ref_profile(
    ref_profiles: ReferenceProfiles | None,
    *,
    codcdc: str,
    filial: str,
) -> dict[str, Any] | None:
    if ref_profiles is None:
        return None
    return (
        ref_profiles.by_key.get((codcdc, filial))
        or ref_profiles.by_key.get((codcdc, ""))
    )


def _row_base_context(df_row: pd.Series) -> dict[str, Any]:
    return {
        "codcdc": df_row.get("codcdc", ""),
        "descdc": df_row.get("descdc", ""),
        "filial": df_row.get("filial", ""),
        "codigo_pessoa": df_row.get("codigo_pessoa", ""),
        "nome": df_row.get("nome", ""),
        "documento": df_row.get("documento", ""),
        "valor_bruto": df_row.get("valor_bruto", ""),
        "valor_bruto_num": df_row.get("valor_bruto_num", None),
        "vencimento": (
            df_row.get("dt_vencimento").strftime("%Y-%m-%d")
            if pd.notna(df_row.get("dt_vencimento"))
            else ""
        ),
        "lancamento": (
            df_row.get("dt_lancamento").strftime("%Y-%m-%d")
            if pd.notna(df_row.get("dt_lancamento"))
            else ""
        ),
    }


# ---------------------------------------------------------------------------
# Detector (6 tipos conforme o plano)
# ---------------------------------------------------------------------------


def detectar_ausencia_mensal(df: pd.DataFrame, rule: dict[str, Any], ref_date: date) -> list[dict[str, Any]]:
    codcdc_pat = str(rule.get("codcdc", "")).strip()
    filial = rule.get("filial")
    dia_esperado = int(rule.get("dia_esperado", 1))
    tolerancia_dias = int(rule.get("tolerancia_dias", 0))

    if not codcdc_pat:
        return []

    df_f_all = df[filtro_codcdc(df, codcdc_pat)].copy()
    if filial is not None and str(filial).strip():
        filiais_alvo = [str(filial).strip()]
    else:
        filiais_alvo = sorted(
            {
                str(x).strip()
                for x in df_f_all["filial"].dropna().astype(str).tolist()
                if str(x).strip()
            }
        )
        if not filiais_alvo:
            filiais_alvo = [""]

    # Define data esperada no mes de ref_date
    # Ajusta caso dia_esperado exceda o ultimo dia do mes.
    month_start = date(ref_date.year, ref_date.month, 1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    last_day = (next_month - timedelta(days=1)).day
    expected_day = min(dia_esperado, last_day)
    expected_date = date(ref_date.year, ref_date.month, expected_day)

    window_start = expected_date - timedelta(days=tolerancia_dias)
    window_end = expected_date + timedelta(days=tolerancia_dias)

    # Para rodar semanalmente: so sinaliza ausencia quando a janela ja iniciou.
    if ref_date < window_start:
        return []

    sev = _get_severidade(rule)
    out: list[dict[str, Any]] = []

    for filial_alvo in filiais_alvo:
        if filial_alvo:
            df_f = df_f_all[df_f_all["filial"] == filial_alvo].copy()
        else:
            df_f = df_f_all.copy()

        has_any = False
        if not df_f.empty:
            has_any = (
                (df_f["dt_vencimento"] >= pd.Timestamp(window_start))
                & (df_f["dt_vencimento"] <= pd.Timestamp(window_end))
            ).any()
        if has_any:
            continue

        # Credor de referencia: mais frequente no historico da conta/filial.
        credor_ref = ""
        if not df_f.empty:
            hist = (
                df_f["nome"]
                .dropna()
                .astype(str)
                .str.strip()
            )
            hist = hist[hist != ""]
            if not hist.empty:
                credor_ref = str(hist.value_counts().index[0])

        out.append(
            {
                "tipo_alerta": "ausencia_mensal",
                "nome_regra": rule.get("nome", ""),
                "severidade": sev,
                "codcdc": codcdc_pat,
                "filial": filial_alvo,
                "credor_referencia": credor_ref,
                "esperado": expected_date.strftime("%Y-%m-%d"),
                "janela_inicio": window_start.strftime("%Y-%m-%d"),
                "janela_fim": window_end.strftime("%Y-%m-%d"),
                "descricao": (
                    "Nenhum lancamento encontrado para a conta na base"
                    if df_f.empty
                    else "Sem lancamento na janela esperada"
                ),
                "correcao": rule.get(
                    "correcao",
                    "Verificar motivo da ausencia e corrigir no SAGI se aplicavel",
                ),
            }
        )

    return out


def detectar_valor_zero(df: pd.DataFrame, rule: dict[str, Any]) -> list[dict[str, Any]]:
    codcdc_pat = str(rule.get("codcdc", "")).strip()
    filial = rule.get("filial")
    tolerancia = float(rule.get("tolerancia_valor_zero", rule.get("tolerancia", 0.0)))

    if not codcdc_pat:
        return []

    df_f = df[filtro_codcdc(df, codcdc_pat)]
    if filial is not None and str(filial).strip():
        df_f = df_f[df_f["filial"] == str(filial).strip()]

    val = df_f["valor_bruto_num"].fillna(0.0).astype(float)
    mask = val.abs() <= tolerancia
    df_bad = df_f[mask].copy()
    if df_bad.empty:
        return []

    sev = _get_severidade(rule)
    out: list[dict[str, Any]] = []
    for _, r in df_bad.iterrows():
        a = _row_base_context(r)
        a.update(
            {
                "tipo_alerta": "valor_zero",
                "nome_regra": rule.get("nome", ""),
                "severidade": sev,
                "descricao": f"Valor zerado (|v| <= {tolerancia:g})",
                "correcao": rule.get("correcao", "Validar se o lancamento deveria ter valor diferente de zero"),
            }
        )
        out.append(a)
    return out


def detectar_desvio_valor(
    df: pd.DataFrame,
    rule: dict[str, Any],
    ref_date: date,
    ref_profiles: ReferenceProfiles | None = None,
) -> list[dict[str, Any]]:
    """
    Detecta valores fora do intervalo definido na regra.

    Suporte:
      - valor_min / valor_max (recomendado)
      - ou: tolerancia_pct + janela_dias_baseline (baseline via mediana)
    """
    codcdc_pat = str(rule.get("codcdc", "")).strip()
    filial = rule.get("filial")

    if not codcdc_pat:
        return []

    df_f = df[filtro_codcdc(df, codcdc_pat)]
    if filial is not None and str(filial).strip():
        df_f = df_f[df_f["filial"] == str(filial).strip()]

    # Restricao para evitar comparar migrados / sem vencimento
    df_f = df_f[df_f["dt_vencimento"].notna()].copy()
    if df_f.empty:
        return []

    valor_min = rule.get("valor_min", None)
    valor_max = rule.get("valor_max", None)
    usar_referencia_fechamento = bool(rule.get("usar_referencia_fechamento", True))

    if valor_min is not None or valor_max is not None:
        if valor_min is None:
            valor_min = -float("inf")
        if valor_max is None:
            valor_max = float("inf")
        valor_min_f = float(valor_min)
        valor_max_f = float(valor_max)
    elif usar_referencia_fechamento:
        filial_key = str(filial).strip() if filial is not None else ""
        profile = _pick_ref_profile(
            ref_profiles, codcdc=codcdc_pat, filial=filial_key
        )
        if profile and profile.get("valor_min") is not None and profile.get("valor_max") is not None:
            margem = float(rule.get("margem_pct_referencia", 0.15))
            base_min = float(profile["valor_min"])
            base_max = float(profile["valor_max"])
            valor_min_f = base_min * (1.0 - margem)
            valor_max_f = base_max * (1.0 + margem)
        else:
            return []
    else:
        tolerancia_pct = float(rule.get("tolerancia_pct", 0.30))
        janela_dias_baseline = int(rule.get("janela_dias_baseline", 180))
        janela_inicio = ref_date - timedelta(days=janela_dias_baseline)
        baseline = df_f[
            (df_f["dt_vencimento"] >= pd.Timestamp(janela_inicio))
            & (df_f["dt_vencimento"] <= pd.Timestamp(ref_date))
        ]
        if baseline.empty:
            return []
        med = float(baseline["valor_bruto_num"].median())
        valor_min_f = med * (1.0 - tolerancia_pct)
        valor_max_f = med * (1.0 + tolerancia_pct)

    mask_bad = (df_f["valor_bruto_num"] < valor_min_f) | (df_f["valor_bruto_num"] > valor_max_f)
    df_bad = df_f[mask_bad].copy()
    if df_bad.empty:
        return []

    sev = _get_severidade(rule)
    out: list[dict[str, Any]] = []
    for _, r in df_bad.iterrows():
        a = _row_base_context(r)
        a.update(
            {
                "tipo_alerta": "desvio_valor",
                "nome_regra": rule.get("nome", ""),
                "severidade": sev,
                "valor_min": valor_min_f,
                "valor_max": valor_max_f,
                "descricao": "Valor fora do intervalo esperado",
                "correcao": rule.get("correcao", "Validar classificacao e/ou valor do lancamento no SAGI"),
            }
        )
        out.append(a)
    return out


def detectar_duplicata(df: pd.DataFrame, rule: dict[str, Any]) -> list[dict[str, Any]]:
    codcdc_pat = str(rule.get("codcdc", "")).strip()
    filial = rule.get("filial")
    janela_dias = int(rule.get("janela_dias", 7))
    tolerancia_centavos = float(rule.get("tolerancia_centavos", 0.01))

    if not codcdc_pat:
        return []

    df_f = df[filtro_codcdc(df, codcdc_pat)]
    if filial is not None and str(filial).strip():
        df_f = df_f[df_f["filial"] == str(filial).strip()]

    df_f = df_f[df_f["dt_vencimento"].notna()].copy()
    if df_f.empty:
        return []

    df_f["valor_bruto_num_round"] = df_f["valor_bruto_num"].round(2)

    group_cols = ["documento", "codigo_pessoa_norm", "valor_bruto_num_round"]
    df_f["_min_dt"] = df_f["dt_vencimento"]
    df_f["_max_dt"] = df_f["dt_vencimento"]

    grouped = df_f.groupby(group_cols, dropna=False, sort=False)
    out: list[dict[str, Any]] = []
    sev = _get_severidade(rule)

    for _key, g in grouped:
        if len(g) < 2:
            continue
        dt_min = g["dt_vencimento"].min()
        dt_max = g["dt_vencimento"].max()
        if pd.isna(dt_min) or pd.isna(dt_max):
            continue
        if (dt_max - dt_min).days > janela_dias:
            continue

        # "trate" rateio: se valores e documento iguais, assumimos duplicata legitima e ainda assim sinalizamos.
        # Premissa a ser refinada com o chefe, entao sinalizacao generica.
        docs = " / ".join(g["documento"].astype(str).unique().tolist())
        filenames = " / ".join(g["codcen"].astype(str).unique().tolist())

        # cria um achado por grupo (mais compacto no Excel)
        out.append(
            {
                "tipo_alerta": "duplicata",
                "nome_regra": rule.get("nome", ""),
                "severidade": sev,
                "codcdc": codcdc_pat,
                "filial": str(g["filial"].iloc[0]).strip() if "filial" in g.columns else "",
                "qtde": int(len(g)),
                "documento": docs,
                "codigo_pessoa": (g["codigo_pessoa_norm"].iloc[0] or ""),
                "valor_bruto_num": float(g["valor_bruto_num_round"].iloc[0]),
                "janela_inicio": dt_min.strftime("%Y-%m-%d"),
                "janela_fim": dt_max.strftime("%Y-%m-%d"),
                "codcen_list": filenames,
                "descricao": "Mesmo doc/pessoa/valor repetido em janela curta",
                "correcao": rule.get("correcao", "Verificar duplicidade e estornar o lancamento indevido no SAGI"),
            }
        )

    return out


def detectar_fornecedor_inesperado(
    df: pd.DataFrame,
    rule: dict[str, Any],
    ref_profiles: ReferenceProfiles | None = None,
) -> list[dict[str, Any]]:
    codcdc_pat = str(rule.get("codcdc", "")).strip()
    filial = rule.get("filial")
    allowed_codigo_pessoa = rule.get("codigo_pessoa", None)
    nome_regex = rule.get("nome_regex", None)

    if not codcdc_pat:
        return []

    df_f = df[filtro_codcdc(df, codcdc_pat)]
    if filial is not None and str(filial).strip():
        df_f = df_f[df_f["filial"] == str(filial).strip()]

    if df_f.empty:
        return []

    usar_referencia_fechamento = bool(rule.get("usar_referencia_fechamento", True))

    allowed_set: set[str] | None = None
    if allowed_codigo_pessoa is not None and str(allowed_codigo_pessoa).strip() != "":
        if isinstance(allowed_codigo_pessoa, list):
            allowed_set = {str(x).strip() for x in allowed_codigo_pessoa if str(x).strip()}
        else:
            allowed_set = {str(allowed_codigo_pessoa).strip()}

    rex = None
    # fallback via fechamento: aprende credores esperados por codcdc/filial
    if allowed_set is None and rex is None and usar_referencia_fechamento:
        filial_key = str(filial).strip() if filial is not None else ""
        profile = _pick_ref_profile(
            ref_profiles, codcdc=codcdc_pat, filial=filial_key
        )
        if profile:
            ref_codes = profile.get("codigo_pessoa_set") or set()
            if ref_codes:
                allowed_set = {str(x).strip() for x in ref_codes if str(x).strip()}

    # Sem regra de fornecedor definida -> nao gera alerta
    if allowed_set is None and rex is None:
        return []

    if nome_regex is not None and str(nome_regex).strip():
        rex = re.compile(str(nome_regex).strip())

    def ok_row(r: pd.Series) -> bool:
        if allowed_set is not None:
            if str(r.get("codigo_pessoa_norm") or "").strip() in allowed_set:
                return True
        if rex is not None:
            if rex.search(str(r.get("nome", ""))):
                return True
        return False

    sev = _get_severidade(rule)
    out: list[dict[str, Any]] = []
    for _, r in df_f.iterrows():
        if ok_row(r):
            continue
        a = _row_base_context(r)
        a.update(
            {
                "tipo_alerta": "fornecedor_inesperado",
                "nome_regra": rule.get("nome", ""),
                "severidade": sev,
                "descricao": "Pessoa nao corresponde ao fornecedor/cliente esperado",
                "correcao": rule.get("correcao", "Validar se a conta deveria ser lancada para esta pessoa no SAGI"),
            }
        )
        out.append(a)
    return out


def detectar_frequencia(df: pd.DataFrame, rule: dict[str, Any], ref_date: date) -> list[dict[str, Any]]:
    codcdc_pat = str(rule.get("codcdc", "")).strip()
    filial = rule.get("filial")
    periodicidade = str(rule.get("periodicidade", "")).strip().lower()
    tolerancia_dias = int(rule.get("tolerancia_dias", 2))

    if not codcdc_pat or periodicidade == "":
        return []

    expected_interval: int
    if periodicidade == "mensal":
        expected_interval = 30
    elif periodicidade == "semanal":
        expected_interval = 7
    elif periodicidade == "quinzenal":
        expected_interval = 14
    else:
        return []

    df_f = df[filtro_codcdc(df, codcdc_pat)]
    if filial is not None and str(filial).strip():
        df_f = df_f[df_f["filial"] == str(filial).strip()]

    df_f = df_f[df_f["dt_vencimento"].notna()].copy()
    if df_f.empty:
        return []

    group_keys: list[str] = []
    if filial is None or str(filial).strip() == "":
        group_keys = ["filial"]

    grouped = df_f.groupby(group_keys, dropna=False, sort=False) if group_keys else [(None, df_f)]

    sev = _get_severidade(rule)
    out: list[dict[str, Any]] = []

    for g_key, g in grouped:
        if group_keys:
            filial_val = str(g_key) if g_key is not None else ""
        else:
            filial_val = str(rule.get("filial", "") or "")

        dates = sorted(g["dt_vencimento"].dropna().dt.date.unique())
        if len(dates) < 2:
            continue

        for prev_dt, next_dt in zip(dates, dates[1:]):
            diff = (next_dt - prev_dt).days
            if diff < expected_interval - tolerancia_dias or diff > expected_interval + tolerancia_dias:
                # Achado ligado ao "next" (o que foge da periodicidade)
                g_next = g[g["dt_vencimento"].dt.date == next_dt]
                example = g_next.iloc[0]
                a = _row_base_context(example)
                a.update(
                    {
                        "tipo_alerta": "frequencia",
                        "nome_regra": rule.get("nome", ""),
                        "severidade": sev,
                        "filial": filial_val,
                        "periodicidade": periodicidade,
                        "esperado_interval_dias": expected_interval,
                        "diferenca_dias": int(diff),
                        "data_anterior": prev_dt.strftime("%Y-%m-%d"),
                        "data_proxima": next_dt.strftime("%Y-%m-%d"),
                        "descricao": "Intervalo de lancamentos fora da periodicidade esperada",
                        "correcao": rule.get(
                            "correcao",
                            "Validar a cadencia no SAGI e corrigir classificacao/periodo se aplicavel",
                        ),
                    }
                )
                out.append(a)

        # Checa lacuna "mais recente": se ultimo lancamento ja passou do intervalo esperado.
        last_dt = dates[-1]
        atraso = (ref_date - last_dt).days
        if atraso > expected_interval + tolerancia_dias:
            example = g[g["dt_vencimento"].dt.date == last_dt].iloc[0]
            a = _row_base_context(example)
            a.update(
                {
                    "tipo_alerta": "frequencia",
                    "nome_regra": rule.get("nome", ""),
                    "severidade": sev,
                    "filial": filial_val,
                    "periodicidade": periodicidade,
                    "esperado_interval_dias": expected_interval,
                    "diferenca_dias": int(atraso),
                    "data_anterior": last_dt.strftime("%Y-%m-%d"),
                    "data_proxima": "",
                    "descricao": "Possivel lancamento faltante: intervalo desde o ultimo vencimento acima do esperado",
                    "correcao": rule.get(
                        "correcao",
                        "Validar se houve falta de lancamento na recorrencia esperada",
                    ),
                }
            )
            out.append(a)

    return out


DETECTORS = {
    "ausencia_mensal": detectar_ausencia_mensal,
    "desvio_valor": detectar_desvio_valor,
    "duplicata": detectar_duplicata,
    "fornecedor_inesperado": detectar_fornecedor_inesperado,
    "frequencia": detectar_frequencia,
    "valor_zero": detectar_valor_zero,
}


# ---------------------------------------------------------------------------
# Motor + Reporter (Excel)
# ---------------------------------------------------------------------------


def executar_auditoria(
    df: pd.DataFrame,
    rules: list[dict[str, Any]],
    *,
    ref_date: date,
    ref_profiles: ReferenceProfiles | None = None,
) -> pd.DataFrame:
    todos: list[dict[str, Any]] = []

    for i, rule in enumerate(rules):
        tipo = str(rule.get("tipo", "")).strip()
        if tipo not in SUPPORTED_TIPOS:
            continue

        if tipo == "desvio_valor":
            hits = DETECTORS[tipo](df, rule, ref_date, ref_profiles)
        elif tipo == "fornecedor_inesperado":
            hits = DETECTORS[tipo](df, rule, ref_profiles)
        elif tipo in {"ausencia_mensal", "frequencia"}:
            hits = DETECTORS[tipo](df, rule, ref_date)
        else:
            hits = DETECTORS[tipo](df, rule)

        # metadados do rule
        for h in hits:
            h.setdefault("rule_index", i)
            h.setdefault("nome_regra", rule.get("nome", ""))
            h.setdefault("tipo_alerta", tipo)

        todos.extend(hits)

    if not todos:
        return pd.DataFrame()

    out = pd.DataFrame(todos)

    if "severidade" in out.columns:
        out["_sev_ord"] = out["severidade"].map(SEV_ORDER).fillna(9)
        out = out.sort_values(["_sev_ord"], ascending=[True]).drop(columns=["_sev_ord"])

    return out.reset_index(drop=True)


def _format_dt_br(value: Any) -> str:
    if value is None or value == "" or (isinstance(value, float) and pd.isna(value)):
        return "-"
    try:
        d = pd.to_datetime(value, errors="coerce")
    except Exception:
        return str(value)
    if pd.isna(d):
        return str(value)
    return d.strftime("%d/%m/%Y")


def _js_string(value: Any) -> str:
    s = "" if value is None else str(value)
    return json.dumps(s, ensure_ascii=False)


def _safe_label(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, float) and pd.isna(value):
        return fallback
    s = str(value).strip()
    if s.lower() in {"nan", "none", ""}:
        return fallback
    return s


def _build_lacunas_payload(
    out_df: pd.DataFrame, ref_date: date
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    if out_df.empty:
        return [], [], {"total_lacunas": 0, "total_atrasos": 0, "contas_pendentes": 0}

    df_aus = out_df[out_df["tipo_alerta"] == "ausencia_mensal"].copy()
    df_freq = out_df[
        (out_df["tipo_alerta"] == "frequencia")
        & (
            out_df.get("descricao", pd.Series([""] * len(out_df), dtype=object))
            .astype(str)
            .str.contains("faltante", case=False, na=False)
        )
    ].copy()

    lacunas: list[dict[str, Any]] = []

    for _, r in df_aus.iterrows():
        codcdc = str(r.get("codcdc", "") or "")
        lacunas.append(
            {
                "conta": codcdc,
                "descricao": NOMES_CONTAS.get(codcdc, codcdc),
                "filial": _safe_label(r.get("filial", ""), "(sem filial)"),
                "documento": _safe_label(r.get("documento", ""), "—"),
                "credor": _safe_label(r.get("credor_referencia", ""), "(sem referência)"),
                "esperado": _format_dt_br(r.get("esperado", "")),
                "janela": f"{_format_dt_br(r.get('janela_inicio',''))} a {_format_dt_br(r.get('janela_fim',''))}",
                "detalhe": str(r.get("descricao", "") or "Sem lancamento na janela esperada"),
            }
        )

    atrasos: list[dict[str, Any]] = []
    for _, r in df_freq.iterrows():
        codcdc = str(r.get("codcdc", "") or "")
        atrasos.append(
            {
                "conta": codcdc,
                "descricao": NOMES_CONTAS.get(codcdc, codcdc),
                "filial": _safe_label(r.get("filial", ""), "(sem filial)"),
                "ultimo": _format_dt_br(r.get("data_anterior", "")),
                "diasSemLancamento": int(r.get("diferenca_dias", 0) or 0),
                "credor": _safe_label(r.get("nome", ""), "(sem referência)"),
            }
        )

    stats = {
        "total_lacunas": len(lacunas),
        "total_atrasos": len(atrasos),
        "contas_pendentes": len({l["conta"] for l in lacunas}),
    }
    return lacunas, atrasos, stats


def gerar_canvas(out_df: pd.DataFrame, ref_date: date, output_path: Path) -> None:
    lacunas, atrasos, stats = _build_lacunas_payload(out_df, ref_date)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    def _lacuna_to_js(l: dict[str, Any]) -> str:
        return (
            "  {\n"
            f"    conta: {_js_string(l['conta'])},\n"
            f"    descricao: {_js_string(l['descricao'])},\n"
            f"    filial: {_js_string(l['filial'])},\n"
            f"    documento: {_js_string(l['documento'])},\n"
            f"    credor: {_js_string(l['credor'])},\n"
            f"    esperado: {_js_string(l['esperado'])},\n"
            f"    janela: {_js_string(l['janela'])},\n"
            f"    detalhe: {_js_string(l['detalhe'])},\n"
            "  },"
        )

    def _atraso_to_js(a: dict[str, Any]) -> str:
        return (
            "  {\n"
            f"    conta: {_js_string(a['conta'])},\n"
            f"    descricao: {_js_string(a['descricao'])},\n"
            f"    filial: {_js_string(a['filial'])},\n"
            f"    ultimo: {_js_string(a['ultimo'])},\n"
            f"    diasSemLancamento: {int(a['diasSemLancamento'])},\n"
            f"    credor: {_js_string(a['credor'])},\n"
            "  },"
        )

    lacunas_js = "\n".join(_lacuna_to_js(l) for l in lacunas)
    atrasos_js = "\n".join(_atraso_to_js(a) for a in atrasos)

    sev_counts = {
        "ALTA": int((out_df.get("severidade", pd.Series(dtype=str)) == "ALTA").sum()) if not out_df.empty else 0,
        "MEDIA": int((out_df.get("severidade", pd.Series(dtype=str)) == "MEDIA").sum()) if not out_df.empty else 0,
        "BAIXA": int((out_df.get("severidade", pd.Series(dtype=str)) == "BAIXA").sum()) if not out_df.empty else 0,
    }

    freq_faltante_mask = (
        (out_df.get("tipo_alerta", pd.Series(dtype=str)) == "frequencia")
        & (
            out_df.get("descricao", pd.Series([""] * len(out_df), dtype=object))
            .astype(str)
            .str.contains("faltante", case=False, na=False)
        )
    ) if not out_df.empty else pd.Series(dtype=bool)

    lacuna_mask = (
        out_df.get("tipo_alerta", pd.Series(dtype=str)).eq("ausencia_mensal") | freq_faltante_mask
    ) if not out_df.empty else pd.Series(dtype=bool)

    outros_df = out_df[~lacuna_mask].copy() if not out_df.empty else pd.DataFrame()
    if not outros_df.empty:
        outros_df["_ord"] = outros_df["severidade"].map(SEV_ORDER).fillna(9)
        outros_df = outros_df.sort_values(["_ord"]).drop(columns=["_ord"]).head(10)

    outros_rows = []
    for _, r in outros_df.iterrows():
        conta = str(r.get("codcdc", "") or "")
        outros_rows.append(
            [
                str(r.get("severidade", "")),
                conta,
                NOMES_CONTAS.get(conta, conta),
                str(r.get("tipo_alerta", "")),
                _safe_label(r.get("filial", ""), "(sem filial)"),
                str(r.get("descricao", "") or ""),
            ]
        )

    outros_rows_js = json.dumps(outros_rows, ensure_ascii=False)

    atualizado = datetime.now().strftime("%d/%m/%Y %H:%M")
    ref_str = ref_date.strftime("%d/%m/%Y")

    tpl = f"""import {{ Callout, Divider, Grid, H1, H2, Stack, Stat, Table, Text }} from "cursor/canvas";

type Lacuna = {{
  conta: string;
  descricao: string;
  filial: string;
  documento: string;
  credor: string;
  esperado: string;
  janela: string;
  detalhe: string;
}};

type Atraso = {{
  conta: string;
  descricao: string;
  filial: string;
  ultimo: string;
  diasSemLancamento: number;
  credor: string;
}};

const REF_DATE = {_js_string(ref_str)};
const ATUALIZADO_EM = {_js_string(f"Gerado em {atualizado}")};

const LACUNAS: Lacuna[] = [
{lacunas_js}
];

const ATRASOS: Atraso[] = [
{atrasos_js}
];

const SEVERIDADE = {{
  alta: {sev_counts["ALTA"]},
  media: {sev_counts["MEDIA"]},
  baixa: {sev_counts["BAIXA"]},
}};

const OUTROS_ALERTAS: string[][] = {outros_rows_js};

export default function AuditoriaLacunas() {{
  return (
    <Stack gap={{20}}>
      <Stack gap={{4}}>
        <H1>Auditoria de Lancamentos - Lacunas</H1>
        <Text tone="secondary" size="small">Data de referencia: {{REF_DATE}}</Text>
        <Text tone="tertiary" size="small">{{ATUALIZADO_EM}}</Text>
      </Stack>

      <Grid columns={{3}} gap={{16}}>
        <Stat
          value={{{stats["total_lacunas"]}}}
          label="Lancamentos faltando este mes"
          tone={{LACUNAS.length > 0 ? "warning" : "success"}}
        />
        <Stat
          value={{{stats["total_atrasos"]}}}
          label="Possiveis atrasos (frequencia)"
          tone={{ATRASOS.length > 0 ? "warning" : "success"}}
        />
        <Stat
          value={{{stats["contas_pendentes"]}}}
          label="Contas com pendencia"
        />
      </Grid>

      <Grid columns={{3}} gap={{16}}>
        <Stat value={{SEVERIDADE.alta}} label="Alertas ALTA" tone={{SEVERIDADE.alta > 0 ? "danger" : undefined}} />
        <Stat value={{SEVERIDADE.media}} label="Alertas MEDIA" tone={{SEVERIDADE.media > 0 ? "warning" : undefined}} />
        <Stat value={{SEVERIDADE.baixa}} label="Alertas BAIXA" tone={{SEVERIDADE.baixa > 0 ? "info" : undefined}} />
      </Grid>

      <Divider />

      <Stack gap={{8}}>
        <H2>Faltando este mes</H2>
        {{LACUNAS.length === 0 ? (
          <Callout tone="success">
            Nenhum lancamento faltando nas contas monitoradas.
          </Callout>
        ) : (
          LACUNAS.map((l, i) => (
            <Stack key={{i}} gap={{2}}>
              <Text>
                Lancamento de <Text weight="semibold" as="span">{{l.descricao}}</Text>{{" "}}
                (plano <Text weight="semibold" as="span">{{l.conta}}</Text>) esta faltando
                este mes na filial <Text weight="semibold" as="span">{{l.filial}}</Text>.
              </Text>
              <Text tone="secondary" size="small">
                Credor de referencia: {{l.credor}}. Esperado por volta de {{l.esperado}} (janela {{l.janela}}). Documento: {{l.documento}}.
              </Text>
            </Stack>
          ))
        )}}
      </Stack>

      <Divider />

      <Stack gap={{8}}>
        <H2>Possiveis atrasos por frequencia</H2>
        {{ATRASOS.length === 0 ? (
          <Callout tone="success">
            Todas as contas com periodicidade configurada estao dentro do esperado.
          </Callout>
        ) : (
          ATRASOS.map((a, i) => (
            <Text key={{i}}>
              {{a.descricao}} (plano <Text weight="semibold" as="span">{{a.conta}}</Text>) - filial{{" "}}
              <Text weight="semibold" as="span">{{a.filial}}</Text>: ultimo lancamento em {{a.ultimo}}, ha{{" "}}
              <Text weight="semibold" as="span">{{a.diasSemLancamento}} dias</Text> sem novo lancamento. Credor mais recente: {{a.credor}}.
            </Text>
          ))
        )}}
      </Stack>

      <Divider />

      <Stack gap={{8}}>
        <H2>Outros alertas relevantes (top 10)</H2>
        <Table
          headers={{["Severidade", "Conta", "Descricao", "Tipo", "Filial", "Detalhe"]}}
          rows={{OUTROS_ALERTAS}}
          columnAlign={{["left", "left", "left", "left", "left", "left"]}}
          emptyMessage="Nenhum alerta complementar."
        />
      </Stack>

      <Divider />

      <Callout tone="info" title="Como atualizar este painel">
        Rode <Text as="span" weight="semibold">python scripts/auditoria_lancamentos.py --ref-date "AAAA-MM-DD"</Text>.
        Este painel sera regerado a partir dos achados do base.csv.
      </Callout>
    </Stack>
  );
}}
"""
    output_path.write_text(tpl, encoding="utf-8")


def gerar_excel(out_df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        if out_df.empty:
            pd.DataFrame(
                [
                    {
                        "total_achados": 0,
                        "mensagem": "Nenhuma anomalia encontrada com as regras atuais.",
                    }
                ]
            ).to_excel(writer, sheet_name="resumo", index=False)
            return

        # Painel simples para usuario final (prioriza lacunas)
        is_gap = out_df["tipo_alerta"].isin(["ausencia_mensal", "frequencia"])
        lacunas_df = out_df[is_gap].copy()
        outros_df = out_df[~is_gap].copy()

        painel = pd.DataFrame(
            [
                {
                    "indicador": "Total de alertas",
                    "valor": int(len(out_df)),
                },
                {
                    "indicador": "Lacunas (ausencia/frequencia)",
                    "valor": int(len(lacunas_df)),
                },
                {
                    "indicador": "Outros alertas",
                    "valor": int(len(outros_df)),
                },
            ]
        )

        painel_contas = (
            out_df.groupby(["codcdc", "tipo_alerta"], dropna=False)
            .size()
            .reset_index(name="qtde")
            .sort_values(["qtde", "codcdc"], ascending=[False, True])
        )

        painel.to_excel(writer, sheet_name="00_painel", index=False)
        painel_contas.to_excel(writer, sheet_name="00_painel", index=False, startrow=6)

        # Aba dedicada de lacunas (mais intuitiva para usuario comum)
        if not lacunas_df.empty:
            lacunas_view_cols = [
                "severidade",
                "tipo_alerta",
                "codcdc",
                "filial",
                "nome_regra",
                "esperado",
                "janela_inicio",
                "janela_fim",
                "data_anterior",
                "data_proxima",
                "descricao",
                "correcao",
            ]
            lacunas_view_cols = [c for c in lacunas_view_cols if c in lacunas_df.columns]
            lacunas_df[lacunas_view_cols].to_excel(
                writer, sheet_name="01_lacunas", index=False
            )
        else:
            pd.DataFrame(
                [{"mensagem": "Nenhuma lacuna detectada com as regras atuais."}]
            ).to_excel(writer, sheet_name="01_lacunas", index=False)

        # resumo
        if "tipo_alerta" in out_df.columns and "severidade" in out_df.columns:
            resumo = (
                out_df.groupby(["tipo_alerta", "severidade"], dropna=False)
                .size()
                .reset_index(name="qtde")
                .sort_values(["tipo_alerta", "severidade"])
            )
        else:
            resumo = pd.DataFrame({"qtde": [len(out_df)]})

        resumo.to_excel(writer, sheet_name="resumo", index=False)

        # abas por tipo
        for tipo in sorted(out_df["tipo_alerta"].dropna().unique().tolist()):
            df_t = out_df[out_df["tipo_alerta"] == tipo].copy()
            sheet = _sheet_name(str(tipo))
            df_t.to_excel(writer, sheet_name=sheet, index=False)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_date(value: str) -> date:
    # Aceita YYYY-MM-DD
    return datetime.strptime(value, "%Y-%m-%d").date()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auditoria semanal de lancamentos com regras YAML"
    )
    parser.add_argument(
        "--csv",
        default=str(DEFAULT_CSV_PATH),
        help=f"Caminho do base.csv (padrao: {DEFAULT_CSV_PATH})",
    )
    parser.add_argument(
        "--regras",
        default=str(DEFAULT_RULES_PATH),
        help=f"Caminho do regras_auditoria.yaml (padrao: {DEFAULT_RULES_PATH})",
    )
    parser.add_argument(
        "--ref-date",
        default=date.today().strftime("%Y-%m-%d"),
        help="Data de referencia para checagens temporais (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Caminho do arquivo Excel de saida. Se omitido, monta padrao automatico.",
    )
    parser.add_argument(
        "--usar-migrados",
        action="store_true",
        help="Inclui registros migrados (ite_pagrec_vencimento=1800-01-01).",
    )
    parser.add_argument(
        "--fechamento",
        default=str(DEFAULT_FECHAMENTO_PATH),
        help=(
            "Arquivo de fechamento (xlsx/csv) usado como baseline por credor/valor "
            f"(padrao: {DEFAULT_FECHAMENTO_PATH})"
        ),
    )
    parser.add_argument(
        "--ignorar-fechamento",
        action="store_true",
        help="Desabilita baseline do arquivo de fechamento.",
    )
    parser.add_argument(
        "--canvas-out",
        default=str(DEFAULT_CANVAS_PATH),
        help=(
            "Caminho do arquivo .canvas.tsx gerado para visualizacao na IDE "
            f"(padrao: {DEFAULT_CANVAS_PATH})"
        ),
    )
    parser.add_argument(
        "--excel",
        action="store_true",
        help="Gera tambem o relatorio Excel (saida padrao agora e o canvas).",
    )
    parser.add_argument(
        "--sem-canvas",
        action="store_true",
        help="Pula a geracao do canvas (.canvas.tsx).",
    )

    args = parser.parse_args()

    csv_path = Path(args.csv)
    rules_path = Path(args.regras)
    fechamento_path = Path(args.fechamento)
    ref_date = _parse_date(args.ref_date)

    if not rules_path.exists():
        raise FileNotFoundError(
            f"Arquivo de regras nao encontrado: {rules_path}. Crie `regras_auditoria.yaml`."
        )

    rules = load_rules_yaml(rules_path)
    if not rules:
        print("Nenhuma regra encontrada no YAML. Nada a executar.", file=sys.stderr)

    loaded = carregar_base(
        csv_path,
        reference_date=ref_date,
        ignore_migrados=not bool(args.usar_migrados),
    )

    ref_profiles: ReferenceProfiles | None = None
    if not bool(args.ignorar_fechamento):
        df_ref = _carregar_fechamento_normalizado(fechamento_path)
        ref_profiles = build_reference_profiles(df_ref)

    result_df = executar_auditoria(
        loaded.df,
        rules,
        ref_date=loaded.ref_date,
        ref_profiles=ref_profiles,
    )

    canvas_path = Path(args.canvas_out)
    if not bool(args.sem_canvas):
        gerar_canvas(result_df, ref_date, canvas_path)
        print(f"Canvas gerado em: {canvas_path}")

    if args.out or bool(args.excel):
        if args.out:
            out_path = Path(args.out)
        else:
            out_path = (
                DEFAULT_OUT_DIR
                / f"relatorio_auditoria_{ref_date.strftime('%Y-%m-%d')}.xlsx"
            )
        gerar_excel(result_df, out_path)
        print(f"Relatorio Excel gerado em: {out_path}")

    print(f"Total de achados: {len(result_df):,}")


if __name__ == "__main__":
    main()

