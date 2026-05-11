"""Dump raw formula XML for PILARES sheet to verify _xlfn. prefixes survived."""
import re
import zipfile
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "02-Referencias" / "04_2026_Abr_Rel_FOPA.xlsx"
with zipfile.ZipFile(p) as z:
    # Show ordering of sheets via workbook.xml
    wb_xml = z.read("xl/workbook.xml").decode("utf-8")
    sheets = re.findall(r'<sheet[^>]+name="([^"]+)"[^>]+r:id="(rId\d+)"', wb_xml)
    print("Sheets:", sheets)

    # Map relationships to sheet target file
    rels = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")
    rel_map = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="(worksheets/[^"]+)"', rels))
    print("\nrel map:", rel_map)

    # Find PILARES sheet target
    pilares_rid = next((rid for n, rid in sheets if n == "PILARES"), None)
    pilares_path = "xl/" + rel_map[pilares_rid]
    print(f"\nPILARES target: {pilares_path}")

    xml = z.read(pilares_path).decode("utf-8")
    print("\n=== Formulas in PILARES ===")
    for m in re.finditer(r'<c r="([A-Z]+\d+)"[^>]*?>(?:<f[^>]*>([^<]+)</f>)', xml):
        print(f"  {m.group(1)}: {m.group(2)}")
