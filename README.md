# spittelmeister-windlast

**Windlastermittlung fuer Balkonabschluesse nach DIN EN 1991-1-4 / NA:2010-12**
Spittelmeister GmbH · Statik-Abteilung · Pforzheim

---

## Ueberblick

Python-Paket zur automatisierten Berechnung von Windlasten auf geschlossene
Balkonabschluesse (Fassadenelemente). Deckt den vollstaendigen Berechnungsweg
nach Eurocode 1 ab — von der Standortermittlung ueber den
Boeengeschwindigkeitsdruck bis zu den massgebenden Schnittgroessen je
Verankerungsfeld — und exportiert das Ergebnis als druckfertiges PDF-Dokument.

**v2.0** — modularisiert. Der Rechenkern ist jetzt unabhaengig von Streamlit,
Requests und LaTeX und kann von anderen Projekten (z. B. `balkonsystem`)
direkt konsumiert werden.

---

## Architektur

Drei Schichten, unabhaengig voneinander verwendbar:

| Schicht | Inhalt | Zusatzabhaengigkeiten |
|---------|--------|-----------------------|
| `spittelmeister_windlast.core`   | Reiner EC1-Rechenkern (qp, cpe,10, Berechnung) | keine — nur stdlib |
| `spittelmeister_windlast.geo`    | Standortermittlung (Nominatim, Elevation, Windzone-Lookup) | `requests` |
| `spittelmeister_windlast.report` | LaTeX/PDF-Export | `pdflatex` (System, Env oder Portable-MiKTeX) |
| `spittelmeister_windlast.daten`  | Normative Tabellen (JSON, im Paket ausgeliefert) | — |

```
spittelmeister-windlast/
├── pyproject.toml
├── src/spittelmeister_windlast/
│   ├── __init__.py              # Oeffentliche API
│   ├── cli.py                   # Headless-CLI
│   ├── core/                    # EC1-Rechenkern
│   │   ├── modelle.py           # Projekt, Standort, Geometrie, Ergebnisse
│   │   ├── peak_pressure.py     # qp(z) nach NA.B.3
│   │   ├── druckbeiwerte.py     # cpe,10 Interpolation
│   │   └── berechnung.py        # WindlastBerechnung
│   ├── geo/                     # Standortermittlung
│   │   ├── geocoding.py         # Nominatim
│   │   ├── elevation.py         # open-elevation + Fallback
│   │   ├── windzone.py          # Lookup PLZ > Praefix > Kreis > Bundesland
│   │   ├── gelaende.py          # Heuristik Kueste / Binnen
│   │   └── pipeline.py          # standort_ermitteln()
│   ├── daten/                   # Normative Tabellen (JSON)
│   │   ├── qb0.json
│   │   ├── windzone_kreis.json
│   │   ├── windzone_plz.json
│   │   ├── windzone_plz_prefix.json
│   │   └── windzone_bundesland.json
│   ├── report/                  # PDF-Export (optional)
│   │   └── latex.py
│   └── utils/
│       └── latex_escape.py
├── apps/streamlit_app/          # Streamlit-Web-UI
│   └── app.py
├── scripts/                     # Beispiele
│   └── example_headless.py
└── tests/                       # pytest
```

---

## Normative Grundlage

| Norm | Inhalt |
|------|--------|
| DIN EN 1991-1-4:2010-12 | Eurocode 1 – Windlasten |
| DIN EN 1991-1-4/NA:2010-12 | Nationaler Anhang Deutschland |
| Tabelle NA.A.1 | Windzonenzuordnung |
| Abschnitt NA.B.3 | Boeengeschwindigkeitsdruck qp(z) |
| Abschnitt 7.2 | Aussendruckbeiwerte vertikale Waende |

> **Gueltigkeitsbereich:** geschlossene Balkonabschluesse, ze ≤ 25 m (fuer cscd=1,0).
> qp-Ansatz gueltig bis z ≤ 300 m.
> Stirnseiten, Randfelder (Aref ≤ 1 m², cpe,1) und Fassadenbekleidung sind
> gesondert nachzuweisen.

---

## Development setup

`uv` ist die Quelle für lokale Umgebung, Extras und Lockfile. Es gibt kein
`requirements.txt` als Dependency-Quelle.

### Voraussetzungen

- Python ≥ 3.10
- `uv`
- TeX Live nur für PDF-Export:

```bash
sudo apt install texlive-latex-base texlive-latex-extra texlive-fonts-recommended
```

