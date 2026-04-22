from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil
from typing import Any

from ..transfer.modelle import ConnectionActions, SupportAction
from ..verankerung.modelle import AnchorageInput


def _round_up(value: float, step: int = 5) -> int:
    return int(step * ceil(value / step))


@dataclass
class ConsistencyIssue:
    severity: str
    title: str
    detail: str
    suggested_updates: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsistencyReport:
    issues: list[ConsistencyIssue] = field(default_factory=list)

    @property
    def quick_fixes(self) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for item in self.issues:
            merged.update(item.suggested_updates)
        return merged

    @property
    def level(self) -> str:
        if any(item.severity == "error" for item in self.issues):
            return "error"
        if any(item.severity == "warning" for item in self.issues):
            return "warning"
        return "success"

    @property
    def summary(self) -> str:
        if not self.issues:
            return "Modellkonsistenz plausibel. Keine offensichtlichen Inkonsistenzen erkannt."
        errs = sum(item.severity == "error" for item in self.issues)
        warns = sum(item.severity == "warning" for item in self.issues)
        infos = sum(item.severity == "info" for item in self.issues)
        return f"Konsistenzcheck: {errs} Fehler, {warns} Warnungen, {infos} Hinweise."

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "summary": self.summary,
            "issues": [
                {
                    "severity": item.severity,
                    "title": item.title,
                    "detail": item.detail,
                    "suggested_updates": dict(item.suggested_updates),
                }
                for item in self.issues
            ],
            "quick_fixes": dict(self.quick_fixes),
        }


