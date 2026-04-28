# Architektur-Scaffold für die Integration Windlast → Verankerung

Dieser Stand ist bewusst **additiv** aufgebaut. Das bestehende Verhalten der Windlast-App
und des Legacy-Reports bleibt erhalten. Gleichzeitig wird die neue Zielarchitektur
vorbereitet, damit die eigentliche Migration in kleinen Schritten erfolgen kann.

## Neue Bausteine

- `.agents/skills/spittelmeister-latex/SKILL.md`
- `.agents/skills/spittelmeister-report/SKILL.md`
- `src/spittelmeister_windlast/transfer/*`
- `src/spittelmeister_windlast/verankerung/*`
- `src/spittelmeister_windlast/projectio/*`
- `src/spittelmeister_windlast/api.py`
- `src/spittelmeister_windlast/ui/*`
- `src/spittelmeister_windlast/report/base.py`
- `src/spittelmeister_windlast/report/protokoll_windlast.py`
- `src/spittelmeister_windlast/report/protokoll_verankerung.py`
- `src/spittelmeister_windlast/report/report_selection.py`
- `src/spittelmeister_windlast/report/report_combined.py`
- `src/spittelmeister_windlast/report/report_bundle.py`
- `src/spittelmeister_windlast/report/report_figures.py`
- `apps/streamlit_app/pages/*`

## Leitidee

1. `core` bleibt der reine EC1-Rechenkern.
2. `api` stellt den stabilen Minimalvertrag fuer externe Automatisierung bereit:
   `spittelmeister_windlast.api.calculate_balcony_wind(...)` liefert `qw`,
   `wch_S`, `wch_F`, `AW_yz`, `AW_xz`, `Hx_d_ges`, `Hy_d_ges` und `gamma_w`
   ohne Streamlit-, CLI- oder Report-Abhaengigkeit.
3. `transfer` übernimmt die Ableitung von Anschlusslasten aus Wind-Ergebnissen.
4. `verankerung` kapselt Dokumentation, Vorprüfung und spätere Hersteller-/EN-1992-4-Logik.
5. `report` wird in modulare Berichtsteile zerlegt.
6. `projectio` und `ui` schaffen Projektzustand, YAML/JSON-Persistenz und eine spätere Multipage-App.

## Empfohlene nächste Commit-Reihenfolge

### Commit 1
- `report/base.py` aktiv nutzen
- Legacy-`report/latex.py` unangetastet lassen
- `protokoll_windlast.py` schrittweise aus dem Legacy-Report heraus entwickeln

### Commit 2
- `ui/project_ui.py` in `apps/streamlit_app/app.py` einbinden
- `projectio/service.py` für Download/Upload des Projektzustands anschließen

### Commit 3
- `apps/streamlit_app/pages/01_Windlast.py` produktiv machen
- `apps/streamlit_app/app.py` auf Shell/Startseite reduzieren

### Commit 4
- `_berechne_reaktionen_vereinfacht(...)` aus `core/berechnung.py` nach `transfer/vereinfachtes_balkonsystem.py` verschieben
- `core/berechnung.py` nur noch Wrapper oder Deprecation-Hinweis

### Commit 5
- `pages/02_Verankerung.py` produktiv ausbauen
- `protokoll_verankerung.py` mit echtem Assessment koppeln

## Bewusste Grenzen des Scaffolds

- kein vollständiger EN-1992-4-Nachweis
- keine automatische PROFIS/Hilti-Parserlogik
- kein produktiver Combined-Report mit allen Legacy-Inhalten
- keine harte Ablösung der bisherigen App

Der Scaffold soll die Repo **umorganisierbar** machen, nicht schon alles fertig rechnen.