`uv` installieren:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Standard-Setup

```bash
uv sync --all-extras --dev
uv run pytest -q -m "not network"
uv run ruff check src/spittelmeister_windlast --select=E,F,W,B --ignore=E501
```

Alternativ über `make`:

```bash
make sync
make test
make lint
# make typecheck bleibt manual review required; siehe docs/audits/uv_migration_report.md
```

### Als Bibliothek für lokale Nachbar-Repos

```bash
uv sync --all-extras --dev
uv run python scripts/example_headless.py
```

Ein Legacy-`pip install -e .` Pfad ist nicht mehr der dokumentierte Standard.
Falls ein Altsystem pip erzwingt, muss der Pip-Export ausdrücklich aus dem
Lockfile abgeleitet und als Kompatibilitätsartefakt behandelt werden.

### Streamlit-App starten

```bash
uv sync --extra app --dev
uv run streamlit run apps/streamlit_app/app.py
```

### Lockfile und Dependencies

```bash
uv lock
uv lock --check
uv add requests --optional geo
uv add --dev pytest
```

## Verwendung als Bibliothek

### Stabile Minimal-API fuer Automatisierung

Fuer `balkon-automation` und andere schlanke Integrationen gibt es eine
kleine, stabile API ohne Streamlit-, CLI- oder Report-Abhaengigkeit:

```python
from spittelmeister_windlast.api import calculate_balcony_wind

result = calculate_balcony_wind(
    geometry={
        "B1": 3.94,
        "T": 1.94,
        "HW_Seite": 1.10,
        "HW_Front": 1.10,
    },
    qw=0.8,
    cpe_parallel=0.5,
    cpe_normal=0.7,
    gamma_w=1.5,
)

print(result.Hx_d_ges, result.Hy_d_ges)
```

Der Rueckgabewert ist eine Dataclass mit den stabilen Feldern `qw`,
`wch_S`, `wch_F`, `AW_yz`, `AW_xz`, `Hx_d_ges`, `Hy_d_ges` und `gamma_w`.
Der Legacy-Alias `calculate_wind(...)` bleibt fuer bestehende Adapter
verfuegbar; neue Integrationen sollen `calculate_balcony_wind(...)` nutzen.

### Vollstaendige API (Rechenkern)

```python
from spittelmeister_windlast import (
    WindlastBerechnung, Projekt, Standort, Geometrie,
)

wb = WindlastBerechnung(
    Projekt("Hochpunkt M Mannheim", "2025-WB-042", "S. Montero"),
    Standort("Wuerzburg", windzone=1, gelaende="binnen", hoehe_uNN=192.0),
    Geometrie(
        h=15.13, d=12.55, b=20.0,
        z_balkon=12.83, e_balkon=1.425,
        h_abschluss=3.00, s_verankerung=4.93,  # s_verankerung = Balkonbreite B
    ),
)
erg = wb.berechnen()
print(f"Hk = {erg.Hk:.2f} kN, Mk = {erg.Mk:.2f} kNm")
```

### Standort aus Adresse

```python
from spittelmeister_windlast.geo import standort_ermitteln

r = standort_ermitteln("Marktplatz 1, 97070 Wuerzburg")
print(r.windzone, r.hoehe_uNN, r.gelaende, r.windzone_quelle)
```

### PDF-Export

```python
from spittelmeister_windlast.report import export_pdf

export_pdf("windlast_wuerzburg.pdf", wb.projekt, wb.standort, wb.geo, erg)
```

### Integration in `balkonsystem`

```python
# balkonsystem/module/windlast.py
from spittelmeister_windlast.core import (
    WindlastBerechnung, Projekt, Standort, Geometrie,
)

# Keine requests-, keine Streamlit-, keine LaTeX-Abhaengigkeit im Kern.
```

---

## CLI

```bash
spittelmeister-windlast calc \
    --projekt "Demo" --nummer 2026-001 --bearbeiter "S. Montero" \
    --standort Wuerzburg --windzone 1 --gelaende binnen --hoehe-unn 192 \
    --h 15.13 --d 12.55 --b 20.0 --z-balkon 12.83 \
    --e-balkon 1.425 --h-abschluss 3.00 --s-verankerung 4.93 \
    --pdf /tmp/windlast.pdf --json
```

---

## Projektzustand / YAML-Persistenz

