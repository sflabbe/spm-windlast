from __future__ import annotations

import streamlit as st

from spittelmeister_windlast.transfer import ConnectionActions, derive_connection_actions_from_snapshot, derive_support_action
from spittelmeister_windlast.ui.session import load_verankerung_state, load_wind_state, save_verankerung_state
from spittelmeister_windlast.ui.verankerung_consistency import analyze_verankerung_consistency, apply_consistency_quick_fixes
from spittelmeister_windlast.ui.verankerung_optimizer import apply_macro_to_state_input, suggest_anchorage_macro
from spittelmeister_windlast.ui.verankerung_preview import build_verankerung_feedback, render_assessment_badges, render_plan_preview_svg, render_side_preview_svg
from spittelmeister_windlast.verankerung import AnchorageInput, assess_anchorage


def _show_feedback_block(level: str, message: str) -> None:
    if level == "success":
        st.success(message)
    elif level == "warning":
        st.warning(message)
    else:
        st.error(message)


def _show_consistency_issue(severity: str, title: str, detail: str) -> None:
    text = f"**{title}** — {detail}"
    if severity == "error":
        st.error(text)
    elif severity == "warning":
        st.warning(text)
    else:
        st.info(text)


st.set_page_config(page_title="02 Verankerung", layout="wide")
st.title("02 · Verankerung")
st.caption(
    "Anschlussgrößen werden aus dem Windmodul übernommen und für eine strukturierte Vorprüfung des Anschlusses dokumentiert. "
    "Für Festlager/Gleitlager wird ein idealisiertes Stützstellenmodell mit Exzentrizität angesetzt."
)

wind_state = load_wind_state()
wind_input = wind_state.get("input", {})
wind_results = wind_state.get("results_snapshot", {})

try:
    actions = derive_connection_actions_from_snapshot(wind_input, wind_results)
    action_error = None
except Exception as exc:
    actions = ConnectionActions()
    action_error = str(exc)

saved_state = load_verankerung_state()
saved_input = dict(saved_state.get("input", {}))
anchorage_default = AnchorageInput.from_mapping(saved_input)

try:
    support_action_default = derive_support_action(
        actions,
        support_index=anchorage_default.support_index,
        support_role=anchorage_default.support_role,
        slide_direction=anchorage_default.slide_direction,
        local_eccentricity_mm=anchorage_default.local_eccentricity_mm,
        platform_eccentricity_mm=float(anchorage_default.platform_eccentricity_mm or 0.0),
    )
except Exception:
    support_action_default = None

with st.expander("Auto-Optimierungsmakro (optional)", expanded=False):
    st.caption("Heuristische Startgeometrie für die Vorprüfung. Das Makro schlägt Randabstände, Achsabstände und Plattenabmessungen vor, ersetzt aber keinen normativen Nachweis und keine Herstellerbemessung.")
    macro = suggest_anchorage_macro(anchorage_default, support_action_default, actions)
    for line in macro.summary_lines:
        st.write(f"- {line}")
    st.info(macro.note_line)
    if st.button("Makro-Vorschlag in Eingabedaten übernehmen", type="secondary", use_container_width=True):
        new_input = apply_macro_to_state_input(saved_input, macro)
        save_verankerung_state(input=new_input, results_snapshot=saved_state.get("results_snapshot", {}))
        st.rerun()

with st.expander("Konsistenz-Kurzcheck (optional)", expanded=False):
    default_consistency = analyze_verankerung_consistency(anchorage_default, support_action_default, actions)
    _show_feedback_block(default_consistency.level, default_consistency.summary)
    if default_consistency.issues:
        for issue in default_consistency.issues:
            _show_consistency_issue(issue.severity, issue.title, issue.detail)
    else:
        st.success("Für die aktuelle Eingabekonfiguration wurden keine offensichtlichen Inkonsistenzen erkannt.")
    if default_consistency.quick_fixes:
        st.caption("Für einige Inkonsistenzen stehen heuristische Quick Fixes bereit. Diese sind UI-Hilfen, kein normativer Nachweis.")
        if st.button("Quick Fixes in Eingabedaten übernehmen", type="secondary", use_container_width=True):
            new_input = apply_consistency_quick_fixes(saved_input, default_consistency)
            save_verankerung_state(input=new_input, results_snapshot=saved_state.get("results_snapshot", {}))
            st.rerun()

col_left, col_right = st.columns([2, 3], gap="large")

