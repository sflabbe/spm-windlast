"""Spittelmeister Windlast — DIN EN 1991-1-4 / NA:2010-12.

Modulare Berechnung von Windlasten auf geschlossene Balkon-/Fassadenabschluesse.

Architektur
-----------

Drei Schichten, unabhaengig voneinander verwendbar:

1. ``core``   — Reiner Rechenkern (keine I/O, keine Netzwerk-Abhaengigkeit).
                Nur Python-stdlib + ``daten``-Paket.

2. ``geo``    — Standortermittlung (Nominatim, open-elevation, Windzone-Lookup).
                Benoetigt ``requests``.

3. ``report`` — PDF-Export via LaTeX.
                Benoetigt ``pdflatex`` im System-PATH.

Quick Start
-----------

>>> from spittelmeister_windlast import (
...     WindlastBerechnung, Projekt, Standort, Geometrie
... )
>>> wb = WindlastBerechnung(
...     Projekt("Hochpunkt M Mannheim", "2025-WB-042", "S. Montero"),
...     Standort("Wuerzburg", windzone=1, gelaende="binnen", hoehe_uNN=192.0),
...     Geometrie(h=15.13, d=12.55, b=20.0, z_balkon=12.83,
...               e_balkon=1.425, h_abschluss=3.00, s_verankerung=4.93),
... )
>>> ergebnisse = wb.berechnen()

Integration in andere Projekte (z. B. ``balkonsystem``)
-------------------------------------------------------

>>> # Nur der Rechenkern (ohne Streamlit, ohne requests):
>>> from spittelmeister_windlast.core import WindlastBerechnung
>>>
>>> # Vollstaendige Pipeline inkl. Standortermittlung:
>>> from spittelmeister_windlast.geo import standort_ermitteln
>>>
>>> # Optional PDF-Report:
>>> from spittelmeister_windlast.report import export_pdf, render_latex
"""

from __future__ import annotations

__version__ = "2.0.0"

# ── Rechenkern (immer verfuegbar) ──────────────────────────────────────────
from .core import (
    Ergebnisse,
    Geometrie,
    PeakPressureResult,
    Projekt,
    Standort,
    WindlastBerechnung,
    berechne_qp,
    berechne_qp_ausfuehrlich,  # legacy
    cpe10,
    get_hoehenstufe,
    interpolate_cpe_excel,     # legacy
    interpolate_linear,
)

__all__ = [
    # Version
    "__version__",
    # Dataclasses
    "Projekt",
    "Standort",
    "Geometrie",
    "Ergebnisse",
    # Rechenkern
    "WindlastBerechnung",
    "berechne_qp",
    "PeakPressureResult",
    "get_hoehenstufe",
    "cpe10",
    "interpolate_linear",
    # Legacy-Aliase (Drop-in fuer alten flachen Code)
    "berechne_qp_ausfuehrlich",
    "interpolate_cpe_excel",
]