- Der Sidebar-Export `Projektzustand herunterladen` schreibt die aktuellen Eingaben aus dem Windlast-Modul mit.
- Gebäude- und Balkongeometrie werden auch ohne vorherige Berechnung persistent im YAML gehalten.
- Ein vorhandener Ergebnissnapshot bleibt bei reinen Geometrie-/Standortänderungen erhalten, bis neu gerechnet wird.

---

## Entwicklung

Die Entwicklungsbefehle laufen über `uv`:

```bash
uv sync --all-extras --dev
uv run pytest -q -m "not network"
uv run ruff check src/spittelmeister_windlast --select=E,F,W,B --ignore=E501
uv lock --check

# Optional/manual: aktuell nicht gruen ohne Type-Fixes
uv run mypy src/spittelmeister_windlast
```

`requirements.txt` existiert in dieser Repo nicht als Quelle der Wahrheit.

---

## Einschraenkungen / Bekannte Limitierungen

| Einschraenkung | Hinweis |
|----------------|---------|
| cscd > 1,0 | Gesonderter Schwingungsnachweis erforderlich (ValueError) |
| Windzone 2* | Spezialzone nicht im Lookup enthalten |
| Randfelder (Aref ≤ 1 m²) | cpe,1 wird nicht automatisch berechnet |
| Gelaendekategorie | Heuristik basierend auf Kreis/Bundesland; manuelle Korrektur empfohlen |

---

## Migration von v1.x (flaches Layout)

Alte Imports:
```python
from windlast_generator import WindlastBerechnung, Projekt, Standort, Geometrie
from geo_standort import standort_ermitteln
```

Neue Imports:
```python
from spittelmeister_windlast import WindlastBerechnung, Projekt, Standort, Geometrie
from spittelmeister_windlast.geo import standort_ermitteln
```

Die Legacy-Funktionen `berechne_qp_ausfuehrlich()` und `interpolate_cpe_excel()`
sind als Re-Exports verfuegbar und geben dieselben Werte wie zuvor zurueck.

---

## Lizenz / Intern

> **Internes Werkzeug der Spittelmeister GmbH.**
> Nicht fuer die Weitergabe an Dritte bestimmt. Berechnungsergebnisse sind
> durch einen zugelassenen Tragwerksplaner zu pruefen und zu verantworten.

---

*Statik-Abteilung Spittelmeister GmbH · v2.1*
# spm-windlast


## Amtliche Gebietscodes / future-proof registry

Zusatzlich zu den normativen Wind- und Schneetabellen enthaelt das Paket jetzt eine hazard-neutrale Verwaltungsschicht auf Basis amtlicher Destatis-Kreiscodes. Damit koennen Lookups robuster ueber 5-stellige Kreisschluessel oder 8-stellige AGS/Gemeindeschluessel laufen und spaeter auch weitere Kartenwerke (z. B. Seismik) auf derselben Verwaltungseinheit aufsetzen.


## Verwaltungs- und Erdbeben-Datenschicht (Vorbereitung fuer Seismik)

Zusätzlich zu Wind- und Schneelasttabellen enthält die Repo jetzt eine
gefahrdungsneutrale Verwaltungsschicht über amtliche Kreis-/Gemeindeschlüssel
und ein integriertes Erdbeben-Dataset aus dem bereitgestellten Excel-
Tabellenwerk.

Neu:
- `daten/erdbebenzonen_dataset.json`
- `geo.get_erdbeben_coverage(...)`
- `geo.get_erdbeben_records(...)`

Wichtige Besonderheit:
- Baden-Württemberg (`BW`) ist im gelieferten Tabellenwerk **explizit** als
  Verweisfall geführt und nicht tabellarisch aufgelöst. Die Repo speichert
  diesen Status bewusst als `external_map_only`, statt stillschweigend „keine
  Daten“ zu melden. Dadurch bleibt die Datenbasis auch für zukünftige
  Seismik-Lookups ehrlich und belastbar.

Kurz gesagt:
- `BW` -> expliziter Kartenverweis / kein stilles Loch in der Datenbank
- `NW` -> externer Kartenverweis laut Tabellenwerk
- `BY`, `HE`, `RP`, `TH`, `SN`, `ST` -> tabellarische Datensätze integriert


## Legacy-PDF-Assets

Die LaTeX-Berichte priorisieren die historischen PDF-Skizzen in `assets/` (`wind_geb.pdf`, `balcony_system.pdf`, `load_scheme.pdf`, `reaction_scheme.pdf`). Die zugehörigen TikZ-/TeX-Dateien bleiben als Fallback in der Repo.
