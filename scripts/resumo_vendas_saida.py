from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path


DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")
NUMBER_RE = re.compile(r"^\d{1,3}(?:\.\d{3})*,\d+$")
CITY_RE = re.compile(r"CIDADE\.:\s*(.*?)\s*-\s*[A-Z]{2}\b")
FILIAL_RE = re.compile(r"Filial:\s*([A-Z0-9]+)")

FILIAL_NOME_MAP = {
    "MATRIZ": "G3S PRESIDENTE PRUDENTE",
    "FILIAL1": "G3S CAMPO GRANDE",
    "FILIAL2": "G3S INATIVO",
    "FILIAL3": "G3S DOURADOS",
    "FILIAL4": "G3S MARINGA",
    "FILIAL5": "G3S LONDRINA",
    "FILIAL6": "GXS MARINGA",
    "FILIAL7": "RSE",
    "FILIAL8": "RSI",
    "FILIAL9": "G3S ASSIS",
}

DISPLAY_ORDER = [
    "G3S CAMPO GRANDE",
    "G3S DOURADOS",
    "G3S LONDRINA",
    "G3S MARINGA",
    "G3S PRESIDENTE PRUDENTE",
]


def br_to_float(value: str) -> float:
    return float(value.replace(".", "").replace(",", "."))


def format_brl(value: float) -> str:
    raw = f"{value:,.2f}"
    return raw.replace(",", "X").replace(".", ",").replace("X", ".")


def extract_total_from_line(line: str) -> float | None:
    fields = [part.strip() for part in line.split(";")]

    date_idx = next((i for i, part in enumerate(fields) if DATE_RE.match(part)), None)
    if date_idx is None:
        return None

    candidates: list[tuple[int, str]] = []
    for idx in range(date_idx + 1, min(len(fields), date_idx + 24)):
        part = fields[idx]
        if NUMBER_RE.match(part):
            candidates.append((idx, part))

    if len(candidates) < 3:
        return None

    price_position = None
    for idx, part in candidates:
        decimals = len(part.split(",")[1])
        if decimals >= 4:
            price_position = idx
            break

    if price_position is None:
        return None

    for idx, part in candidates:
        if idx <= price_position:
            continue
        decimals = len(part.split(",")[1])
        if decimals == 2:
            return br_to_float(part)

    return None


def branch_label(filial_code: str | None, city: str | None) -> str:
    if filial_code:
        return FILIAL_NOME_MAP.get(filial_code, filial_code)
    if city:
        return f"G3S {city}"
    return "FILIAL_NAO_IDENTIFICADA"


def parse_report(path: Path) -> dict[str, float]:
    totals = defaultdict(float)
    current_city: str | None = None
    current_filial_code: str | None = None
    current_branch = "FILIAL_NAO_IDENTIFICADA"

    with path.open("r", encoding="latin-1", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            city_match = CITY_RE.search(line)
            if city_match:
                current_city = city_match.group(1).strip()
                current_branch = branch_label(current_filial_code, current_city)
                continue

            filial_match = FILIAL_RE.search(line)
            if filial_match:
                current_filial_code = filial_match.group(1).strip()
                current_branch = branch_label(current_filial_code, current_city)
                continue

            line_total = extract_total_from_line(line)
            if line_total is not None:
                totals[current_branch] += line_total

    return dict(totals)


def parse_reports_from_folder(folder_path: Path) -> dict[str, float]:
    totals = defaultdict(float)
    csv_files = sorted(folder_path.glob("*.csv"))
    if not csv_files:
        return {}

    for csv_file in csv_files:
        report_totals = parse_report(csv_file)
        for filial, value in report_totals.items():
            totals[filial] += value

    return dict(totals)


def print_table(totals: dict[str, float]) -> None:
    if not totals:
        print("Nenhuma venda encontrada no relatório informado.")
        return

    order_map = {name: idx for idx, name in enumerate(DISPLAY_ORDER)}
    ordered = sorted(
        totals.items(),
        key=lambda item: (order_map.get(item[0], len(DISPLAY_ORDER)), item[0]),
    )
    filial_header = "filial"
    valor_header = "valor_vendas"

    filial_width = max(len(filial_header), max(len(name) for name, _ in ordered))
    valor_width = max(len(valor_header), max(len(format_brl(value)) for _, value in ordered))

    separator = f"+-{'-' * filial_width}-+-{'-' * valor_width}-+"
    print(separator)
    print(f"| {filial_header:<{filial_width}} | {valor_header:>{valor_width}} |")
    print(separator)
    for filial, total in ordered:
        print(f"| {filial:<{filial_width}} | {format_brl(total):>{valor_width}} |")
    print(separator)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lê relatório(s) de saída e mostra valor vendido por filial."
    )
    parser.add_argument(
        "--arquivo",
        default=None,
        help="Caminho do relatório de saída CSV exportado do SAGI.",
    )
    parser.add_argument(
        "--pasta",
        default="02-Referencias/Seletiva/Relatorios_Saida/Abril",
        help="Pasta com arquivos CSV de relatório de saída (um por filial).",
    )
    args = parser.parse_args()

    if args.arquivo:
        csv_path = Path(args.arquivo)
        if not csv_path.exists():
            raise SystemExit(f"Arquivo não encontrado: {csv_path}")
        totals = parse_report(csv_path)
    else:
        folder_path = Path(args.pasta)
        if not folder_path.exists():
            raise SystemExit(f"Pasta não encontrada: {folder_path}")
        totals = parse_reports_from_folder(folder_path)

    print_table(totals)


if __name__ == "__main__":
    main()
