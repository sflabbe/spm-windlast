from __future__ import annotations

from spittelmeister_windlast.transfer.modelle import ConnectionActions, SupportAction
from spittelmeister_windlast.ui.verankerung_optimizer import apply_macro_to_state_input, suggest_anchorage_macro
from spittelmeister_windlast.verankerung.modelle import AnchorageInput


def test_optimizer_suggests_geometry_for_four_anchor_group() -> None:
    anchorage = AnchorageInput(
        support_role="gleitlager",
        slide_direction="x",
        anchor_count=4,
        wdvs_mm=120.0,
        spalt_mm=20.0,
        bracket_offset_mm=40.0,
        anchor_plane_offset_mm=30.0,
        manufacturer_mode="manual",
    )
    actions = ConnectionActions(Hx_Ed=1.17, Hy_1_Ed=1.65, Hy_2_Ed=4.35)
    support = SupportAction(support_role="gleitlager", total_resultant_Ed=4.35)
    suggestion = suggest_anchorage_macro(anchorage, support, actions)
    assert suggestion.values["edge_left_mm"] >= 80
    assert suggestion.values["spacing_x_mm"] >= 90
    assert suggestion.values["spacing_y_mm"] >= 120
    assert suggestion.values["plate_width_mm"] >= 180
    assert suggestion.values["manufacturer_mode"] == "precheck"


def test_apply_macro_merges_and_appends_note() -> None:
    suggestion = suggest_anchorage_macro(
        AnchorageInput(anchor_count=2),
        SupportAction(total_resultant_Ed=3.2),
        ConnectionActions(),
    )
    merged = apply_macro_to_state_input({"note": "Bestand prüfen."}, suggestion)
    assert "Auto-Optimierungsmakro angewendet" in merged["note"]
    assert merged["edge_left_mm"] > 0
