from __future__ import annotations

import streamlit as st

from spittelmeister_windlast.report import (
    ReportSelection,
    build_combined_runtime_data,
    compile_latex_to_pdf_bytes,
    create_report_zip_bundle,
    protokol_header_from_project_meta,
    render_combined_report,
)
from spittelmeister_windlast.ui.session import (
    load_latex_config_state,
    load_project_meta_state,
    load_report_selection_state,
    load_verankerung_state,
    load_wind_state,
    save_report_selection_state,
)

st.set_page_config(page_title="04 Protokoll", layout="wide")
st.title("04 · Protokoll")
st.caption("Combined Report aus gespeichertem Projektzustand: Windlast, Verankerung und Export-Bundle.")

saved = load_report_selection_state()
selection = ReportSelection()
selection.windlast.include = bool(saved.get("windlast", {}).get("include", True))
selection.verankerung.include = bool(saved.get("verankerung", {}).get("include", False))
selection.herstellernachweis.include = bool(saved.get("herstellernachweis", {}).get("include", False))

col_select, col_status = st.columns([2, 3], gap="large")
with col_select:
    st.subheader("Modulauswahl")
    selection.windlast.include = st.checkbox("Windlast aufnehmen", value=selection.windlast.include)
    selection.verankerung.include = st.checkbox("Verankerung aufnehmen", value=selection.verankerung.include)
    selection.herstellernachweis.include = st.checkbox(
        "Herstellernachweis aufnehmen", value=selection.herstellernachweis.include, disabled=True
    )

save_report_selection_state(
    windlast={"include": selection.windlast.include},
    verankerung={"include": selection.verankerung.include},
    herstellernachweis={"include": selection.herstellernachweis.include},
)

project_meta = load_project_meta_state()
wind_state = load_wind_state()
ver_state = load_verankerung_state()
runtime_data = build_combined_runtime_data(project_meta, wind_state, ver_state)
header = protokol_header_from_project_meta(project_meta)
tex_source = render_combined_report(header, selection, runtime_data)

with col_status:
    st.subheader("Projektstatus")
    st.write("Ausgewählte Module:", selection.selected_module_labels())
    st.caption(f"Projekt: {header.projekt_nr} · {header.projekt_bez}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Windlast-Snapshot", "ja" if runtime_data.windlast is not None else "nein")
    c2.metric("ConnectionActions", "ja" if runtime_data.connection_actions is not None else "nein")
    c3.metric("Verankerung-Bewertung", "ja" if runtime_data.anchorage_assessment is not None else "nein")

if selection.windlast.include and runtime_data.windlast is None:
    st.warning("Windlast wurde für den Bericht ausgewählt, aber es liegt noch kein gespeicherter Wind-Snapshot vor.")
if selection.verankerung.include and runtime_data.connection_actions is None:
    st.warning("Verankerung wurde ausgewählt, aber Anschlussgrößen konnten aus dem Projektzustand noch nicht rekonstruiert werden.")

st.subheader("Exports")
filename_stub = header.projekt_nr.replace(" ", "_") or "windlast_report"
tex_bytes = tex_source.encode("utf-8")
zip_bytes = create_report_zip_bundle(tex_source)

exp1, exp2, exp3 = st.columns(3)
with exp1:
    st.download_button(
        "TEX herunterladen",
        data=tex_bytes,
        file_name=f"{filename_stub}_combined.tex",
        mime="text/x-tex",
    )
with exp2:
    st.download_button(
        "ZIP-Bundle herunterladen",
        data=zip_bytes,
        file_name=f"{filename_stub}_combined_bundle.zip",
        mime="application/zip",
    )
with exp3:
    latex_cfg = load_latex_config_state()
    pdflatex_path = str(latex_cfg.get("pdflatex_path") or "pdflatex")
    if st.button("PDF kompilieren"):
        try:
            pdf_bytes = compile_latex_to_pdf_bytes(tex_source, pdflatex_executable=pdflatex_path)
            st.session_state["combined_pdf_bytes"] = pdf_bytes
            st.session_state["combined_pdf_name"] = f"{filename_stub}_combined.pdf"
            st.success("Combined PDF wurde erfolgreich kompiliert.")
        except Exception as exc:  # pragma: no cover - runtime/UI path
            st.session_state.pop("combined_pdf_bytes", None)
            st.session_state.pop("combined_pdf_name", None)
            st.error(f"PDF-Kompilierung fehlgeschlagen: {exc}")

if st.session_state.get("combined_pdf_bytes"):
    st.download_button(
        "Combined PDF herunterladen",
        data=st.session_state["combined_pdf_bytes"],
        file_name=st.session_state.get("combined_pdf_name", f"{filename_stub}_combined.pdf"),
        mime="application/pdf",
    )

with st.expander("LaTeX-Vorschau", expanded=False):
    st.code(tex_source[:12000], language="tex")
