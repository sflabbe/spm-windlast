from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any

from ..transfer.modelle import ConnectionActions, SupportAction
from ..verankerung.modelle import AnchorageInput


def _round_up(value: float, step: int) -> int:
    return int(step * ceil(value / step))


@dataclass
class MacroSuggestion:
    values: dict[str, Any]
    summary_lines: list[str]
    note_line: str


def suggest_anchorage_macro(
    anchorage: AnchorageInput,
    support_action: SupportAction | None,
    actions: ConnectionActions | None,
) -> MacroSuggestion:
    resultant = float(support_action.total_resultant_Ed if support_action is not None else 0.0)
    if resultant <= 0.0 and actions is not None:
        resultant = max(abs(actions.Hx_Ed), abs(actions.Hy_1_Ed), abs(actions.Hy_2_Ed), 1.0)
    resultant = max(resultant, 1.0)

    edge = max(70, _round_up(55 + 4.5 * resultant, 5))
    if anchorage.support_role == "gleitlager":
        edge = max(edge, 80)

    spacing_x = 0
    spacing_y = 0
    if anchorage.anchor_count >= 3:
        spacing_x = _round_up(max(90.0, 45.0 + 12.0 * resultant), 5)
        spacing_y = _round_up(max(120.0, 70.0 + 16.0 * resultant), 5)
    elif anchorage.anchor_count == 2:
        spacing_y = _round_up(max(110.0, 65.0 + 14.0 * resultant), 5)

    wdvs = int(round(float(anchorage.wdvs_mm or 120.0)))
    spalt = int(round(float(anchorage.spalt_mm or 20.0)))
    bracket = int(round(float(anchorage.bracket_offset_mm or 40.0)))
    anchor_plane = int(round(float(anchorage.anchor_plane_offset_mm or 30.0)))
    local_e = wdvs + spalt + bracket + anchor_plane
    thickness = _round_up(max(10.0, 8.0 + 0.6 * resultant + 0.008 * local_e), 2)

    n_cols = 2 if anchorage.anchor_count >= 3 else 1
    n_rows = 2 if anchorage.anchor_count not in {1, 2} else anchorage.anchor_count
    width = 2 * edge + (spacing_x if n_cols == 2 else 0) + 20
    height = 2 * edge + (spacing_y if n_rows >= 2 else 0) + 20
    width = _round_up(max(width, 140), 5)
    height = _round_up(max(height, 180), 5)

    role = anchorage.support_role
    slide = anchorage.slide_direction
    mode = anchorage.manufacturer_mode if anchorage.manufacturer_mode != "manual" else "precheck"

    lines = [
        f"Empfohlene Randabstände: links/rechts/oben/unten je {edge} mm.",
        f"Empfohlene Platte: {width} x {height} x {thickness} mm.",
    ]
    if spacing_x > 0:
        lines.append(f"Empfohlener Achsabstand x: {spacing_x} mm.")
    if spacing_y > 0:
        lines.append(f"Empfohlener Achsabstand y: {spacing_y} mm.")
    lines.append(
        f"Heuristische Grundlage: R_h,Ed ≈ {resultant:.2f} kN, e_local ≈ {local_e} mm, Lagerrolle {role}."
    )

    note_line = (
        "Auto-Optimierungsmakro angewendet: heuristische Startgeometrie für Vorprüfung. "
        "Kein normativer Nachweis und keine Herstellerbemessung."
    )
    values = {
        "support_role": role,
        "slide_direction": slide,
        "manufacturer_mode": mode,
        "edge_left_mm": edge,
        "edge_right_mm": edge,
        "edge_top_mm": edge,
        "edge_bottom_mm": edge,
        "spacing_x_mm": spacing_x,
        "spacing_y_mm": spacing_y,
        "plate_width_mm": width,
        "plate_height_mm": height,
        "plate_thickness_mm": thickness,
        "wdvs_mm": wdvs,
        "spalt_mm": spalt,
        "bracket_offset_mm": bracket,
        "anchor_plane_offset_mm": anchor_plane,
    }
    return MacroSuggestion(values=values, summary_lines=lines, note_line=note_line)


def apply_macro_to_state_input(saved_input: dict[str, Any], suggestion: MacroSuggestion) -> dict[str, Any]:
    merged = dict(saved_input)
    merged.update(suggestion.values)
    existing_note = str(merged.get("note", "")).strip()
    if suggestion.note_line not in existing_note:
        merged["note"] = (existing_note + "\n" + suggestion.note_line).strip()
    return merged
