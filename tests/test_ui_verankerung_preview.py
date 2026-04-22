from __future__ import annotations

from spittelmeister_windlast.transfer.modelle import ConnectionActions, SupportAction
from spittelmeister_windlast.ui.verankerung_preview import (
    build_verankerung_feedback,
    render_assessment_badges,
    render_plan_preview_svg,
    render_side_preview_svg,
)
from spittelmeister_windlast.verankerung import AnchorageInput, assess_anchorage


def _anchorage() -> AnchorageInput:
    return AnchorageInput(
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
        platform_eccentricity_mm=50.0,
        manufacturer_mode="precheck",
    )


def _actions() -> ConnectionActions:
    return ConnectionActions(s=3.1, Hx_Ed=1.17, Hy_1_Ed=1.65, Hy_2_Ed=4.35, M_A_k=7.54)


def _support() -> SupportAction:
    return SupportAction(
        support_index=2,
        support_role="gleitlager",
        slide_direction="x",
        transferred_fx_Ed=0.0,
        transferred_fy_Ed=4.35,
        released_component_Ed=0.585,
        local_eccentricity_mm=210.0,
        platform_eccentricity_mm=50.0,
        additional_moment_Ed=1.13,
        total_resultant_Ed=4.35,
    )


def test_preview_svgs_contain_key_labels() -> None:
    anchorage = _anchorage()
    actions = _actions()
    support = _support()
    plan = render_plan_preview_svg(anchorage, support, actions)
    side = render_side_preview_svg(anchorage, support)
    assert "Plandarstellung" in plan
    assert "Gleitachse x" in plan
    assert "e_platform=50" in plan
    assert "Seitenansicht" in side
    assert "e_local=210" in side
    assert "M_add,Ed=1.13" in side


def test_feedback_has_missing_and_strengths() -> None:
    anchorage = _anchorage()
    actions = _actions()
    support = _support()
    assessment = assess_anchorage(actions, anchorage, support_action=support)
    feedback = build_verankerung_feedback(anchorage, assessment, support)
    assert feedback["completeness"] > 0.7
    assert feedback["strengths"]
    assert feedback["hints"]
    assert feedback["level"] in {"success", "warning", "error"}
    badges = render_assessment_badges(assessment)
    assert "Ankeranzahl" in badges
    assert "Lastübergabe aus Windmodul" in badges
