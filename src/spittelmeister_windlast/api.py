"""Stable public API for automation integrations.

This module intentionally stays independent from Streamlit, the CLI and the
reporting layer.  It exposes the small wind-load contract currently consumed by
``balkon-automation``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class BalconyWindResult:
    """Result contract for balcony automation wind loads."""

    qw: float
    wch_S: float
    wch_F: float
    AW_yz: float
    AW_xz: float
    Hx_d_ges: float
    Hy_d_ges: float
    gamma_w: float

    def asdict(self) -> dict[str, float]:
        """Return the result as a plain dictionary."""
        return asdict(self)


def calculate_balcony_wind(
    *,
    geometry: Mapping[str, Any] | Any | None = None,
    qw: float,
    cpe_parallel: float,
    cpe_normal: float,
    gamma_w: float = 1.5,
    B1: float | None = None,
    T: float | None = None,
    HW_Seite: float | None = None,
    HW_Front: float | None = None,
) -> BalconyWindResult:
    """Calculate the minimal balcony wind payload for automation.

    Args:
        geometry: Optional mapping/object with ``B1``, ``T``, ``HW_Seite`` and
            ``HW_Front`` fields, matching ``balkon-automation``'s
            ``BalconyGeometry`` contract.
        qw: Characteristic wind pressure.
        cpe_parallel: Pressure coefficient for the side/parallel face.
        cpe_normal: Pressure coefficient for the front/normal face.
        gamma_w: Wind partial safety factor.
        B1: Optional direct front width override.
        T: Optional direct balcony depth override.
        HW_Seite: Optional direct side wind height override.
        HW_Front: Optional direct front wind height override.

    Returns:
        ``BalconyWindResult`` with the stable fields consumed by
        ``balkon-automation``.
    """
    t = _coalesce_float(T, geometry, "T", "t", "balkontiefe_T", "e_balkon")
    b1 = _coalesce_float(B1, geometry, "B1", "b1", "B", "balkonbreite_B", "s_verankerung")
    hw_seite = _coalesce_float(
        HW_Seite,
        geometry,
        "HW_Seite",
        "hw_seite",
        "HW_yz",
        "hw_yz",
        "h_abschluss",
    )
    hw_front = _coalesce_float(
        HW_Front,
        geometry,
        "HW_Front",
        "hw_front",
        "HW_xz",
        "hw_xz",
        "h_abschluss",
    )

    qw_value = float(qw)
    gamma_value = float(gamma_w)
    wch_S = qw_value * float(cpe_parallel)
    wch_F = qw_value * float(cpe_normal)
    AW_yz = t * hw_seite
    AW_xz = b1 * hw_front

    return BalconyWindResult(
        qw=qw_value,
        wch_S=wch_S,
        wch_F=wch_F,
        AW_yz=AW_yz,
        AW_xz=AW_xz,
        Hx_d_ges=gamma_value * wch_S * AW_yz,
        Hy_d_ges=gamma_value * wch_F * AW_xz,
        gamma_w=gamma_value,
    )


def calculate_wind(**kwargs: Any) -> BalconyWindResult:
    """Legacy alias for older adapters; prefer ``calculate_balcony_wind``."""
    return calculate_balcony_wind(**kwargs)


def _coalesce_float(
    explicit: float | None,
    geometry: Mapping[str, Any] | Any | None,
    *aliases: str,
) -> float:
    if explicit is not None:
        return float(explicit)
    if geometry is None:
        raise ValueError(f"Missing geometry value for {aliases[0]}")
    value = _read_geometry_value(geometry, *aliases)
    return float(value)


def _read_geometry_value(geometry: Mapping[str, Any] | Any, *aliases: str) -> Any:
    if isinstance(geometry, Mapping):
        for alias in aliases:
            if alias in geometry:
                return geometry[alias]
    else:
        for alias in aliases:
            if hasattr(geometry, alias):
                return getattr(geometry, alias)
    raise KeyError(aliases[0])


__all__ = ["BalconyWindResult", "calculate_balcony_wind", "calculate_wind"]