def analyze_verankerung_consistency(
    anchorage: AnchorageInput,
    support_action: SupportAction | None,
    actions: ConnectionActions | None = None,
) -> ConsistencyReport:
    issues: list[ConsistencyIssue] = []

    edge_left = float(anchorage.edge_distances_mm.get("left", 0.0))
    edge_right = float(anchorage.edge_distances_mm.get("right", 0.0))
    edge_top = float(anchorage.edge_distances_mm.get("top", 0.0))
    edge_bottom = float(anchorage.edge_distances_mm.get("bottom", 0.0))
    sx = float(anchorage.spacing_mm.get("x", 0.0))
    sy = float(anchorage.spacing_mm.get("y", 0.0))
    plate_w = float(anchorage.plate_width_mm or 0.0)
    plate_h = float(anchorage.plate_height_mm or 0.0)
    plate_t = float(anchorage.plate_thickness_mm or 0.0)

    required_w = edge_left + edge_right + (sx if anchorage.anchor_count >= 3 else 0.0) + 20.0
    required_h = edge_top + edge_bottom + (sy if anchorage.anchor_count >= 2 else 0.0) + 20.0
    if plate_w > 0.0 and required_w > 0.0 and plate_w < required_w:
        target = _round_up(required_w, 5)
        issues.append(
            ConsistencyIssue(
                severity="error",
                title="Plattenbreite vs. Rand-/Achsabstände",
                detail=(
                    f"Plattenbreite {plate_w:.0f} mm ist kleiner als die aus Randabständen/spacing abgeleitete Mindestbreite von ca. {required_w:.0f} mm."
                ),
                suggested_updates={"plate_width_mm": target},
            )
        )
    if plate_h > 0.0 and required_h > 0.0 and plate_h < required_h:
        target = _round_up(required_h, 5)
        issues.append(
            ConsistencyIssue(
                severity="error",
                title="Plattenhöhe vs. Rand-/Achsabstände",
                detail=(
                    f"Plattenhöhe {plate_h:.0f} mm ist kleiner als die aus Randabständen/spacing abgeleitete Mindesthöhe von ca. {required_h:.0f} mm."
                ),
                suggested_updates={"plate_height_mm": target},
            )
        )

    spacing_updates: dict[str, Any] = {}
    if anchorage.anchor_count >= 3:
        if sx <= 0.0:
            spacing_updates["spacing_x_mm"] = 90.0
        if sy <= 0.0:
            spacing_updates["spacing_y_mm"] = 120.0
        if spacing_updates:
            issues.append(
                ConsistencyIssue(
                    severity="warning",
                    title="Achsabstände unvollständig",
                    detail="Für eine Mehrfachverankerung fehlen x- und/oder y-Achsabstände. Die Gruppenwirkung bleibt damit unklar.",
                    suggested_updates=spacing_updates,
                )
            )
    elif anchorage.anchor_count == 2 and sy <= 0.0:
        issues.append(
            ConsistencyIssue(
                severity="warning",
                title="Achsabstand y fehlt",
                detail="Für ein Ankerpaar fehlt der vertikale Achsabstand. Die Geometrie ist so nur teilweise dokumentiert.",
                suggested_updates={"spacing_y_mm": 110.0},
            )
        )

    if anchorage.support_role == "gleitlager" and support_action is not None:
        current_release = abs(float(support_action.released_component_Ed or 0.0))
        alt_release = abs(support_action.base_fy_Ed) if support_action.slide_direction == "x" else abs(support_action.base_fx_Ed)
        if alt_release > max(0.25, current_release * 1.8):
            alt = "y" if support_action.slide_direction == "x" else "x"
            issues.append(
                ConsistencyIssue(
                    severity="warning",
                    title="Gleitrichtung möglicherweise unpassend",
                    detail=(
                        f"Die aktuell freigegebene Richtung '{support_action.slide_direction}' löst nur {current_release:.2f} kN, während '{alt}' etwa {alt_release:.2f} kN freigeben würde. Prüfen, ob die Schlitzrichtung konstruktiv korrekt angesetzt ist."
                    ),
                    suggested_updates={"slide_direction": alt},
                )
            )
        elif current_release < 0.10 and alt_release < 0.10:
            issues.append(
                ConsistencyIssue(
                    severity="info",
                    title="Gleitrichtung hat derzeit wenig Einfluss",
                    detail="Die freigegebene Komponente ist im aktuellen Lastzustand sehr klein. Die Lagerrolle ist dokumentarisch trotzdem sinnvoll, beeinflusst die Lasten aber kaum.",
                )
            )

    if anchorage.local_eccentricity_mm < 60.0:
        issues.append(
            ConsistencyIssue(
                severity="warning",
                title="Lokale Exzentrizität sehr klein",
                detail=(
                    f"e_local = {anchorage.local_eccentricity_mm:.0f} mm ist für einen Anschluss mit WDVS/Spalt/Konsole eher klein. Prüfen, ob WDVS, Spalt, Laschenhebel und Abstand zur Ankerachse vollständig erfasst sind."
                ),
            )
        )

    moment_ref = abs(float(support_action.additional_moment_Ed or 0.0)) if support_action is not None else 0.0
    resultant_ref = abs(float(support_action.total_resultant_Ed or 0.0)) if support_action is not None else 0.0
    if plate_t > 0.0 and (moment_ref > 0.8 or resultant_ref > 4.0) and plate_t < 12.0:
        issues.append(
            ConsistencyIssue(
                severity="warning",
                title="Plattendicke eher knapp",
                detail=(
                    f"Bei R_h,Ed ≈ {resultant_ref:.2f} kN und M_add,Ed ≈ {moment_ref:.2f} kNm wirkt eine Plattendicke von {plate_t:.0f} mm eher knapp. Für die Vorprüfung kann eine robustere Startgeometrie sinnvoll sein."
                ),
                suggested_updates={"plate_thickness_mm": 12.0},
            )
        )

    if anchorage.support_index == 2 and float(anchorage.platform_eccentricity_mm or 0.0) == 0.0:
        issues.append(
            ConsistencyIssue(
                severity="info",
                title="e_platform = 0 an Stützstelle 2",
                detail="Wenn die Plattformresultierende nicht mittig liegt, kann an der zweiten Stützstelle eine zusätzliche Plattform-Exzentrizität sinnvoll sein.",
            )
        )

    if actions is not None and abs(actions.Hx_Ed) + abs(actions.Hy_1_Ed) + abs(actions.Hy_2_Ed) <= 0.0:
        issues.append(
            ConsistencyIssue(
                severity="error",
                title="Keine verwertbaren Windlasten",
                detail="Die Anschluss- und Stützstellenlogik ist ohne rekonstruierten Wind-Snapshot derzeit nicht belastbar.",
            )
        )

    return ConsistencyReport(issues=issues)


def apply_consistency_quick_fixes(saved_input: dict[str, Any], report: ConsistencyReport) -> dict[str, Any]:
    merged = dict(saved_input)
    merged.update(report.quick_fixes)
    if report.quick_fixes:
        note_line = "Konsistenz-Quick-Fixes angewendet: heuristische UI-Korrekturen, kein normativer Nachweis."
        existing_note = str(merged.get("note", "")).strip()
        if note_line not in existing_note:
            merged["note"] = (existing_note + "\n" + note_line).strip()
    return merged
