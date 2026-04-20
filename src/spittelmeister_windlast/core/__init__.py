"""Berechnungskern — reine EC1-Logik ohne I/O und ohne UI.

Abhaengigkeiten: nur Python-Standardbibliothek + ``daten``-Paket.
Keine ``requests``, keine ``streamlit``, kein ``pdflatex``.
"""

from .berechnung import WindlastBerechnung
from .druckbeiwerte import cpe10, interpolate_cpe_excel, interpolate_linear
from .modelle import Ergebnisse, Geometrie, Projekt, Standort
from .peak_pressure import (
    PeakPressureResult,
    berechne_qp,
    berechne_qp_ausfuehrlich,
    get_hoehenstufe,
)

__all__ = [
    # Dataclasses
    "Projekt",
    "Standort",
    "Geometrie",
    "Ergebnisse",
    # Rechenkern
    "WindlastBerechnung",
    # Einzelfunktionen / Bausteine
    "berechne_qp",
    "PeakPressureResult",
    "get_hoehenstufe",
    "cpe10",
    "interpolate_linear",
    # Legacy-Aliase
    "berechne_qp_ausfuehrlich",
    "interpolate_cpe_excel",
]
