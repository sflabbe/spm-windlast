"""Spittelmeister Windlast — DIN EN 1991-1-4 / NA:2010-12.

Modulare Berechnung von Windlasten auf geschlossene Balkon-/Fassadenabschluesse.
"""

from __future__ import annotations

__version__ = "2.3.0"

from .api import BalconyWindResult, calculate_balcony_wind, calculate_wind
from .core import (
    Ergebnisse,
    Geometrie,
    PeakPressureResult,
    Projekt,
    Standort,
    WindlastBerechnung,
    berechne_qp,
    berechne_qp_ausfuehrlich,
    cpe10,
    get_hoehenstufe,
    interpolate_cpe_excel,
    interpolate_linear,
)
from .projectio import ModuleEntry, ProjectDocument, ProjectMetadata, dump_project_document, load_project_document
from .transfer import (
    ConnectionActions,
    SupportAction,
    derive_connection_actions_from_snapshot,
    derive_connection_actions_from_wind,
    derive_connection_actions_simple,
    derive_support_action,
)
from .verankerung import AnchorageAssessment, AnchorageInput, CheckItem, assess_anchorage

__all__ = [
    "__version__",
    "BalconyWindResult",
    "calculate_balcony_wind",
    "calculate_wind",
    "Projekt",
    "Standort",
    "Geometrie",
    "Ergebnisse",
    "WindlastBerechnung",
    "berechne_qp",
    "PeakPressureResult",
    "get_hoehenstufe",
    "cpe10",
    "interpolate_linear",
    "berechne_qp_ausfuehrlich",
    "interpolate_cpe_excel",
    "ConnectionActions",
    "SupportAction",
    "derive_connection_actions_from_snapshot",
    "derive_connection_actions_from_wind",
    "derive_connection_actions_simple",
    "derive_support_action",
    "AnchorageInput",
    "CheckItem",
    "AnchorageAssessment",
    "assess_anchorage",
    "ProjectMetadata",
    "ModuleEntry",
    "ProjectDocument",
    "dump_project_document",
    "load_project_document",
]
