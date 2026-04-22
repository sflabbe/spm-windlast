from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
from typing import Any

try:  # pragma: no cover
    import streamlit as st
except Exception:  # pragma: no cover
    st = None

from ..projectio.models import ModuleEntry, ProjectDocument, ProjectMetadata
from ..projectio.service import dump_project_document, load_project_document
from ..utils import resolve_pdflatex
from .session import (
    load_latex_config_state,
    load_project_meta_state,
    load_report_selection_state,
    load_verankerung_state,
    load_wind_state,
    save_latex_config_state,
    save_project_meta_state,
    save_report_selection_state,
    save_verankerung_state,
    save_wind_state,
)


def detect_pdflatex(explicit_path: str | None = None) -> str | None:
    return resolve_pdflatex(explicit_path)


def _parse_sidebar_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                pass
    return date.today()


def _build_project_meta_from_sidebar() -> ProjectMetadata:
    defaults = ProjectMetadata(**load_project_meta_state()) if load_project_meta_state() else ProjectMetadata()
    datum_default = _parse_sidebar_date(defaults.datum)
    datum_value = st.date_input("Datum", value=datum_default)
    return ProjectMetadata(
        project_id=st.text_input("Projektnummer", value=defaults.project_id),
        title=st.text_input("Projektbezeichnung", value=defaults.title),
        client=st.text_input("Auftraggeber", value=defaults.client),
        street=st.text_input("Straße", value=defaults.street),
        city=st.text_input("Ort", value=defaults.city),
        revision=st.text_input("Revision", value=defaults.revision),
        bearbeiter=st.text_input("Bearbeiter", value=defaults.bearbeiter),
        datum=datum_value.strftime("%d.%m.%Y"),
    )


def build_project_document_from_state() -> ProjectDocument:
    project_state = load_project_meta_state()
    wind_state = load_wind_state()
    verankerung_state = load_verankerung_state()
    report_state = load_report_selection_state()

    project = ProjectMetadata(**project_state) if project_state else ProjectMetadata()

    modules = {
        "windlast": ModuleEntry(
            enabled=bool(wind_state),
            input=dict(wind_state.get("input", {})),
            results_snapshot=dict(wind_state.get("results_snapshot", {})),
        ),
        "verankerung": ModuleEntry(
            enabled=bool(verankerung_state),
            input=dict(verankerung_state.get("input", {})),
            results_snapshot=dict(verankerung_state.get("results_snapshot", {})),
        ),
        "herstellernachweis": ModuleEntry(enabled=False),
    }
    report = {
        "selection": report_state or {
            "windlast": {"include": True},
            "verankerung": {"include": bool(verankerung_state)},
            "herstellernachweis": {"include": False},
        }
    }
    return ProjectDocument(project=project, modules=modules, report=report)


def apply_project_document_to_state(doc: ProjectDocument) -> None:
    save_project_meta_state(**asdict(doc.project))

    wind_entry = doc.modules.get("windlast")
    if wind_entry is not None:
        save_wind_state(
            input=dict(wind_entry.input),
            results_snapshot=dict(wind_entry.results_snapshot),
        )

    ver_entry = doc.modules.get("verankerung")
    if ver_entry is not None:
        save_verankerung_state(
            input=dict(ver_entry.input),
            results_snapshot=dict(ver_entry.results_snapshot),
        )

    selection = dict(doc.report.get("selection", {}))
    if selection:
        save_report_selection_state(**selection)


def render_project_sidebar() -> dict[str, Any]:
    if st is None:  # pragma: no cover
        raise RuntimeError("Streamlit ist für die Sidebar nicht verfügbar.")

    with st.sidebar:
        st.markdown("### Projekt")
        meta = _build_project_meta_from_sidebar()
        save_project_meta_state(**asdict(meta))

        st.markdown("---")
        st.markdown("### Persistenz")
        current_doc = build_project_document_from_state()
        doc_text = dump_project_document(current_doc)
        st.download_button(
            "Projektzustand herunterladen",
            data=doc_text.encode("utf-8"),
            file_name="windlast_projekt.yaml",
            mime="text/yaml",
        )

        uploaded = st.file_uploader("Projektzustand laden", type=["yaml", "yml", "json"])
        if uploaded is not None and st.button("Geladene Projektdatei übernehmen"):
            loaded = load_project_document(uploaded.getvalue().decode("utf-8"))
            apply_project_document_to_state(loaded)
            st.success(f"Projektdatei geladen: {loaded.project.title}")
            st.rerun()

        if st.button("Projektzustand zurücksetzen"):
            for key in (
                "project_meta",
                "wind_inp",
                "verankerung_inp",
                "report_selection",
                "latex_cfg",
                "generated_pdf_bytes",
                "generated_pdf_name",
                "generated_result",
                "generated_error",
                "geo_result",
                "auto_windzone",
                "auto_gelaende",
                "auto_hoehe_uNN",
                "auto_standort",
                "switch_to_calc",
            ):
                st.session_state.pop(key, None)
            st.rerun()

        st.markdown("---")
        st.markdown("### LaTeX")
        latex_state = load_latex_config_state()
        resolved_pdflatex = detect_pdflatex(str(latex_state.get("pdflatex_path") or ""))
        latex_default = str(latex_state.get("pdflatex_path") or resolved_pdflatex or "")
        latex_path = st.text_input("pdflatex-Pfad", value=latex_default)
        effective_pdflatex = detect_pdflatex(latex_path)
        save_latex_config_state(pdflatex_path=latex_path)
        if effective_pdflatex:
            st.caption(f"pdflatex aktiv: `{effective_pdflatex}`")
            if latex_path and latex_path != effective_pdflatex:
                st.info("Gespeicherter Pfad war nicht gueltig. Fallback-Autodetektion wird verwendet.")
        else:
            st.warning("pdflatex wurde nicht automatisch gefunden.")
            st.caption("Getestet werden PATH, Umgebungsvariablen und bekannte portable-MiKTeX-Pfade.")

    return asdict(meta)
