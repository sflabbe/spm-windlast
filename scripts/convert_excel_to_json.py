#!/usr/bin/env python3
"""Konvertiert die offiziellen Excel-Tabellen (Wind- und Schneelastzonen
nach Verwaltungsgrenzen, Stand 2022-06-02) in die JSON-Formate des
spittelmeister_windlast-Pakets.

Erzeugt vier Dateien im Zielverzeichnis:
  - windzone_kreis.json              (flach: kreis_normalisiert -> WZ)
  - windzone_kreis_detail.json       (reich: Varianten, Bemerkung, Bundesland)
  - schneelastzone_kreis.json        (flach: kreis_normalisiert -> SLZ)
  - schneelastzone_kreis_detail.json (reich)

Konventionen:
  - "WZ dominant" = max(alle WZ des Kreises) -> konservativ fuer die Statik.
  - "SLZ dominant" ebenso, wobei '1a' und '2a' als Halbstufen behandelt werden:
    Reihenfolge 1 < 1a < 2 < 2a < 3.
  - Kreisnamen werden ueber die Normalisierung des Pakets
    (geo._normalize.norm_kreis) in lowercase + ohne Umlaute ueberfuehrt.
"""

from __future__ import annotations

import json
import re
import sys
from collections import OrderedDict, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

# Paket-interne Normalisierung wiederverwenden
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from spittelmeister_windlast.geo._normalize import norm_kreis  # noqa: E402

