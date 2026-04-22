from __future__ import annotations

from spittelmeister_windlast.transfer import derive_support_action
from spittelmeister_windlast.transfer.modelle import ConnectionActions
from spittelmeister_windlast.verankerung import AnchorageInput, assess_anchorage


def _actions() -> ConnectionActions:
    return ConnectionActions(
        Hx_k=0.78,
        Hx_Ed=1.17,
        Hy_1_k=1.10,
        Hy_1_Ed=1.65,
        Hy_2_k=2.90,
        Hy_2_Ed=4.35,
        M_A_k=7.54,
        s=2.6,
        note="Vereinfachte statische Abschätzung in Draufsicht.",
    )


def test_assessment_collects_geometry_and_basis_summaries() -> None:
    anchorage = AnchorageInput(
        connection_label="A1",
        support_type="Stahlbetondecke",
        support_index=2,
        support_role="gleitlager",
        slide_direction="x",
        substrate_strength_class="C25/30",
        anchor_designation="M12",
        anchor_count=4,
        plate_width_mm=160.0,
        plate_height_mm=220.0,
        plate_thickness_mm=12.0,
        edge_distances_mm={"left": 80.0, "right": 80.0, "top": 70.0, "bottom": 70.0},
        spacing_mm={"x": 90.0, "y": 140.0},
        wdvs_mm=120.0,
        spalt_mm=20.0,
        bracket_offset_mm=40.0,
        anchor_plane_offset_mm=30.0,
        platform_eccentricity_mm=60.0,
        manufacturer_mode="precheck",
        note="Musteranschluss.",
    )
    support_action = derive_support_action(
        _actions(),
        support_index=anchorage.support_index,
        support_role=anchorage.support_role,
        slide_direction=anchorage.slide_direction,
        local_eccentricity_mm=anchorage.local_eccentricity_mm,
        platform_eccentricity_mm=float(anchorage.platform_eccentricity_mm or 0.0),
    )

    result = assess_anchorage(_actions(), anchorage, support_action=support_action)

    assert result.overall_status == "open"
    assert any("Zusatzmoment aus Exzentrizität" in item for item in result.basis_summary)
    assert any("Lagerkinematik" in item for item in result.geometry_summary)
    assert any(item.title == "Gleitrichtung / freigegebene Komponente" and item.status == "open" for item in result.checks)
    assert "Musteranschluss." in result.decisive_notes


def test_assessment_is_manual_for_incomplete_geometry() -> None:
    anchorage = AnchorageInput(anchor_count=2, edge_distances_mm={"left": 80.0}, manufacturer_mode="manual")

    result = assess_anchorage(_actions(), anchorage)

    assert result.overall_status == "manual"
    assert any(item.title == "Randabstände" and item.status == "manual" for item in result.checks)
    assert any(item.title == "Achsabstände" and item.status == "manual" for item in result.checks)
