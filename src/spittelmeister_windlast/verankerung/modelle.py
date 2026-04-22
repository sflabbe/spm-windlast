from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Mapping


AssessmentStatus = Literal["ok", "open", "manual", "fail"]
ManufacturerMode = Literal["manual", "precheck", "hilti_doc"]
SupportRole = Literal["festlager", "gleitlager"]
SlideDirection = Literal["x", "y"]


@dataclass
class AnchorageInput:
    connection_label: str = "Anschluss 1"
    support_type: str = "Stahlbeton"
    support_index: int = 1
    support_role: SupportRole = "festlager"
    slide_direction: SlideDirection = "x"
    anchor_count: int = 2
    anchor_designation: str = "M12"
    plate_width_mm: float | None = None
    plate_height_mm: float | None = None
    plate_thickness_mm: float | None = None
    edge_distances_mm: dict[str, float] = field(default_factory=dict)
    spacing_mm: dict[str, float] = field(default_factory=dict)
    wdvs_mm: float | None = None
    spalt_mm: float | None = None
    bracket_offset_mm: float | None = None
    anchor_plane_offset_mm: float | None = None
    platform_eccentricity_mm: float | None = None
    substrate_strength_class: str = "unbekannt"
    manufacturer_mode: ManufacturerMode = "manual"
    note: str = ""

    @property
    def anchor_group_shape(self) -> str:
        if self.anchor_count <= 1:
            return "Einzelanker"
        if self.anchor_count == 2:
            return "Ankerpaar"
        if self.anchor_count == 4:
            return "2x2-Gruppe"
        return f"{self.anchor_count}-teilige Gruppe"

    @property
    def plate_area_mm2(self) -> float | None:
        if self.plate_width_mm and self.plate_height_mm:
            return float(self.plate_width_mm * self.plate_height_mm)
        return None

    @property
    def local_eccentricity_mm(self) -> float:
        return float(self.wdvs_mm or 0.0) + float(self.spalt_mm or 0.0) + float(self.bracket_offset_mm or 0.0) + float(self.anchor_plane_offset_mm or 0.0)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "AnchorageInput":
        def _as_float(value: Any) -> float | None:
            if value in (None, ""):
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        def _as_dict(keys: list[str], source: Mapping[str, Any], mapping_key: str, fallback_prefix: str = "") -> dict[str, float]:
            out: dict[str, float] = {}
            raw = source.get(mapping_key)
            if isinstance(raw, Mapping):
                for key, value in raw.items():
                    number = _as_float(value)
                    if number is not None and number > 0.0:
                        out[str(key)] = number
            for key in keys:
                number = _as_float(source.get(f"{fallback_prefix}{key}_mm"))
                if number is not None and number > 0.0:
                    out[key] = number
            return out

        edge_keys = ["left", "right", "top", "bottom"]
        spacing_keys = ["x", "y"]
        manufacturer_mode = str(data.get("manufacturer_mode", "manual"))
        if manufacturer_mode not in {"manual", "precheck", "hilti_doc"}:
            manufacturer_mode = "manual"
        support_role = str(data.get("support_role", "festlager"))
        if support_role not in {"festlager", "gleitlager"}:
            support_role = "festlager"
        slide_direction = str(data.get("slide_direction", "x"))
        if slide_direction not in {"x", "y"}:
            slide_direction = "x"
        anchor_count = data.get("anchor_count", 2)
        try:
            anchor_count = int(float(anchor_count))
        except (TypeError, ValueError):
            anchor_count = 2
        support_index = data.get("support_index", 1)
        try:
            support_index = int(float(support_index))
        except (TypeError, ValueError):
            support_index = 1
        return cls(
            connection_label=str(data.get("connection_label", "Anschluss 1")),
            support_type=str(data.get("support_type", "Stahlbeton")),
            support_index=support_index,
            support_role=support_role,  # type: ignore[arg-type]
            slide_direction=slide_direction,  # type: ignore[arg-type]
            anchor_count=anchor_count,
            anchor_designation=str(data.get("anchor_designation", "M12")),
            plate_width_mm=_as_float(data.get("plate_width_mm")),
            plate_height_mm=_as_float(data.get("plate_height_mm")),
            plate_thickness_mm=_as_float(data.get("plate_thickness_mm")),
            edge_distances_mm=_as_dict(edge_keys, data, "edge_distances_mm", "edge_"),
            spacing_mm=_as_dict(spacing_keys, data, "spacing_mm", "spacing_"),
            wdvs_mm=_as_float(data.get("wdvs_mm")),
            spalt_mm=_as_float(data.get("spalt_mm")),
            bracket_offset_mm=_as_float(data.get("bracket_offset_mm")),
            anchor_plane_offset_mm=_as_float(data.get("anchor_plane_offset_mm")),
            platform_eccentricity_mm=_as_float(data.get("platform_eccentricity_mm")),
            substrate_strength_class=str(data.get("substrate_strength_class", "unbekannt")),
            manufacturer_mode=manufacturer_mode,  # type: ignore[arg-type]
            note=str(data.get("note", "")),
        )


@dataclass
class CheckItem:
    title: str
    status: AssessmentStatus
    detail: str


@dataclass
class AnchorageAssessment:
    overall_status: AssessmentStatus
    checks: list[CheckItem] = field(default_factory=list)
    manual_scope: list[str] = field(default_factory=list)
    basis_summary: list[str] = field(default_factory=list)
    geometry_summary: list[str] = field(default_factory=list)
    decisive_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "checks": [asdict(item) for item in self.checks],
            "manual_scope": list(self.manual_scope),
            "basis_summary": list(self.basis_summary),
            "geometry_summary": list(self.geometry_summary),
            "decisive_notes": list(self.decisive_notes),
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "AnchorageAssessment":
        checks_payload = data.get("checks", [])
        checks: list[CheckItem] = []
        if isinstance(checks_payload, list):
            for item in checks_payload:
                if isinstance(item, Mapping):
                    checks.append(
                        CheckItem(
                            title=str(item.get("title", "Prüfpunkt")),
                            status=str(item.get("status", "open")),
                            detail=str(item.get("detail", "")),
                        )
                    )
        return cls(
            overall_status=str(data.get("overall_status", "open")),
            checks=checks,
            manual_scope=[str(item) for item in data.get("manual_scope", [])],
            basis_summary=[str(item) for item in data.get("basis_summary", [])],
            geometry_summary=[str(item) for item in data.get("geometry_summary", [])],
            decisive_notes=[str(item) for item in data.get("decisive_notes", [])],
        )
