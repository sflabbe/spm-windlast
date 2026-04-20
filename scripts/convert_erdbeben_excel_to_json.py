
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import pandas as pd


STATE_NUM = {
    "SH": "01", "HH": "02", "NI": "03", "HB": "04", "NW": "05", "HE": "06",
    "RP": "07", "BW": "08", "BY": "09", "SL": "10", "BE": "11", "BB": "12",
    "MV": "13", "SN": "14", "ST": "15", "TH": "16",
}
SHEETS = {
    "Bayern": ("BY", "Bayern"),
    "Hessen": ("HE", "Hessen"),
    "Nordrhein-Westfalen": ("NW", "Nordrhein-Westfalen"),
    "Rheinland-Pfalz": ("RP", "Rheinland-Pfalz"),
    "Thüringen": ("TH", "Thüringen"),
    "Sachsen": ("SN", "Sachsen"),
    "Sachsen-Anhalt": ("ST", "Sachsen-Anhalt"),
}


def norm_text(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    return text


def norm_simple(value):
    text = norm_text(value)
    if not text:
        return None
    repl = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue"}
    for old, new in repl.items():
        text = text.replace(old, new)
    text = text.lower().replace("-", " ").replace("/", " ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = " ".join(text.split())
    for prefix in ("landkreis ", "kreisfreie stadt ", "stadtkreis ", "stadt ", "kreis "):
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    return text


def normalize_area_code(value, state_code):
    text = norm_text(value)
    if not text:
        return None
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return None
    if len(digits) == 8:
        return digits
    if len(digits) == 7:
        return digits.zfill(8)
    if len(digits) == 6:
        return STATE_NUM[state_code] + digits
    return digits


def parse_zone(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    m = re.search(r"(\d+)", text)
    return int(m.group(1)) if m else text


def parse_ground(value):
    text = norm_text(value)
    if not text:
        return None
    m = re.search(r"Untergrundklasse\s+([A-Z]+)$", text)
    return m.group(1) if m else text


def load_admin_codes(repo_root: Path):
    path = repo_root / "src/spittelmeister_windlast/daten/admin_kreise_codes.json"
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    by_state_base = {}
    for code, rec in data["codes"].items():
        key = (rec.get("bundesland_code"), rec.get("base_name_normalized"))
        by_state_base.setdefault(key, []).append((code, rec))
    return by_state_base


def resolve_kreis(admin_alias, county_name, state_code):
    base = norm_simple(county_name)
    cands = admin_alias.get((state_code, base), [])
    if len(cands) == 1:
        return cands[0][0], [c[0] for c in cands]
    return None, [c[0] for c in cands]


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/convert_erdbeben_excel_to_json.py /path/to/Erdbeben.xlsx")

    xlsx_path = Path(sys.argv[1]).resolve()
    repo_root = Path(__file__).resolve().parents[1]
    out_path = repo_root / "src/spittelmeister_windlast/daten/erdbebenzonen_dataset.json"
    admin_alias = load_admin_codes(repo_root)

    coverage = {
        "BW": {
            "state_name": "Baden-Württemberg",
            "mode": "external_map_only",
            "status": "explicit_missing_in_workbook_table",
            "source_sheet": "Erläuterung",
            "note": 'Baden-Württemberg verweist in seiner Bekanntmachung von DIN 4149:2005-04 als Technische Baubestimmung ausschließlich auf die "Karte der Erdbebenzonen und geologischen Untergrundklassen für Baden-Württemberg 1:350 000".',
            "source_reference": "Landesvermessungsamt Baden-Württemberg / www.lgl-bw.de",
        },
        "NW": {
            "state_name": "Nordrhein-Westfalen",
            "mode": "external_map_reference",
            "status": "external_map_reference_in_workbook",
            "source_sheet": "Nordrhein-Westfalen",
            "note": 'Die Zuordnung erfolgt mit der "Karte der Erdbebenzonen und geologischen Untergrundklassen der Bundesrepublik Deutschland"; Verweis auf Geologischer Dienst Nordrhein-Westfalen.',
            "source_reference": "https://www.gd.nrw.de/pr_kd_erdbebenzonen-karte-350000.php",
        },
    }

    records = []
    next_id = 1

    def add_record(state_code, state_name, source_sheet, source_row, *, county_name=None, municipality_name=None, district_name=None, area_code=None, kreis_code=None, kreis_candidates=None, eq_zone=None, ground_class=None, note=None, source_mode="table"):
        nonlocal next_id
        records.append({
            "id": next_id,
            "state_code": state_code,
            "state_name": state_name,
            "source_sheet": source_sheet,
            "source_row": int(source_row) if source_row is not None and not pd.isna(source_row) else None,
            "source_mode": source_mode,
            "county_name": norm_text(county_name),
            "municipality_name": norm_text(municipality_name),
            "district_name": norm_text(district_name),
            "county_name_normalized": norm_simple(county_name),
            "municipality_name_normalized": norm_simple(municipality_name),
            "district_name_normalized": norm_simple(district_name),
            "area_code": area_code,
            "kreis_code": kreis_code,
            "kreis_code_candidates": kreis_candidates or [],
            "earthquake_zone": eq_zone,
            "ground_class": ground_class,
            "note": norm_text(note),
        })
        next_id += 1

    # Bayern
    df = pd.read_excel(xlsx_path, sheet_name="Bayern")
    coverage["BY"] = {"state_name": "Bayern", "mode": "table", "status": "tabular"}
    for idx, row in df.iterrows():
        county = norm_text(row.get("Kreis_Name"))
        if not county:
            continue
        area = normalize_area_code(row.get("Gde_Nr"), "BY")
        kreis_code = area[:5] if area and len(area) >= 5 else None
        candidates = []
        if not kreis_code:
            kreis_code, candidates = resolve_kreis(admin_alias, county, "BY")
        add_record("BY", "Bayern", "Bayern", idx + 2, county_name=county, municipality_name=row.get("Gemeinde_Name"), district_name=row.get("Gemarkung_Name"), area_code=area, kreis_code=kreis_code, kreis_candidates=candidates, eq_zone=parse_zone(row.get("EZON")), ground_class=parse_ground(row.get("GUK")), note=row.get("Bemerkung"))

    # Hessen
    df = pd.read_excel(xlsx_path, sheet_name="Hessen")
    coverage["HE"] = {"state_name": "Hessen", "mode": "table", "status": "tabular"}
    for idx, row in df.iterrows():
        county = norm_text(row.get("Kreis"))
        if not county:
            continue
        area = normalize_area_code(row.get("Gemeinde-ID"), "HE")
        kreis_digits = "".join(ch for ch in str(row.get("Kreis-ID") or "") if ch.isdigit())
        kreis_code = "06" + kreis_digits.zfill(3) if kreis_digits else None
        candidates = [kreis_code] if kreis_code else []
        if not kreis_code:
            kreis_code, candidates = resolve_kreis(admin_alias, county, "HE")
        add_record("HE", "Hessen", "Hessen", idx + 2, county_name=county, municipality_name=row.get("Gemeinde"), district_name=row.get("Gemarkung"), area_code=area, kreis_code=kreis_code, kreis_candidates=candidates, eq_zone=parse_zone(row.get("Erdbebenzone")), ground_class=parse_ground(row.get("Geologie")), note=row.get("RPU"))

    # Rheinland-Pfalz
    df = pd.read_excel(xlsx_path, sheet_name="Rheinland-Pfalz")
    coverage["RP"] = {"state_name": "Rheinland-Pfalz", "mode": "table", "status": "tabular"}
    for idx, row in df.iterrows():
        county = norm_text(row.get("Kreis_Name"))
        if not county:
            continue
        area = normalize_area_code(row.get("Gde_Nr"), "RP")
        kreis_code = area[:5] if area and len(area) >= 5 else None
        candidates = []
        if not kreis_code:
            kreis_code, candidates = resolve_kreis(admin_alias, county, "RP")
        note = None
        area_qkm = row.get("Fläche [qkm]")
        if area_qkm is not None and not pd.isna(area_qkm):
            note = f"Flaeche [qkm]: {area_qkm}"
        add_record("RP", "Rheinland-Pfalz", "Rheinland-Pfalz", idx + 2, county_name=county, municipality_name=row.get("Gemeinde_Name"), district_name=row.get("Gemarkung_Name"), area_code=area, kreis_code=kreis_code, kreis_candidates=candidates, eq_zone=parse_zone(row.get("EZON")), ground_class=parse_ground(row.get("GUK")), note=note)

    # Thüringen
    df = pd.read_excel(xlsx_path, sheet_name="Thüringen", header=1)
    coverage["TH"] = {"state_name": "Thüringen", "mode": "table_name_only", "status": "tabular_names_only"}
    for idx, row in df.iterrows():
        muni = norm_text(row.get("Gemeinde"))
        if not muni:
            continue
        add_record("TH", "Thüringen", "Thüringen", idx + 3, municipality_name=muni, district_name=row.get("Gemarkung"), eq_zone=parse_zone(row.get("Erdbebenzone")), ground_class=parse_ground(row.get("Untergrundklasse")), source_mode="table_name_only")

    # Sachsen
    df = pd.read_excel(xlsx_path, sheet_name="Sachsen")
    coverage["SN"] = {"state_name": "Sachsen", "mode": "table_name_only", "status": "tabular_names_only"}
    last_county = None
    last_muni = None
    for idx, row in df.iterrows():
        county = norm_text(row.get("Landkreis"))
        muni = norm_text(row.get("Gemeinde"))
        zone = parse_zone(row.get("Erdbeben-\nzone"))
        if county and county.startswith(("Direktionsbezirk", "Erdbebenzone")):
            if county.startswith("Erdbebenzone"):
                last_county = None
                last_muni = None
            continue
        if county:
            last_county = county
        county = last_county
        if muni:
            last_muni = muni
        muni = last_muni
        if zone is None:
            continue
        add_record("SN", "Sachsen", "Sachsen", idx + 2, county_name=county, municipality_name=muni, district_name=row.get("Gemarkung"), eq_zone=zone, ground_class=parse_ground(row.get("Geologische \nUntergrundklasse")), source_mode="table_name_only")

    # Sachsen-Anhalt
    df = pd.read_excel(xlsx_path, sheet_name="Sachsen-Anhalt", header=1)
    coverage["ST"] = {"state_name": "Sachsen-Anhalt", "mode": "table_name_only", "status": "tabular_names_only"}
    for idx, row in df.iterrows():
        muni = norm_text(row.get("Gemeinde"))
        if not muni:
            continue
        add_record("ST", "Sachsen-Anhalt", "Sachsen-Anhalt", idx + 3, municipality_name=muni, district_name=row.get("Gemarkung"), eq_zone=parse_zone(row.get("Erdbeben-\nzone")), ground_class=parse_ground(row.get("Geologische \nUntergrundklasse")), source_mode="table_name_only")

    index_area = {}
    index_kreis = {}
    index_state = {}
    for rec in records:
        index_state.setdefault(rec["state_code"], []).append(rec["id"])
        if rec["area_code"]:
            index_area.setdefault(rec["area_code"], []).append(rec["id"])
        if rec["kreis_code"]:
            index_kreis.setdefault(rec["kreis_code"], []).append(rec["id"])

    dataset = {
        "metadata": {
            "source_file": xlsx_path.name,
            "description": "Erdbebenzonen und geologische Untergrundklassen aus dem bereitgestellten Excel-Tabellenwerk; BW und NW explizit als Karten-/Verweisfaelle erfasst.",
            "n_records": len(records),
            "states_with_table": sorted([k for k, v in coverage.items() if v["mode"] in ("table", "table_name_only")]),
            "states_external_only": sorted([k for k, v in coverage.items() if v["mode"] not in ("table", "table_name_only")]),
        },
        "coverage": coverage,
        "index": {
            "area_code_8": index_area,
            "kreis_code_5": index_kreis,
            "state_code": index_state,
        },
        "records": records,
    }

    out_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} with {len(records)} records.")


if __name__ == "__main__":
    main()