# ---------------------------------------------------------------------------
# Bundeslaender-Mapping (Code -> voller Name, fuer Sheet-Erkennung)
# ---------------------------------------------------------------------------
BUNDESLAENDER = {
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


def sheet_to_bundesland(sheet: str) -> str | None:
    """Extrahiert BL-Code aus Sheet-Namen wie 'SH (01)' oder 'BW(08)'."""
    m = re.match(r"\s*([A-Z]{2})\b", sheet)
    if m and m.group(1) in BUNDESLAENDER:
        return m.group(1)
    return None


def _kreis_type_from_ags(ags: str) -> str:
    """Aus dem Gemeindeschluessel (AGS, 8-stellig) ableiten, ob es sich um
    eine kreisfreie Stadt oder einen Landkreis handelt.

    AGS-Struktur: LLRKKGGG wobei:
        LL  = Bundesland (2-stellig)
        R   = Regierungsbezirk (1-stellig)
        KK  = Kreisschluessel (2-stellig)
        GGG = Gemeinde (3-stellig)

    Heuristik: Kreisfreie Staedte haben als Gemeinde-Suffix genau '000'
    (die ganze Stadt deckt den gesamten Kreis ab). Landkreise haben
    Gemeinden mit 3-stelligen Suffix != '000'.

    Beispiele:
        09162000 -> stadt    (Muenchen kreisfrei)
        09184112 -> landkreis (Gemeinde Aschheim im LK Muenchen)
    """
    s = str(ags).strip()
    if len(s) != 8 or not s.isdigit():
        return ""
    return "stadt" if s.endswith("000") else "landkreis"


# Prefixe, die im Kreisnamen direkt den Typ angeben
STADT_PREFIX_RE = re.compile(
    r"^(?:Kreisfreie\s+Stadt|Stadt\s+|SK\s+)(.+)$", re.IGNORECASE
)
LANDKREIS_PREFIX_RE = re.compile(
    r"^(?:Landkreis\s+|Kreis\s+|LK\s+)(.+)$", re.IGNORECASE
)


def _clean_kreis_with_type(kreis_raw: str, ags: str = "") -> tuple[str, str]:
    """Extrahiert aus einem Kreisnamen-String den reinen Ortsnamen und den Typ.

    Returns:
        (ortsname, typ) mit typ in {"stadt", "landkreis", ""}.

    Prioritaet:
        1. Expliziter Prefix im Namen ("Kreisfreie Stadt Dresden", "LK Gifhorn")
        2. AGS-Ableitung (Muenchen 09162 -> stadt, 09184 -> landkreis)
        3. Kein Typ (normaler Landkreis ohne Namenskollision)
    """
    name = kreis_raw.strip()

    m = STADT_PREFIX_RE.match(name)
    if m:
        return m.group(1).strip(), "stadt"

    m = LANDKREIS_PREFIX_RE.match(name)
    if m:
        return m.group(1).strip(), "landkreis"

    # Kein expliziter Prefix -> ggf. via AGS
    if ags:
        return name, _kreis_type_from_ags(ags)

    return name, ""


def _format_kreis_label(ortsname: str, typ: str, is_ambigue: bool) -> str:
    """Baut den Anzeige-Namen fuer den JSON-'name'-Key.

    Nur bei ambigen Namen (Muenchen, Karlsruhe ...) oder explizit typisierten
    Eintraegen wird der Typ angehaengt. Fuer eindeutige Namen (Dithmarschen)
    bleibt der Name unveraendert.
    """
    if not typ:
        return ortsname
    # Ambige Namen bekommen immer das Suffix, ansonsten nur wenn der Typ
    # explizit im Quelltext stand (sonst fuegen wir kein kuenstliches Label ein)
    if is_ambigue:
        suffix = "Stadt" if typ == "stadt" else "Landkreis"
        return f"{ortsname} ({suffix})"
    return ortsname


def _disambig_key(ortsname_normalized: str, typ: str, is_ambigue: bool) -> str:
    """Erzeugt den Lookup-Key fuer ambige Namen.

    'muenchen' (stadt)     -> 'muenchen stadt'
    'muenchen' (landkreis) -> 'muenchen landkreis'
    'dithmarschen' (_)     -> 'dithmarschen'  (nicht ambig, kein Suffix)
    """
    if not is_ambigue or not typ:
        return ortsname_normalized
    return f"{ortsname_normalized} {typ}"


# Ambigue Namen: Orte, die sowohl als kreisfreie Stadt als auch als Landkreis
# unter demselben Namen existieren.
AMBIGUE_KREISNAMEN = {
    "muenchen", "rosenheim", "wuerzburg", "ansbach", "bamberg", "bayreuth",
    "coburg", "hof", "kaufbeuren", "kempten", "landshut", "memmingen",
    "passau", "regensburg", "schwabach", "schweinfurt", "weiden",
    "aschaffenburg", "fuerth", "ingolstadt", "nuernberg", "straubing",
    "augsburg", "erlangen", "heilbronn", "karlsruhe", "kassel",
    "darmstadt", "frankfurt", "offenbach", "kaiserslautern", "trier",
    "osnabrueck", "oldenburg", "leipzig",
}


# ---------------------------------------------------------------------------
# Zonen-Ordnung (fuer die Bestimmung der "dominanten" Zone pro Kreis)
# ---------------------------------------------------------------------------
WIND_ORDER = {1: 1, 2: 2, 3: 3, 4: 4, "2*": 2.5}
SNOW_ORDER = {"1": 1, "1a": 1.5, "2": 2, "2a": 2.5, "3": 3, "3a": 3.5}


def parse_windzone_value(text: str) -> int | str | None:
    """Parst 'Windzone 3' / '3' / 3 / 'WZ 4' -> int."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return None
    s = str(text).strip()
    m = re.search(r"(\d)\s*\*?", s)
    if m:
        val = int(m.group(1))
        if "*" in s:
            return f"{val}*"
        return val
    return None


def parse_snowzone_value(text: str) -> str | None:
    """Parst '1a' / '2' / 'SLZ 3' / '3a' -> str.

    Gueltige Werte: '1', '1a', '2', '2a', '3', '3a' (Sonderregelung alpin).
    """
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return None
    s = str(text).strip().lower().replace("slz", "").strip()
    m = re.match(r"^([123][a]?)$", s)
    if m:
        return m.group(1)
    try:
        return str(int(float(s)))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Parser fuer Kreis-Namen aus narrativem Text
# ---------------------------------------------------------------------------
# Prae- und Suffixe, die NICHT zum Kreisnamen gehoeren.
# (?<![\w\-]) verhindert, dass "Kreis" am Ende eines Bindestrich-Kompositums wie
# "Alb-Donau-Kreis" matcht (da '-' direkt davor steht).
NOISE_WORDS = re.compile(
    r"(?<![\w\-])(Landkreise?|Kreise?|kreisfreie\s+Stadt|kreisfreie\s+Staedte|"
    r"Stadt|LK|SK|Regierungsbezirk|Land)\b\.?",
    re.IGNORECASE,
)
SEPARATORS = re.compile(r"\s*(?:,|;|\bund\b)\s*", re.IGNORECASE)


def extract_kreise(text: str) -> list[str]:
    """Aus 'Landkreise Aurich, Wittmund, Friesland und Cuxhaven,
    kreisfreie Stadt Emden' -> ['Aurich', 'Wittmund', 'Friesland',
    'Cuxhaven', 'Emden']."""
    if not text or pd.isna(text):
        return []
    # ':' trennt ggf. Einleitung, z. B. 'Regierungsbezirk Karlsruhe:'
    # -> vor dem Doppelpunkt ist Beschreibung, nach ':' nichts mehr.
    s = str(text)
    # Alles nach ':' abschneiden (nicht von Interesse fuer Kreise)
    if ":" in s:
        s = s.split(":", 1)[0]
    # Rauschen entfernen, bevor wir splitten
    s = NOISE_WORDS.sub(" ", s)
    parts = SEPARATORS.split(s)
    return [p.strip(" .,;") for p in parts if p.strip(" .,;")]


# ---------------------------------------------------------------------------
# WIND: Parser pro Sheet
# ---------------------------------------------------------------------------


def parse_wind_sheet_nrw(df: pd.DataFrame, bl: str) -> list[dict]:
    """NW-Stil: Landkreis | Gemeindeschluessel | Gemeinde | WZ (tabellarisch)."""
    records = []
    for _, row in df.iloc[3:].iterrows():
        landkreis, ags, gem, wz = row.values[:4]
        if pd.isna(landkreis) or pd.isna(wz):
            continue
        wz_val = parse_windzone_value(wz)
        if wz_val is None:
            continue
        lk_str = str(landkreis).strip()
        ags_str = str(ags).strip() if pd.notna(ags) else ""
        ortsname, typ = _clean_kreis_with_type(lk_str, ags_str)
        records.append({
            "bundesland": bl,
            "kreis_raw": lk_str,
            "ortsname": ortsname,
            "typ": typ,
            "windzone": wz_val,
            "gemeinden": str(gem).strip() if pd.notna(gem) else "",
            "ags": ags_str,
        })
    return records


def parse_wind_sheet_single_city(df: pd.DataFrame, bl: str) -> list[dict]:
    """Ein-Satz-Sheet (z. B. Hamburg): 'Das Stadtgebiet von X wird der Windzone N zugeordnet.'"""
    text = " ".join(str(v) for row in df.values for v in row if pd.notna(v))
    m = re.search(r"Windzone\s*(\d)", text)
    if not m:
        return []
    wz = int(m.group(1))
    name = BUNDESLAENDER[bl]
    return [{
        "bundesland": bl,
        "kreis_raw": name,
        "ortsname": name,
        "typ": "stadt",
        "windzone": wz,
        "gemeinden": f"Stadtgebiet {name}",
        "ags": "",
    }]


_NOISE_PHRASE_START = re.compile(
    r"^(?:ausser|au\u00dfer|soweit|einschl\b|jeweils|alle\b|und\s)",
    re.IGNORECASE,
)


def parse_wind_sheet_narrative(df: pd.DataFrame, bl: str) -> list[dict]:
    """Narratives Format: Subsektion | Kreis-Beschreibung | 'Windzone N' | Gemeinden.

    Auch Regierungsbezirke werden erfasst, damit fuer BW/BY keine Kreise
    verloren gehen, die nur ueber "Regierungsbezirk X: alle Gemeinden WZ Y"
    zugeordnet sind.
    """
    records = []
    active_kreise: list[str] = []
    for _, row in df.iterrows():
        vals = list(row.values) + [None] * (4 - len(row.values))
        _subsec, kreis_desc, wz_text, gemeinden = vals[:4]

        if pd.notna(kreis_desc) and str(kreis_desc).strip():
            desc = str(kreis_desc).strip()
            # Ueberspringe reine Bundesland-Ueberschrift wie "3 Niedersachsen"
            if re.match(r"^\d+\s+[A-Za-zÄÖÜäöüß\-]+$", desc):
                continue
            # Ueberspringe narrative Fortsetzungen ("außer den Gemeinden ...")
            if _NOISE_PHRASE_START.match(desc):
                continue
            # Regierungsbezirk wird als Pseudo-Kreis erfasst
            if "Regierungsbezirk" in desc:
                rb = desc.rstrip(":").strip()
                active_kreise = [rb]
            else:
                kreise = extract_kreise(desc)
                if kreise:
                    active_kreise = kreise
        wz_val = parse_windzone_value(wz_text)
        if wz_val is not None and active_kreise:
            gem_desc = str(gemeinden).strip() if pd.notna(gemeinden) else "alle Gemeinden"
            for kr in active_kreise:
                ortsname, typ = _clean_kreis_with_type(kr)
                records.append({
                    "bundesland": bl,
                    "kreis_raw": kr,
                    "ortsname": ortsname,
                    "typ": typ,
                    "windzone": wz_val,
                    "gemeinden": gem_desc,
                    "ags": "",
                })
    return records


def parse_wind(path: Path) -> list[dict]:
    xl = pd.ExcelFile(path)
    all_records = []
    for sheet in xl.sheet_names:
        bl = sheet_to_bundesland(sheet)
        if bl is None:
            continue
        df = pd.read_excel(path, sheet_name=sheet, header=None)
        if bl == "NW":
            recs = parse_wind_sheet_nrw(df, bl)
        elif bl == "HH":
            recs = parse_wind_sheet_single_city(df, bl)
        else:
            recs = parse_wind_sheet_narrative(df, bl)
        all_records.extend(recs)
    return all_records


# ---------------------------------------------------------------------------
# SCHNEE: Parser pro Sheet
# ---------------------------------------------------------------------------


def _find_header_row(df: pd.DataFrame, max_scan: int = 5) -> int:
    """Findet die Zeile, die Schluesselwoerter wie 'Landkreis' / 'Gemeinde'
    enthaelt. Standard: Zeile 0."""
    for i in range(min(max_scan, len(df))):
        row_text = " ".join(str(v).lower() for v in df.iloc[i].values if pd.notna(v))
        if ("landkreis" in row_text or "stadtkreis" in row_text) and (
            "gemeinde" in row_text or "schluessel" in row_text or "schlüssel" in row_text
        ):
            return i
    return 0


def _sheet_default_slz(df: pd.DataFrame) -> str | None:
    """Falls die erste Zeile 'Schneelastzone X' lautet (SN-Stil),
    ist X die Default-Zone fuer alle Eintraege des Sheets ohne eigene SLZ."""
    first = " ".join(str(v) for v in df.iloc[0].values if pd.notna(v))
    m = re.match(r"^\s*Schneelastzone\s*([123][a]?)\b", first)
    return m.group(1) if m else None


def parse_snow_sheet_tabular(df: pd.DataFrame, bl: str) -> list[dict]:
    """Tabellarisch: variable Header-Spalten. Wir finden den Header-Row
    dynamisch und Default-SLZ aus dem Sheet-Titel."""
    default_slz = _sheet_default_slz(df)
    header_row = _find_header_row(df)
    header = [str(v).lower().strip() if pd.notna(v) else "" for v in df.iloc[header_row].values]

    def col(name_fragment: str) -> int | None:
        for i, h in enumerate(header):
            if name_fragment in h:
                return i
        return None

    c_lk = col("landkreis") or col("stadtkreis") or col("kreis")
    c_ags = col("gemeinde-schlüssel") or col("gemeindeschlüssel") or col("schlüssel")
    # Gemeinde-Spalte != AGS-Spalte
    c_gem = None
    for i, h in enumerate(header):
        if ("gemeinde" in h and "schlüss" not in h and "teil" not in h) and i != c_ags:
            c_gem = i
            break
    c_slz = col("schneelast") or col("slz")
    c_fn = col("fußnote") or col("fussnote") or col("hinweis")

    records = []
    active_lk: str | None = None
    for _, row in df.iloc[header_row + 1:].iterrows():
        vals = row.values
        lk = vals[c_lk] if c_lk is not None and c_lk < len(vals) else None
        gem = vals[c_gem] if c_gem is not None and c_gem < len(vals) else None
        ags = vals[c_ags] if c_ags is not None and c_ags < len(vals) else None
        slz = vals[c_slz] if c_slz is not None and c_slz < len(vals) else None
        fn = vals[c_fn] if c_fn is not None and c_fn < len(vals) else None

        # SLZ ermitteln (explizit > Sheet-Default)
        slz_val = parse_snowzone_value(slz) if slz is not None else None
        if slz_val is None and default_slz:
            slz_val = default_slz
        if slz_val is None:
            continue

        # Landkreis-Kontext fortschreiben (Rohtext aus Excel)
        if pd.notna(lk) and str(lk).strip():
            lk_text = str(lk).strip()
            # Regierungsbezirk-Ueberschrift ueberspringen
            if ":" in lk_text and "Regierungsbezirk" in lk_text:
                continue
            # Narrative Fortsetzungen ("außer den Gemeinden X, Y ...") ueberspringen
            if _NOISE_PHRASE_START.match(lk_text):
                continue
            active_lk = lk_text

        if not active_lk:
            continue

        # Per-row Disambiguierung: Typ aus Prefix (oder AGS falls vorhanden)
        ags_clean = str(ags).strip() if pd.notna(ags) else ""
        ortsname, typ = _clean_kreis_with_type(active_lk, ags_clean)

        records.append({
            "bundesland": bl,
            "kreis_raw": active_lk,
            "ortsname": ortsname,
            "typ": typ,
            "gemeinde": str(gem).strip() if pd.notna(gem) else "",
            "ags": ags_clean,
            "slz": slz_val,
            "fussnote": str(fn).strip() if pd.notna(fn) else "",
        })
    return records


def parse_snow(path: Path) -> list[dict]:
    xl = pd.ExcelFile(path)
    all_records = []
    for sheet in xl.sheet_names:
        bl = sheet_to_bundesland(sheet)
        if bl is None:
            continue
        df = pd.read_excel(path, sheet_name=sheet, header=None)
        recs = parse_snow_sheet_tabular(df, bl)
        all_records.extend(recs)
    return all_records


# ---------------------------------------------------------------------------
# Aggregation: flat + detail
# ---------------------------------------------------------------------------


def dominant_wz(zonen: list[int | str]) -> int | str:
    """max() fuer Windzonen, '2*' als 2.5 einsortiert."""
    return max(zonen, key=lambda z: WIND_ORDER.get(z, 0))


def dominant_slz(zonen: list[str]) -> str:
    """max() fuer Schneelastzonen mit der Ordnung 1 < 1a < 2 < 2a < 3."""
    return max(zonen, key=lambda z: SNOW_ORDER.get(z, 0))


def build_wind_outputs(records: list[dict]) -> tuple[dict, dict]:
    """Aggregiert Wind-Records zu (flat_dict, detail_dict).

    Key-Logik analog build_snow_outputs:
      - Eindeutige Ortsnamen: Key = normalisierter Ortsname
      - Ambige Namen: Key = '<normalized> stadt' / '<normalized> landkreis'
    """
    by_key: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        ortsname = r["ortsname"]
        typ = r["typ"]
        ortsname_norm = norm_kreis(ortsname)
        if not ortsname_norm:
            continue
        is_ambigue = ortsname_norm in AMBIGUE_KREISNAMEN
        key = _disambig_key(ortsname_norm, typ, is_ambigue)
        by_key[key].append(r)

    flat = OrderedDict()
    detail = OrderedDict()
    for key in sorted(by_key):
        recs = by_key[key]
        zonen = [r["windzone"] for r in recs]
        wz_dom = dominant_wz(zonen)
        varianten_dict: dict = defaultdict(list)
        for r in recs:
            desc = r.get("gemeinden", "") or "alle Gemeinden"
            if desc not in varianten_dict[r["windzone"]]:
                varianten_dict[r["windzone"]].append(desc)
        varianten = [
            {
                "windzone": z,
                "gemeinden": v[0] if len(v) == 1 else v,
            }
            for z, v in sorted(varianten_dict.items(), key=lambda x: WIND_ORDER.get(x[0], 0))
        ]
        bls = sorted({r["bundesland"] for r in recs})
        typen = [r["typ"] for r in recs if r["typ"]]
        typ_main = max(set(typen), key=typen.count) if typen else ""
        ortsname_main = recs[0]["ortsname"]
        ortsname_norm = norm_kreis(ortsname_main)
        is_ambigue = ortsname_norm in AMBIGUE_KREISNAMEN
        display_name = _format_kreis_label(ortsname_main, typ_main, is_ambigue)

        flat[key] = wz_dom
        detail[key] = {
            "name": display_name,
            "typ": typ_main or None,
            "bundesland": bls[0] if len(bls) == 1 else bls,
            "windzone_dominant": wz_dom,
            "varianten": varianten,
        }

    metadata = {
        "source": "Windzonen nach Verwaltungsgrenzen",
        "stand": "2022-06-02",
        "norm": "DIN EN 1991-1-4/NA:2010-12, Anhang NA.A",
        "generated": date.today().isoformat(),
        "n_kreise": len(detail),
        "n_records": len(records),
        "hinweis_dominant": "windzone_dominant = max() aller im Kreis vorkommenden Windzonen (konservativ). Fuer Gemeinde-genaue Entscheidung siehe 'varianten' und ggf. die originale Tabelle.",
        "hinweis_ambige_namen": "Orte, die sowohl als kreisfreie Stadt als auch als Landkreis unter demselben Namen existieren, werden ueber 'name <typ>' disambiguiert.",
    }
    detail_with_meta = {"metadata": metadata, "kreise": detail}
    return flat, detail_with_meta


def build_snow_outputs(records: list[dict]) -> tuple[dict, dict]:
    """Aggregiert Schnee-Records zu (flat_dict, detail_dict).

    Key-Logik:
      - Eindeutige Ortsnamen (z. B. 'dithmarschen'): Key = 'dithmarschen'
      - Ambige Namen (z. B. 'muenchen'): Key = 'muenchen stadt' / 'muenchen landkreis'
        falls Typ aus Prefix/AGS bekannt ist; sonst faellt das in 'muenchen'.
    """
    by_key: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        ortsname = r["ortsname"]
        typ = r["typ"]
        ortsname_norm = norm_kreis(ortsname)
        if not ortsname_norm:
            continue
        is_ambigue = ortsname_norm in AMBIGUE_KREISNAMEN
        key = _disambig_key(ortsname_norm, typ, is_ambigue)
        by_key[key].append(r)

    flat = OrderedDict()
    detail = OrderedDict()
    for key in sorted(by_key):
        recs = by_key[key]
        zonen = [r["slz"] for r in recs]
        slz_dom = dominant_slz(zonen)
        # Varianten aggregieren
        varianten_dict: dict = defaultdict(list)
        for r in recs:
            desc = r.get("gemeinde", "") or "alle Gemeinden"
            if desc not in varianten_dict[r["slz"]]:
                varianten_dict[r["slz"]].append(desc)
        varianten = [
            {
                "slz": z,
                "gemeinden_beispiele": (
                    v if len(v) <= 5 else v[:5] + [f"... ({len(v)-5} weitere)"]
                ),
                "n_gemeinden": len(v),
            }
            for z, v in sorted(varianten_dict.items(), key=lambda x: SNOW_ORDER.get(x[0], 0))
        ]
        fussnoten = sorted({r["fussnote"] for r in recs if r.get("fussnote")})
        bls = sorted({r["bundesland"] for r in recs})
        # Typ des Eintrags (majority vote, meist homogen)
        typen = [r["typ"] for r in recs if r["typ"]]
        typ_main = max(set(typen), key=typen.count) if typen else ""
        ortsname_main = recs[0]["ortsname"]
        ortsname_norm = norm_kreis(ortsname_main)
        is_ambigue = ortsname_norm in AMBIGUE_KREISNAMEN
        display_name = _format_kreis_label(ortsname_main, typ_main, is_ambigue)

        flat[key] = slz_dom
        detail[key] = {
            "name": display_name,
            "typ": typ_main or None,
            "bundesland": bls[0] if len(bls) == 1 else bls,
            "slz_dominant": slz_dom,
            "varianten": varianten,
            "fussnoten": fussnoten,
        }

    metadata = {
        "source": "Schneelastzonen nach Verwaltungsgrenzen",
        "stand": "2022-06-02",
        "norm": "DIN EN 1991-1-3/NA",
        "generated": date.today().isoformat(),
        "zonen": ["1", "1a", "2", "2a", "3", "3a"],
        "n_kreise": len(detail),
        "n_records": len(records),
        "hinweis_dominant": "slz_dominant = hoechste im Kreis vorkommende Schneelastzone mit Ordnung 1 < 1a < 2 < 2a < 3 (konservativ). Fuer Gemeinde-Praezision siehe 'varianten' und Originaltabelle.",
        "hinweis_ambige_namen": "Orte, die sowohl als kreisfreie Stadt als auch als Landkreis unter demselben Namen existieren (z. B. Muenchen, Karlsruhe), werden ueber 'name <typ>' disambiguiert, z. B. 'muenchen stadt' und 'muenchen landkreis'.",
    }
    detail_with_meta = {"metadata": metadata, "kreise": detail}
    return flat, detail_with_meta


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    here = Path(__file__).resolve().parent
    uploads = Path("/mnt/user-data/uploads")
    out_dir = Path("/home/claude/out_json")
    out_dir.mkdir(exist_ok=True)

    wind_path = uploads / "Windzonen_nach_Verwaltungsgrenzen.xlsx"
    snow_path = uploads / "Schneelastzonen_nach_Verwaltungsgrenzen.xlsx"

    print("Parsing Wind...")
    wind_records = parse_wind(wind_path)
    print(f"  {len(wind_records)} records aus {len({r['bundesland'] for r in wind_records})} Bundeslaendern")
    wind_flat, wind_detail = build_wind_outputs(wind_records)
    print(f"  -> {len(wind_flat)} eindeutige Kreise (normalisiert)")

    print("\nParsing Schnee...")
    snow_records = parse_snow(snow_path)
    print(f"  {len(snow_records)} records aus {len({r['bundesland'] for r in snow_records})} Bundeslaendern")
    snow_flat, snow_detail = build_snow_outputs(snow_records)
    print(f"  -> {len(snow_flat)} eindeutige Kreise (normalisiert)")

    # Schreiben
    for name, obj in [
        ("windzone_kreis.json", wind_flat),
        ("windzone_kreis_detail.json", wind_detail),
        ("schneelastzone_kreis.json", snow_flat),
        ("schneelastzone_kreis_detail.json", snow_detail),
    ]:
        path = out_dir / name
        path.write_text(
            json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False),
            encoding="utf-8",
        )
        print(f"geschrieben: {path} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
