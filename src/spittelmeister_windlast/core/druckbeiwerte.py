"""Aussendruckbeiwerte cpe,10 nach DIN EN 1991-1-4, Abschnitt 7.2.

Interpolation exakt nach Excel-Vorlage 27.02.2026 / Tafel 3.35.
Wichtig: Die Vorlage klemmt nicht ueberall ab, sondern extrapoliert in
einzelnen Bereichen. Genau dieses Verhalten wird hier nachgebildet.
"""

from __future__ import annotations

from typing import Literal

Bereich = Literal["A", "D", "E"]


def interpolate_linear(x: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """Lineare Interpolation / Extrapolation exakt wie in der Excel-Vorlage."""
    if abs(x2 - x1) < 1e-12:
        raise ValueError("Interpolation nicht moeglich: identische x-Stuetzstellen.")
    return ((y2 - y1) / (x2 - x1)) * (x - x1) + y1


def cpe10(bereich: Bereich, h_d: float) -> float:
    """Aussendruckbeiwert cpe,10 fuer Bereich A, D oder E in Abhaengigkeit von h/d.

    Args:
        bereich: "A" (Front Sog), "D" (Seite Druck) oder "E" (Seite Sog)
        h_d:     h/d-Verhaeltnis (dimensionslos)

    Returns:
        cpe,10 [-]. Vorzeichen wie in der Excel-Vorlage (D positiv, A/E negativ).
    """
    if bereich == "D":
        # IF(h_d > 1; 0.8; linear zwischen (0.25, 0.7) und (1.0, 0.8))
        return 0.8 if h_d > 1.0 else interpolate_linear(h_d, 0.25, 0.7, 1.0, 0.8)
    if bereich == "E":
        # IF(h_d > 1; -0.5; linear zwischen (0.25, -0.3) und (1.0, -0.5))
        return -0.5 if h_d > 1.0 else interpolate_linear(h_d, 0.25, -0.3, 1.0, -0.5)
    if bereich == "A":
        # IF(h_d > 5; -1.4; linear zwischen (1.0, -1.2) und (5.0, -1.4))
        return -1.4 if h_d > 5.0 else interpolate_linear(h_d, 1.0, -1.2, 5.0, -1.4)
    raise ValueError(f"Unbekannter Bereich: {bereich!r} (erlaubt: 'A', 'D', 'E')")


# Legacy-Alias
def interpolate_cpe_excel(zone: str, h_d: float) -> float:
    """Legacy-API (Zone statt Bereich)."""
    return cpe10(zone, h_d)  # type: ignore[arg-type]


__all__ = ["cpe10", "interpolate_linear", "interpolate_cpe_excel"]
