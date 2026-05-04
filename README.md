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

## Installation und Entwicklung: `uv` und `pip`

### Zielbild

Diese Repo soll mit zwei sauberen Installationspfaden funktionieren:

1. **`uv` als Standard fuer Entwicklung und reproduzierbare lokale Umgebungen.**
   `uv.lock` bleibt der Lockfile-Pfad fuer Entwickler, Tests und CI.
2. **`pip` als Kompatibilitaetspfad fuer klassische Python-Umgebungen.**
   `pip` installiert direkt aus `pyproject.toml`; ein handgepflegtes
   `requirements.txt` ist nicht die Quelle der Wahrheit.

Aktueller Stand der Repo:

| Thema | Status | Konsequenz |
|-------|--------|------------|
| Paketlayout | `src/`-Layout mit `pyproject.toml` | kompatibel mit `uv` und `pip` |
| Build-Backend | `hatchling` | `pip install .` baut ueber PEP-517/518 |
| Runtime-Core | `pyyaml>=6.0` | `pip install -e .` reicht fuer Headless-Core |
| Optionale Extras | `geo`, `app`, `all` | `uv --extra ...` und `pip .[extra]` moeglich |
| Dev-Tools | `[dependency-groups].dev` | `uv sync --dev`; mit modernem `pip` auch `--group dev` |
| Lockfile | `uv.lock` | nur `uv`; `pip` nutzt keine `uv.lock`-Aufloesung |

**Regel:** Neue Abhaengigkeiten werden zuerst in `pyproject.toml` gepflegt.
`uv.lock` wird daraus aktualisiert. Falls ein altes Deployment zwingend ein
`requirements.txt` braucht, wird es aus `uv.lock` exportiert und nicht manuell
editiert.

### Plan de trabajo / Arbeitsplan fuer echte Doppelkompatibilitaet

1. **Quelle der Wahrheit fixieren.**
   `pyproject.toml` bleibt die einzige gepflegte Dependency-Quelle:
   `project.dependencies` fuer Core, `project.optional-dependencies` fuer
   optionale Features, `[dependency-groups].dev` fuer Entwicklung.
2. **`uv`-Pfad prueffaehig halten.**
   CI und lokale Standardbefehle laufen mit `uv sync --all-extras --dev --frozen`,
   `uv lock --check`, `uv run pytest ...` und `uv run ruff ...`.
3. **`pip`-Pfad prueffaehig halten.**
   Mindestens pro Release einmal testen:
   `python -m pip install -e .`, `python -m pip install -e ".[all]"` und,
   falls `pip>=25.1` verfuegbar ist, `python -m pip install --group dev`.
4. **OS-Matrix absichern.**
   Die gleichen Smoke-Checks unter Linux, Windows und macOS dokumentieren:
   Import, CLI, Headless-Beispiel, Streamlit-Start.
5. **Keine verdeckte Vermischung.**
   `uv.lock` ist fuer `uv`; `pip` bekommt entweder direkte `pyproject.toml`-
   Installation oder einen bewusst exportierten Requirements-Snapshot.
6. **Release-Artefakte optional bauen.**
   Fuer externe Weitergabe lieber Wheel bauen und installieren, statt die Repo
   roh zu kopieren.

---

## Voraussetzungen

### Alle Systeme

- Python `>=3.10`
- Git oder entpackte Repo
- Fuer PDF-Export: eine funktionierende LaTeX-Installation mit `pdflatex`

Empfohlene Schnellpruefung:

```bash
python --version
```

Unter Windows ist oft der Python Launcher verfuegbar:

```powershell
py --version
```

### Linux

Systempakete fuer PDF-Export, Beispiel Debian/Ubuntu:

```bash
sudo apt update
sudo apt install texlive-latex-base texlive-latex-extra texlive-fonts-recommended
```

### macOS

Python kann z. B. ueber den offiziellen Installer, Homebrew oder `uv python`
bereitgestellt werden. Fuer PDF-Export wird eine TeX-Distribution benoetigt,
z. B. MacTeX oder BasicTeX plus fehlende Pakete.

### Windows

Python aus dem offiziellen Installer oder ueber `winget` installieren. Fuer
PDF-Export wird z. B. MiKTeX oder TeX Live benoetigt. Falls `pdflatex` nicht im
`PATH` liegt, funktionieren die PDF-Tests und der PDF-Export nicht, der
Rechenkern aber schon.

---

## Setup mit `uv` empfohlen

### `uv` installieren

Linux/macOS:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Alternativ gehen auch Paketmanager wie Homebrew, WinGet oder Scoop.

### Linux/macOS: komplette Entwicklungsumgebung

```bash
cd spm-windlast
uv sync --all-extras --dev
uv run pytest -q -m "not network"
uv run ruff check src/spittelmeister_windlast --select=E,F,W,B --ignore=E501
uv run python scripts/example_headless.py
```

### Windows PowerShell: komplette Entwicklungsumgebung

