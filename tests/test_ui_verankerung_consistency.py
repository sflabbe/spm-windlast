from __future__ import annotations

from spittelmeister_windlast.transfer.modelle import ConnectionActions, SupportAction
from spittelmeister_windlast.ui.verankerung_consistency import analyze_verankerung_consistency, apply_consistency_quick_fixes
from spittelmeister_windlast.verankerung.modelle import AnchorageInput


def _actions() -> ConnectionActions:
    return ConnectionActions(Hx_Ed=1.2, Hy_1_Ed=1.8, Hy_2_Ed=4.4, s=3.1)


def test_consistency_detects_plate_too_small_and_suggests_fix() -> None:
    anchorage = AnchorageInput(
        support_index=2,
        support_role="gleitlager",
        slide_direction="x",
        anchor_count=4,
        plate_width_mm=140.0,
        plate_height_mm=180.0,
        plate_thickness_mm=10.0,
        edge_distances_mm={"left": 80.0, "right": 80.0, "top": 70.0, "bottom": 70.0},
        spacing_mm={"x": 90.0, "y": 140.0},
        wdvs_mm=120.0,
        spalt_mm=20.0,
        bracket_offset_mm=40.0,
        anchor_plane_offset_mm=30.0,
        platform_eccentricity_mm=50.0,
    )
    support = SupportAction(
        support_index=2,
        support_role="gleitlager",
        slide_direction="x",
        base_fx_Ed=0.6,
        base_fy_Ed=4.4,
        transferred_fx_Ed=0.0,
        transferred_fy_Ed=4.4,
        released_component_Ed=0.6,
        local_eccentricity_mm=210.0,
        platform_eccentricity_mm=50.0,
        additional_moment_Ed=1.14,
        total_resultant_Ed=4.4,
    )
    report = analyze_verankerung_consistency(anchorage, support, _actions())
    titles = [item.title for item in report.issues]
    assert "Plattenbreite vs. Rand-/Achsabstände" in titles
    assert "Plattenhöhe vs. Rand-/Achsabstände" in titles
    assert report.quick_fixes["plate_width_mm"] >= 250
    assert report.quick_fixes["plate_height_mm"] >= 300


def test_consistency_can_suggest_alternate_slide_direction() -> None:
    anchorage = AnchorageInput(
        support_index=2,
        support_role="gleitlager",
        slide_direction="x",
        anchor_count=2,
        plate_width_mm=180.0,
        plate_height_mm=220.0,
        plate_thickness_mm=12.0,
        edge_distances_mm={"left": 80.0, "right": 80.0, "top": 70.0, "bottom": 70.0},
        spacing_mm={"y": 120.0},
        wdvs_mm=120.0,
        spalt_mm=20.0,
        bracket_offset_mm=20.0,
        anchor_plane_offset_mm=20.0,
    )
    support = SupportAction(
        support_index=2,
        support_role="gleitlager",
        slide_direction="x",
        base_fx_Ed=0.10,
        base_fy_Ed=3.50,
        transferred_fx_Ed=0.0,
        transferred_fy_Ed=3.50,
        released_component_Ed=0.10,
        local_eccentricity_mm=180.0,
        additional_moment_Ed=0.63,
        total_resultant_Ed=3.50,
    )
    report = analyze_verankerung_consistency(anchorage, support, _actions())
    assert any(item.title == "Gleitrichtung möglicherweise unpassend" for item in report.issues)
    patched = apply_consistency_quick_fixes({"note": "Alt"}, report)
    assert patched["slide_direction"] == "y"
    assert "Quick-Fixes" in patched["note"]
