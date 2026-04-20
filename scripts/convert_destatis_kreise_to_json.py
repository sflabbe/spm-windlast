#!/usr/bin/env python3
"""Konvertiert die amtliche Destatis-Tabelle der Kreise/Stadtkreise in JSON.

Quelle:
  Destatis – "Kreisfreie Städte und Landkreise am 31.12.2024"
  https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/04-kreise.xlsx?__blob=publicationFile

Erzeugt:
  - src/spittelmeister_windlast/daten/admin_kreise_codes.json

Die Datei ist gefahrdungsneutral und kann daher spaeter nicht nur fuer Wind- und
Schneelast, sondern auch fuer Seismik oder andere Kartenwerke als stabile
Verwaltungsebene wiederverwendet werden.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spittelmeister_windlast.geo._normalize import norm_kreis, norm_kreis_basis  # noqa: E402

STATE_MAP = {
    "01": "SH",
    "02": "HH",
    "03": "NI",
    "04": "HB",
    "05": "NW",
    "06": "HE",
    "07": "RP",
    "08": "BW",
    "09": "BY",
    "10": "SL",
    "11": "BE",
    "12": "BB",
    "13": "MV",
    "14": "SN",
    "15": "ST",
    "16": "TH",
}
STATE_NAMES = {
    "SH": "Schleswig-Holstein",
    "HH": "Hamburg",
    "NI": "Niedersachsen",
    "HB": "Bremen",
    "NW": "Nordrhein-Westfalen",
    "HE": "Hessen",
    "RP": "Rheinland-Pfalz",
    "BW": "Baden-Wuerttemberg",
    "BY": "Bayern",
    "SL": "Saarland",
    "BE": "Berlin",
    "BB": "Brandenburg",
    "MV": "Mecklenburg-Vorpommern",
    "SN": "Sachsen",
    "ST": "Sachsen-Anhalt",
    "TH": "Thueringen",
}


def build_payload(xlsx_path: Path) -> dict:
    df = pd.read_excel(xlsx_path, sheet_name="Kreisfreie Städte u. Landkreise", header=1)
    df = df.iloc[2:].copy()
    df = df[[df.columns[0], df.columns[1], df.columns[2]]]
    df.columns = ["code", "type", "name"]

    codes: dict[str, dict] = {}
    index_by_base_state_type: dict[str, str] = {}
    for _, row in df.iterrows():
        try:
            code = str(int(row["code"])).zfill(5)
        except Exception:
            continue
        if len(code) != 5 or code[:2] not in STATE_MAP:
            continue

        type_label = str(row["type"]).strip()
        name = str(row["name"]).strip()
        kreis_type = "stadt" if "stadt" in type_label.lower() else "landkreis"
        state_code = STATE_MAP[code[:2]]
        rec = {
            "code": code,
            "bundesland_code": state_code,
            "bundesland_name": STATE_NAMES[state_code],
            "type": kreis_type,
            "destatis_type_label": type_label,
            "name": name,
            "name_normalized": norm_kreis(name),
            "base_name_normalized": norm_kreis_basis(name),
        }
        codes[code] = rec
        idx_key = f"{rec['base_name_normalized']}|{state_code}|{kreis_type}"
        index_by_base_state_type[idx_key] = code

    return {
        "metadata": {
            "source": "Destatis – Kreisfreie Städte und Landkreise am 31.12.2024",
            "source_url": "https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Administrativ/04-kreise.xlsx?__blob=publicationFile",
            "generated_from": xlsx_path.name,
            "n_codes": len(codes),
        },
        "codes": codes,
        "index_by_base_state_type": index_by_base_state_type,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/convert_destatis_kreise_to_json.py /path/to/04-kreise.xlsx [output.json]")
        return 2
    xlsx = Path(sys.argv[1])
    output = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path("src/spittelmeister_windlast/daten/admin_kreise_codes.json")
    payload = build_payload(xlsx)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {output} with {payload['metadata']['n_codes']} codes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