```powershell
cd spm-windlast
uv sync --all-extras --dev
uv run pytest -q -m "not network"
uv run ruff check src/spittelmeister_windlast --select=E,F,W,B --ignore=E501
uv run python scripts/example_headless.py
```

### Nur Core ohne App-Extras

```bash
uv sync
uv run python scripts/example_headless.py
```

### Mit Streamlit-App

```bash
uv sync --extra app --dev
uv run streamlit run apps/streamlit_app/app.py
```

### Lockfile pflegen

```bash
uv lock
uv lock --check
uv add requests --optional geo
uv add --dev pytest
```

### Makefile-Kurzbefehle Linux/macOS

```bash
make sync
make test
make lint
make smoke
```

Unter Windows funktionieren die direkten `uv`-Befehle oben am robustesten.
`make` nur verwenden, wenn eine passende Make-Umgebung installiert ist.

---

## Setup mit `pip` Kompatibilitaetspfad

Der `pip`-Pfad ist fuer klassische virtuelle Umgebungen, IDEs, alte CI-Jobs
oder Systeme ohne `uv`. Er ist bewusst einfach gehalten.

### Linux/macOS: virtuelle Umgebung

```bash
cd spm-windlast
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

### Windows PowerShell: virtuelle Umgebung

```powershell
cd spm-windlast
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
```

Falls PowerShell die Aktivierung blockiert, fuer diese Shell erlauben:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Core installieren

Linux/macOS:

```bash
python -m pip install -e .
python scripts/example_headless.py
```

Windows PowerShell:

```powershell
py -m pip install -e .
py scripts\example_headless.py
```

### Mit optionalen Features installieren

Geo-Lookup:

```bash
python -m pip install -e ".[geo]"
```

Streamlit-App:

```bash
python -m pip install -e ".[app]"
streamlit run apps/streamlit_app/app.py
```

Alles zusammen:

```bash
python -m pip install -e ".[all]"
```

Windows PowerShell analog:

```powershell
py -m pip install -e ".[all]"
py -m streamlit run apps/streamlit_app/app.py
```

### Dev-Tools mit modernem `pip`

Ab `pip>=25.1` koennen Dependency-Groups aus `pyproject.toml` installiert
werden:

```bash
python -m pip install --group dev
python -m pytest -q -m "not network"
python -m ruff check src/spittelmeister_windlast --select=E,F,W,B --ignore=E501
```

Windows PowerShell:

```powershell
py -m pip install --group dev
py -m pytest -q -m "not network"
py -m ruff check src/spittelmeister_windlast --select=E,F,W,B --ignore=E501
```

### Dev-Tools mit altem `pip` Fallback

Falls `pip --group` nicht verfuegbar ist:

```bash
python -m pip install "pytest>=8.0" "pytest-cov>=5.0" "mypy>=1.10" "ruff>=0.5"
```

Windows PowerShell:

```powershell
py -m pip install "pytest>=8.0" "pytest-cov>=5.0" "mypy>=1.10" "ruff>=0.5"
```

### Requirements-Snapshot nur falls noetig

Nur fuer Altsysteme, die zwingend `requirements.txt` brauchen:

```bash
uv export --format requirements.txt --all-extras --dev -o requirements.lock.txt
python -m pip install -r requirements.lock.txt
python -m pip install -e . --no-deps
```

`requirements.lock.txt` ist dann ein exportiertes Kompatibilitaetsartefakt,
nicht die primaere Dependency-Quelle.

---

## Pruef- und Smoke-Befehle

```bash
# uv, reproduzierbarer Standard
uv sync --all-extras --dev --frozen
uv lock --check
uv run pytest -q -m "not network"
uv run ruff check src/spittelmeister_windlast --select=E,F,W,B --ignore=E501
uv run python scripts/example_headless.py

# pip, Kompatibilitaetspfad
python -m pip install -e ".[all]"
python -m pip install --group dev  # falls pip >= 25.1
python -m pytest -q -m "not network"
python scripts/example_headless.py
```

`mypy` ist weiterhin **manual review required** und aktuell nicht als gruenes
Pflichtgate dokumentiert:

```bash
uv run mypy src/spittelmeister_windlast
```

---

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

Der prueffaehige Standardpfad ist oben unter **Installation und Entwicklung: `uv` und `pip`** dokumentiert.

Kurzfassung:

```bash
# Standard: uv
uv sync --all-extras --dev
uv lock --check
uv run pytest -q -m "not network"
uv run ruff check src/spittelmeister_windlast --select=E,F,W,B --ignore=E501

# Kompatibilitaet: pip
python -m pip install -e ".[all]"
python -m pip install --group dev  # falls pip >= 25.1
python -m pytest -q -m "not network"
```

`requirements.txt` existiert in dieser Repo nicht als Quelle der Wahrheit. Falls noetig, wird ein Requirements-Snapshot aus `uv.lock` exportiert.

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
