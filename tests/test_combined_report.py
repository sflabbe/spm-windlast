from __future__ import annotations

from io import BytesIO
import zipfile

from spittelmeister_windlast.report import (
    ReportSelection,
    build_combined_runtime_data,
    create_report_zip_bundle,
    protokol_header_from_project_meta,
    render_combined_report,
)


def _sample_project_meta() -> dict[str, object]:
    return {
        "project_id": "2026-WB-777",
        "title": "Wind / Verankerung Muster",
        "client": "Bauherr GmbH",
        "street": "Musterstraße 1",
        "city": "Pforzheim",
        "revision": "2",
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
            "support_type": "Stahlbeton",
            "support_index": 2,
            "support_role": "gleitlager",
            "slide_direction": "x",
            "anchor_count": 2,
            "edge_left_mm": 80.0,
            "edge_right_mm": 80.0,
            "wdvs_mm": 120.0,
            "spalt_mm": 20.0,
            "platform_eccentricity_mm": 60.0,
            "plate_thickness_mm": 12.0,
            "manufacturer_mode": "precheck",
            "note": "Musterprüfung",
        },
        "results_snapshot": {
            "overall_status": "open",
            "checks": [
                {"title": "Ankeranzahl", "status": "ok", "detail": "2 Verankerungen gesetzt."},
                {"title": "Randabstände", "status": "open", "detail": "Normativ noch zu prüfen."},
            ],
            "manual_scope": ["Vollständiger Nachweis bleibt projektspezifisch offen."],
        },
    }


def test_combined_runtime_and_render_include_selected_modules() -> None:
    meta = _sample_project_meta()
    wind_state = _sample_wind_state()
    ver_state = _sample_ver_state()
    runtime = build_combined_runtime_data(meta, wind_state, ver_state)
    header = protokol_header_from_project_meta(meta)
    selection = ReportSelection()
    selection.windlast.include = True
    selection.verankerung.include = True

    tex = render_combined_report(header, selection, runtime)

    assert "Statische Berechnung" in tex
    assert "Wind / Verankerung Muster" in tex
    assert "Verankerung / Anschluss" in tex
    assert "Windlastermittlung" in tex
    assert "Lagerkinematik und Exzentrizität" in tex
    assert "Skizze in Plandarstellung" in tex
    assert "Skizze in Seitenansicht" in tex
    assert "Hx_{Ed}" in tex or "H_{x,Ed}" in tex


def test_report_zip_bundle_contains_main_and_assets() -> None:
    meta = _sample_project_meta()
    runtime = build_combined_runtime_data(meta, _sample_wind_state(), _sample_ver_state())
    header = protokol_header_from_project_meta(meta)
    selection = ReportSelection()
    selection.windlast.include = True
    selection.verankerung.include = True
    tex = render_combined_report(header, selection, runtime)

    bundle = create_report_zip_bundle(tex)

    with zipfile.ZipFile(BytesIO(bundle), "r") as zf:
        names = set(zf.namelist())

    assert "main.tex" in names
    assert "README.txt" in names
    assert "assets/building_geometry_zoning.tex" in names
    assert "assets/reaction_scheme.tex" in names
