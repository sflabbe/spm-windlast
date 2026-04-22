"""Projekt-Shell für die multipage Streamlit-App.

`streamlit run app.py` bleibt der Einstiegspunkt, aber die produktive Windlast-
Oberfläche lebt jetzt in `pages/01_Windlast.py`. Dieses Shell-Modul hält die
Projekt-Sidebar, zeigt den aktuellen Status und verweist auf die Module.
"""

from __future__ import annotations

import streamlit as st

from spittelmeister_windlast.ui.project_ui import build_project_document_from_state, render_project_sidebar
from spittelmeister_windlast.ui.windlast_page import _inject_page_css

st.set_page_config(
    page_title="Windlast-Projektshell | Spittelmeister",
    layout="wide",
    initial_sidebar_state="expanded",
)

_inject_page_css()
project_meta = render_project_sidebar()
doc = build_project_document_from_state()

with st.sidebar:
    st.markdown("---")
    st.caption("Navigation: Module über die Streamlit-Seitenleiste öffnen")

st.markdown("# Windlast-Projektshell")
st.markdown(
    "**Spittelmeister GmbH** · modulare Arbeitsoberfläche für Windlast, Verankerung "
    "und Berichtserstellung"
)
st.markdown("---")

st.info(
    "Die produktive Erfassungs- und Berechnungsmaske wurde nach "
    "**01 · Windlast** verschoben. Dieses Startmodul hält nur noch den Projektkontext."
)

c1, c2, c3 = st.columns(3)
c1.metric("Projekt", project_meta["project_id"] or "—")
c2.metric("Revision", project_meta["revision"] or "0")
c3.metric("Bearbeiter", project_meta["bearbeiter"] or "—")

m1, m2, m3 = st.columns(3)
m1.markdown(
    "### 01 · Windlast\n"
    "Geschäftslogik, Standortsuche, PDF-Export und Snapshot der Ergebnisse."
)
m2.markdown(
    "### 02 · Verankerung\n"
    "Übernimmt Reaktionen aus Windlast und dokumentiert/prechecked den Anschluss."
)
m3.markdown(
    "### 04 · Protokoll\n"
    "Wählt Module für den kombinierten Bericht aus und bereitet den Export vor."
)

st.markdown("## Aktueller Projektzustand")
status_cols = st.columns(3)
status_cols[0].write(
    f"**Windlast**: {'aktiv' if doc.modules['windlast'].enabled else 'leer'}"
)
status_cols[1].write(
    f"**Verankerung**: {'aktiv' if doc.modules['verankerung'].enabled else 'leer'}"
)
status_cols[2].write(
    f"**Herstellernachweis**: {'aktiv' if doc.modules['herstellernachweis'].enabled else 'leer'}"
)

if doc.modules["windlast"].results_snapshot:
    results = doc.modules["windlast"].results_snapshot
    p1, p2, p3 = st.columns(3)
    p1.metric("qp(h)", f"{float(results.get('qp', 0.0)):.3f} kN/m²")
    p2.metric("Hk je Feld", f"{float(results.get('Hk', 0.0)):.2f} kN")
    p3.metric("Mk Fußpunkt", f"{float(results.get('Mk', 0.0)):.2f} kNm")
else:
    st.caption("Noch keine Windlast-Ergebnisse im Projektzustand gespeichert.")

st.markdown("---")
st.caption(
    "Kompatibilität: `streamlit run app.py` bleibt gültig. Die funktionale UI lebt "
    "ab jetzt seitenbasiert unter `pages/` und wird dort weiter refaktoriert."
)
