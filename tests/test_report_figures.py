from __future__ import annotations

from spittelmeister_windlast.report.report_figures import (
    render_support_kinematics_figures,
    render_support_plan_sketch,
    render_support_side_sketch,
)
from spittelmeister_windlast.transfer.modelle import ConnectionActions, SupportAction
from spittelmeister_windlast.verankerung.modelle import AnchorageInput


def _anchorage() -> AnchorageInput:
    return AnchorageInput(
        connection_label="Anschluss 1",
        support_type="Stahlbetondecke",
        support_index=2,
        support_role="gleitlager",
        slide_direction="x",
        anchor_count=4,
        anchor_designation="M12",
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
    )


def _support_action() -> SupportAction:
    return SupportAction(
        support_index=2,
        support_role="gleitlager",
        slide_direction="x",
        transferred_fx_Ed=0.0,
        transferred_fy_Ed=4.35,
        released_component_Ed=0.59,
        local_eccentricity_mm=210.0,
        platform_eccentricity_mm=60.0,
        additional_moment_Ed=1.17,
        total_resultant_Ed=4.35,
    )


def _actions() -> ConnectionActions:
    return ConnectionActions(s=2.6)


def test_plan_sketch_contains_support_and_release_labels() -> None:
    tex = render_support_plan_sketch(_anchorage(), _support_action(), _actions())
    assert "Skizze in Plandarstellung" in tex
    assert "Gleitachse x" in tex
    assert "Resultierende Plattformlast" in tex
    assert "Stützstelle 2" in tex


def test_side_sketch_contains_local_and_platform_eccentricity() -> None:
    tex = render_support_side_sketch(_anchorage(), _support_action())
    assert "Skizze in Seitenansicht" in tex
    assert "e_{local}=210" in tex
    assert "e_{platform}=60" in tex
    assert "R_{h,Ed}=4.35" in tex


def test_combined_kinematics_figure_contains_note() -> None:
    tex = render_support_kinematics_figures(_anchorage(), _support_action(), _actions())
    assert "Skizzen Festlager / Gleitlager und Exzentrizität" in tex
    assert "Skizzenhinweis" in tex