with col_left:
    st.subheader("Anschlussdaten")
    top1, top2 = st.columns(2)
    with top1:
        connection_label = st.text_input("Bezeichnung", value=anchorage_default.connection_label)
    with top2:
        support_type = st.text_input("Untergrund / Bauteil", value=anchorage_default.support_type)
    substrate_strength_class = st.text_input("Materialgrundlage / Festigkeitsklasse", value=anchorage_default.substrate_strength_class, help="z. B. C20/25, Mauerwerk unbekannt, Bestandsdecke mit Probebelastung.")

    with st.expander("Lagerkinematik und Exzentrizität", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            support_index = st.selectbox("Stützstelle", [1, 2], index=max(min(anchorage_default.support_index, 2), 1) - 1)
            support_role = st.selectbox("Lagerrolle", ["festlager", "gleitlager"], index=["festlager", "gleitlager"].index(anchorage_default.support_role))
            slide_direction = st.selectbox("Gleitrichtung", ["x", "y"], index=["x", "y"].index(anchorage_default.slide_direction), help="Nur relevant für Gleitlager. x = Freigabe in Hx-Richtung, y = Freigabe in Hy-Richtung.", disabled=support_role != "gleitlager")
        with c2:
            platform_eccentricity_mm = st.number_input("Plattform-Exzentrizität [mm]", min_value=0.0, value=float(anchorage_default.platform_eccentricity_mm or 0.0), step=5.0, help="Zusätzlicher Hebel zwischen Plattformresultierenden und betrachteter Stützstelle.")
            wdvs_mm = st.number_input("WDVS [mm]", min_value=0.0, value=float(anchorage_default.wdvs_mm or 0.0), step=5.0)
            spalt_mm = st.number_input("Spalt [mm]", min_value=0.0, value=float(anchorage_default.spalt_mm or 0.0), step=2.0)
            bracket_offset_mm = st.number_input("Konsolen-/Laschenhebel [mm]", min_value=0.0, value=float(anchorage_default.bracket_offset_mm or 0.0), step=5.0)
            anchor_plane_offset_mm = st.number_input("Ankerachsenabstand [mm]", min_value=0.0, value=float(anchorage_default.anchor_plane_offset_mm or 0.0), step=5.0)
        st.caption("Faustregel: e_local = WDVS + Spalt + Konsole + Abstand zur Ankerachse. e_platform ergänzt den Hebel zwischen Plattformresultierenden und betrachteter Stützstelle.")

    with st.expander("Ankergruppe und Anschlussplatte", expanded=True):
        a1, a2 = st.columns(2)
        with a1:
            anchor_designation = st.text_input("Ankerbezeichnung", value=anchorage_default.anchor_designation)
            anchor_count = st.number_input("Anzahl Verankerungen", min_value=1, value=int(anchorage_default.anchor_count))
            plate_width = st.number_input("Plattenbreite [mm]", min_value=0.0, value=float(anchorage_default.plate_width_mm or 0.0), step=5.0)
            plate_height = st.number_input("Plattenhöhe [mm]", min_value=0.0, value=float(anchorage_default.plate_height_mm or 0.0), step=5.0)
            plate_thickness = st.number_input("Plattendicke [mm]", min_value=0.0, value=float(anchorage_default.plate_thickness_mm or 0.0), step=1.0)
        with a2:
            edge_left = st.number_input("Randabstand links [mm]", min_value=0.0, value=float(anchorage_default.edge_distances_mm.get("left", 0.0)), step=5.0)
            edge_right = st.number_input("Randabstand rechts [mm]", min_value=0.0, value=float(anchorage_default.edge_distances_mm.get("right", 0.0)), step=5.0)
            edge_top = st.number_input("Randabstand oben [mm]", min_value=0.0, value=float(anchorage_default.edge_distances_mm.get("top", 0.0)), step=5.0)
            edge_bottom = st.number_input("Randabstand unten [mm]", min_value=0.0, value=float(anchorage_default.edge_distances_mm.get("bottom", 0.0)), step=5.0)
            spacing_x = st.number_input("Achsabstand x [mm]", min_value=0.0, value=float(anchorage_default.spacing_mm.get("x", 0.0)), step=5.0)
            spacing_y = st.number_input("Achsabstand y [mm]", min_value=0.0, value=float(anchorage_default.spacing_mm.get("y", 0.0)), step=5.0)

    mode = st.selectbox("Nachweisstrategie", ["manual", "precheck", "hilti_doc"], index=["manual", "precheck", "hilti_doc"].index(anchorage_default.manufacturer_mode))
    note = st.text_area("Notiz / Annahmen", value=anchorage_default.note, height=120)

    anchorage = AnchorageInput(
        connection_label=connection_label,
        support_type=support_type,
        support_index=int(support_index),
        support_role=support_role,
        slide_direction=slide_direction,
        substrate_strength_class=substrate_strength_class,
        anchor_designation=anchor_designation,
        anchor_count=int(anchor_count),
        edge_distances_mm={key: value for key, value in {"left": float(edge_left), "right": float(edge_right), "top": float(edge_top), "bottom": float(edge_bottom)}.items() if value > 0.0},
        spacing_mm={key: value for key, value in {"x": float(spacing_x), "y": float(spacing_y)}.items() if value > 0.0},
        wdvs_mm=float(wdvs_mm) if wdvs_mm > 0.0 else None,
        spalt_mm=float(spalt_mm) if spalt_mm > 0.0 else None,
        bracket_offset_mm=float(bracket_offset_mm) if bracket_offset_mm > 0.0 else None,
        anchor_plane_offset_mm=float(anchor_plane_offset_mm) if anchor_plane_offset_mm > 0.0 else None,
        platform_eccentricity_mm=float(platform_eccentricity_mm) if platform_eccentricity_mm > 0.0 else None,
        plate_width_mm=float(plate_width) if plate_width > 0.0 else None,
        plate_height_mm=float(plate_height) if plate_height > 0.0 else None,
        plate_thickness_mm=float(plate_thickness) if plate_thickness > 0.0 else None,
        manufacturer_mode=mode,
        note=note,
    )
    support_action = derive_support_action(actions, support_index=anchorage.support_index, support_role=anchorage.support_role, slide_direction=anchorage.slide_direction, local_eccentricity_mm=anchorage.local_eccentricity_mm, platform_eccentricity_mm=float(anchorage.platform_eccentricity_mm or 0.0))
    assessment = assess_anchorage(actions, anchorage, support_action=support_action)
    feedback = build_verankerung_feedback(anchorage, assessment, support_action, action_error=action_error)
    consistency_report = analyze_verankerung_consistency(anchorage, support_action, actions)

    save_verankerung_state(
        input={
            "connection_label": connection_label,
            "support_type": support_type,
            "support_index": int(support_index),
            "support_role": support_role,
            "slide_direction": slide_direction,
            "substrate_strength_class": substrate_strength_class,
            "anchor_designation": anchor_designation,
            "anchor_count": int(anchor_count),
            "edge_left_mm": float(edge_left),
            "edge_right_mm": float(edge_right),
            "edge_top_mm": float(edge_top),
            "edge_bottom_mm": float(edge_bottom),
            "spacing_x_mm": float(spacing_x),
            "spacing_y_mm": float(spacing_y),
            "wdvs_mm": float(wdvs_mm),
            "spalt_mm": float(spalt_mm),
            "bracket_offset_mm": float(bracket_offset_mm),
            "anchor_plane_offset_mm": float(anchor_plane_offset_mm),
            "platform_eccentricity_mm": float(platform_eccentricity_mm),
            "plate_width_mm": float(plate_width),
            "plate_height_mm": float(plate_height),
            "plate_thickness_mm": float(plate_thickness),
            "manufacturer_mode": mode,
            "note": note,
        },
        results_snapshot={**assessment.to_dict(), "actions": actions.__dict__, "support_action": support_action.__dict__, "feedback": feedback, "consistency_report": consistency_report.to_dict()},
    )

with col_right:
    _show_feedback_block(feedback["level"], feedback["summary"])
    st.progress(feedback["completeness"], text=f"Eingabe- und Dokumentationsgrad: {feedback['completeness']*100:.0f}%")

    overview_tab, sketch_tab, checks_tab = st.tabs(["Übersicht", "Preview", "Bewertung"])

    with overview_tab:
        st.subheader("Übernommene Anschlussgrößen aus Wind")
        if action_error:
            st.warning(f"Wind-Snapshot noch unvollständig: {action_error}")
        else:
            st.success("Anschlussgrößen wurden aus dem Windmodul rekonstruiert.")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Hx,Ed [kN]", f"{actions.Hx_Ed:.2f}")
        m2.metric("Hy,1,Ed [kN]", f"{actions.Hy_1_Ed:.2f}")
        m3.metric("Hy,2,Ed [kN]", f"{actions.Hy_2_Ed:.2f}")
        m4.metric("M_A,k [kNm]", f"{actions.M_A_k:.2f}")

        st.subheader("Lokales Stützstellenmodell")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Fx,Ed lokal [kN]", f"{support_action.transferred_fx_Ed:.2f}")
        s2.metric("Fy,Ed lokal [kN]", f"{support_action.transferred_fy_Ed:.2f}")
        s3.metric("freigegeben [kN]", f"{support_action.released_component_Ed:.2f}")
        s4.metric("M_add,Ed [kNm]", f"{support_action.additional_moment_Ed:.2f}")

        st.caption(f"Stützstelle {support_action.support_index} als {support_action.support_role}; Gleitachse {support_action.slide_direction}; e_local = {support_action.local_eccentricity_mm:.1f} mm; e_platform = {support_action.platform_eccentricity_mm:.1f} mm.")
        st.caption(actions.note)
        st.markdown(render_assessment_badges(assessment), unsafe_allow_html=True)

        ccol1, ccol2 = st.columns(2)
        with ccol1:
            with st.expander("Was schon gut dokumentiert ist", expanded=True):
                for item in feedback["strengths"]:
                    st.write(f"- {item}")
        with ccol2:
            with st.expander("Was noch fehlt / prüfen", expanded=True):
                for item in feedback["missing"]:
                    st.write(f"- {item}")
                for item in feedback["hints"]:
                    st.write(f"- {item}")

        st.subheader("Modellkonsistenz")
        _show_feedback_block(consistency_report.level, consistency_report.summary)
        if consistency_report.issues:
            for issue in consistency_report.issues:
                _show_consistency_issue(issue.severity, issue.title, issue.detail)
        else:
            st.success("Keine offensichtlichen Inkonsistenzen erkannt.")

        if consistency_report.quick_fixes:
            with st.expander("Heuristische Quick Fixes", expanded=False):
                st.caption("Diese Vorschläge korrigieren offensichtliche UI-Inkonsistenzen. Sie ersetzen keinen normativen Nachweis.")
                for key, value in consistency_report.quick_fixes.items():
                    st.write(f"- {key}: {value}")
                if st.button("Quick Fixes jetzt übernehmen", type="secondary", use_container_width=True):
                    new_input = apply_consistency_quick_fixes(saved_input, consistency_report)
                    save_verankerung_state(input=new_input, results_snapshot=saved_state.get("results_snapshot", {}))
                    st.rerun()

        if actions.trace:
            with st.expander("Transfer-Trace Wind"):
                for item in actions.trace:
                    st.write(f"- {item}")
        if support_action.trace:
            with st.expander("Transfer-Trace Stützstelle", expanded=True):
                for item in support_action.trace:
                    st.write(f"- {item}")

    with sketch_tab:
        st.subheader("Preview der Anschluss-Skizzen")
        st.caption("Die Preview verwendet dieselben Eingangsdaten wie der Report. So sieht man vor dem PDF sofort, ob Lagerrolle, Gleitachse und Exzentrizitäten logisch modelliert sind.")
        plan_col, side_col = st.columns(2)
        with plan_col:
            st.markdown(render_plan_preview_svg(anchorage, support_action, actions), unsafe_allow_html=True)
        with side_col:
            st.markdown(render_side_preview_svg(anchorage, support_action), unsafe_allow_html=True)
        st.info("Wenn die Vorschau unplausibel aussieht — z. B. falsche aktive Stützstelle, unlogische Gleitachse, zu kleine Platte oder e_local = 0 — lohnt sich die Korrektur hier mehr als erst im PDF-Export.")

    with checks_tab:
        st.subheader("Bewertung")
        st.write("Gesamtstatus:", assessment.overall_status)
        for item in assessment.checks:
            if item.status == "ok":
                st.success(f"{item.title}: {item.detail}")
            elif item.status == "fail":
                st.error(f"{item.title}: {item.detail}")
            else:
                st.warning(f"{item.title}: {item.detail}")

        with st.expander("Basis der Vorprüfung", expanded=True):
            for item in assessment.basis_summary:
                st.write(f"- {item}")
        with st.expander("Dokumentierte Geometrie", expanded=True):
            for item in assessment.geometry_summary:
                st.write(f"- {item}")
        with st.expander("Nicht abgedeckter Restumfang"):
            for item in assessment.manual_scope:
                st.write(f"- {item}")
