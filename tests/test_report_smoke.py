from __future__ import annotations

import shutil

import pytest

from spittelmeister_windlast.report import (
    ReportSelection,
    build_combined_runtime_data,
    compile_latex_to_pdf_bytes,
    protokol_header_from_project_meta,
    render_combined_report,
)


def _sample_project_meta() -> dict[str, object]:
    return {
        "project_id": "2026-WB-900",
        "title": "Smoke Musterbericht",
        "client": "Bauherr GmbH",
        "street": "Musterstraße 1",
        "city": "Pforzheim",
        "revision": "3",
        "bearbeiter": "S. Labbe",
        "datum": "21.04.2026",
    }


def _sample_wind_state() -> dict[str, object]:
    return {
        "input": {
            "adresse": "Musterstraße 1, Pforzheim",
            "h_gebaeude": 18.0,
            "d_gebaeude": 10.0,
            "b_gebaeude": 20.0,
            "z_balkon": 12.0,
            "e_balkon": 2.5,
            "h_abschl": 1.1,
            "s_verank": 3.2,
            "b_auflager_rand": 0.3,
            "standort_bez": "Pforzheim",
            "hoehe_uNN": 260.0,
            "windzone": 2,
            "gelaende": "binnen",
        },
        "results_snapshot": {
            "qb0": 0.65,
            "qp": 0.95,
            "qp_faktor": 1.46,
            "qp_formel": r"q_p = 1.46 \cdot q_{b,0}",
            "qp_auswertung": r"q_p = 1.46 \cdot 0.65 = 0.95~\mathrm{kN/m^2}",
            "qp_abschnitt": "Außenbereich",
            "qp_verfahren": "DIN EN 1991-1-4/NA",
            "qp_normstelle": "NA.B.3",
            "gelaende_label": "Binnenland",
            "cscd": 1.0,
            "h_d": 1.8,
            "A_ref": 3.52,
            "A_w_side": 2.75,
            "A_w_front": 3.52,
            "cpe10_D": 0.8,
            "cpe10_E": -0.5,
            "cpe10_A": -1.2,
            "we_side_pressure": 0.76,
            "we_side_suction": -0.48,
            "we_front_suction": -1.14,
            "q_side_pressure": 0.84,
            "q_side_suction": -0.53,
            "q_front_suction": -1.25,
            "wk_sog": -1.25,
            "wk_druck": 0.84,
            "wk_massgebend": -1.25,
            "lastfall_massgebend": "Frontsog",
            "qhk": 1.25,
            "Hk": 4.0,
            "Mk": 2.2,
            "hoehenstufe": 0,
            "cscd_begruendung": "Für das Beispiel wird cscd = 1.0 angesetzt.",
            "methodik": "Beispieltest",
            "cp_net_sog": -1.2,
            "cp_net_druck": 0.8,
            "zone_massgebend": "A",
            "cpi_unguenstig_sog": 0.0,
            "cpi_unguenstig_druck": 0.0,
            "q_seite_1": 0.84,
            "q_seite_2": -0.53,
            "q_vorne": -1.25,
            "s": 2.6,
            "auflagerabstand": 2.6,
            "Hx_k": 0.78,
            "Hx_Ed": 1.17,
            "Hy_1_k": 1.10,
            "Hy_1_Ed": 1.65,
            "Hy_2_k": 2.90,
            "Hy_2_Ed": 4.35,
            "M_A_k": 7.54,
            "gamma_Q_reaktionen": 1.5,
            "reaktionsmodell_hinweis": "Vereinfachte statische Abschätzung in Draufsicht.",
        },
    }


def _sample_ver_state() -> dict[str, object]:
    return {
        "input": {
            "connection_label": "Anschluss 1",
            "support_type": "Stahlbetondecke",
            "support_index": 2,
            "support_role": "gleitlager",
            "slide_direction": "x",
            "substrate_strength_class": "C25/30",
            "anchor_designation": "M12",
            "anchor_count": 4,
            "edge_left_mm": 80.0,
            "edge_right_mm": 80.0,
            "edge_top_mm": 70.0,
            "edge_bottom_mm": 70.0,
            "spacing_x_mm": 90.0,
            "spacing_y_mm": 140.0,
            "wdvs_mm": 120.0,
            "spalt_mm": 20.0,
            "bracket_offset_mm": 40.0,
            "anchor_plane_offset_mm": 30.0,
            "platform_eccentricity_mm": 60.0,
            "plate_width_mm": 160.0,
            "plate_height_mm": 220.0,
            "plate_thickness_mm": 12.0,
            "manufacturer_mode": "precheck",
            "note": "Musterprüfung",
        },
        "results_snapshot": {
            "overall_status": "open",
            "checks": [
                {"title": "Ankeranzahl", "status": "ok", "detail": "4 Verankerungen gesetzt."},
                {"title": "Randabstände", "status": "open", "detail": "Normativ noch zu prüfen."},
            ],
            "manual_scope": ["Vollständiger Nachweis bleibt projektspezifisch offen."],
            "basis_summary": ["Transfermodell: vereinfachtes_balkonsystem"],
            "geometry_summary": ["Platte [mm]: 160 x 220 x 12"],
            "decisive_notes": ["Musterprüfung"],
        },
    }


def _sample_tex() -> str:
    meta = _sample_project_meta()
    runtime = build_combined_runtime_data(meta, _sample_wind_state(), _sample_ver_state())
    header = protokol_header_from_project_meta(meta)
    selection = ReportSelection()
    selection.windlast.include = True
    selection.verankerung.include = True
    return render_combined_report(header, selection, runtime)


def test_combined_report_smoke_contains_verankerung_sections() -> None:
    tex = _sample_tex()
    assert "Anschlussgeometrie und Grundlagen" in tex
    assert "Bewertungsmatrix" in tex
    assert "Nicht abgedeckter Restumfang" in tex
    assert "Ankergruppe" in tex
    assert "Lagerkinematik und Exzentrizität" in tex
    assert "Abgeleitete lokale Stützstellenlasten" in tex
    assert "Skizzen Festlager / Gleitlager und Exzentrizität" in tex
    assert "Skizze in Plandarstellung" in tex
    assert "Skizze in Seitenansicht" in tex
    assert "Höhe Geländer bzw. Abschattung" in tex
    assert "Balkon Breite" in tex
    assert "Verankerung Abstand zum Rand" in tex


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex nicht installiert")
def test_combined_report_smoke_compiles_to_pdf() -> None:
    pdf = compile_latex_to_pdf_bytes(_sample_tex())
    assert len(pdf) > 5000
