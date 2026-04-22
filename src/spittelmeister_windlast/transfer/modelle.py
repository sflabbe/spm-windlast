from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot
from typing import Any, Literal, Mapping


SupportRole = Literal["festlager", "gleitlager"]
SlideDirection = Literal["x", "y"]


@dataclass
class ConnectionActions:
    """Abgeleitete Anschlussgrößen aus dem Windmodul."""

    source: str = "wind"
    model_name: str = "vereinfachtes_balkonsystem"
    q_seite_1: float = 0.0
    q_seite_2: float = 0.0
    q_vorne: float = 0.0
    s: float = 0.0
    auflagerabstand: float = 0.0
    Hx_k: float = 0.0
    Hx_Ed: float = 0.0
    Hy_1_k: float = 0.0
    Hy_1_Ed: float = 0.0
    Hy_2_k: float = 0.0
    Hy_2_Ed: float = 0.0
    M_A_k: float = 0.0
    gamma_Q: float = 1.5
    note: str = (
        "Vereinfachte statische Abschätzung in Draufsicht. Die Größen dienen der "
        "Vorbemessung und ersetzen kein vollständiges Tragwerksmodell."
    )
    trace: list[str] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ConnectionActions":
        """Robuste Rekonstruktion aus dict-/Snapshot-Daten."""

        def _as_float(key: str, default: float = 0.0) -> float:
            raw = data.get(key, default)
            if raw in (None, ""):
                return float(default)
            return float(raw)

        raw_trace = data.get("trace", [])
        trace = [str(item) for item in raw_trace] if isinstance(raw_trace, list) else []
        return cls(
            source=str(data.get("source", "wind")),
            model_name=str(data.get("model_name", "vereinfachtes_balkonsystem")),
            q_seite_1=_as_float("q_seite_1"),
            q_seite_2=_as_float("q_seite_2"),
            q_vorne=_as_float("q_vorne"),
            s=_as_float("s"),
            auflagerabstand=_as_float("auflagerabstand", _as_float("s")),
            Hx_k=_as_float("Hx_k"),
            Hx_Ed=_as_float("Hx_Ed"),
            Hy_1_k=_as_float("Hy_1_k"),
            Hy_1_Ed=_as_float("Hy_1_Ed"),
            Hy_2_k=_as_float("Hy_2_k"),
            Hy_2_Ed=_as_float("Hy_2_Ed"),
            M_A_k=_as_float("M_A_k"),
            gamma_Q=_as_float("gamma_Q", _as_float("gamma_Q_reaktionen", 1.5)),
            note=str(
                data.get(
                    "note",
                    data.get(
                        "reaktionsmodell_hinweis",
                        "Vereinfachte statische Abschätzung in Draufsicht. Die Größen dienen der Vorbemessung und ersetzen kein vollständiges Tragwerksmodell.",
                    ),
                )
            ),
            trace=trace,
        )


@dataclass
class SupportAction:
    """Lokale Lager- bzw. Anschlussgrößen für Festlager/Gleitlager."""

    support_index: int = 1
    support_role: SupportRole = "festlager"
    slide_direction: SlideDirection = "x"
    source_model: str = "support_distribution_v1"
    base_fx_Ed: float = 0.0
    base_fy_Ed: float = 0.0
    transferred_fx_Ed: float = 0.0
    transferred_fy_Ed: float = 0.0
    released_component_Ed: float = 0.0
    local_eccentricity_mm: float = 0.0
    platform_eccentricity_mm: float = 0.0
    additional_moment_Ed: float = 0.0
    total_resultant_Ed: float = 0.0
    note: str = ""
    trace: list[str] = field(default_factory=list)

    @property
    def released_axis_label(self) -> str:
        return "x" if self.slide_direction == "x" else "y"

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SupportAction":
        def _as_float(key: str, default: float = 0.0) -> float:
            raw = data.get(key, default)
            if raw in (None, ""):
                return float(default)
            try:
                return float(raw)
            except (TypeError, ValueError):
                return float(default)

        def _as_int(key: str, default: int = 1) -> int:
            raw = data.get(key, default)
            try:
                return int(float(raw))
            except (TypeError, ValueError):
                return int(default)

        raw_trace = data.get("trace", [])
        trace = [str(item) for item in raw_trace] if isinstance(raw_trace, list) else []
        role = str(data.get("support_role", "festlager"))
        if role not in {"festlager", "gleitlager"}:
            role = "festlager"
        slide = str(data.get("slide_direction", "x"))
        if slide not in {"x", "y"}:
            slide = "x"
        obj = cls(
            support_index=_as_int("support_index", 1),
            support_role=role,  # type: ignore[arg-type]
            slide_direction=slide,  # type: ignore[arg-type]
            source_model=str(data.get("source_model", "support_distribution_v1")),
            base_fx_Ed=_as_float("base_fx_Ed"),
            base_fy_Ed=_as_float("base_fy_Ed"),
            transferred_fx_Ed=_as_float("transferred_fx_Ed"),
            transferred_fy_Ed=_as_float("transferred_fy_Ed"),
            released_component_Ed=_as_float("released_component_Ed"),
            local_eccentricity_mm=_as_float("local_eccentricity_mm"),
            platform_eccentricity_mm=_as_float("platform_eccentricity_mm"),
            additional_moment_Ed=_as_float("additional_moment_Ed"),
            total_resultant_Ed=_as_float("total_resultant_Ed"),
            note=str(data.get("note", "")),
            trace=trace,
        )
        if obj.total_resultant_Ed == 0.0:
            obj.total_resultant_Ed = hypot(obj.transferred_fx_Ed, obj.transferred_fy_Ed)
        return obj
