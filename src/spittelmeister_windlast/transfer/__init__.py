"""Transfer layer zwischen Windlast-Ergebnis und Anschluss-/Verankerungsmodul."""

from .mapping import derive_connection_actions_from_snapshot, derive_connection_actions_from_wind
from .modelle import ConnectionActions, SupportAction
from .platform_supports import derive_support_action
from .vereinfachtes_balkonsystem import derive_connection_actions_simple

__all__ = [
    "ConnectionActions",
    "SupportAction",
    "derive_connection_actions_from_snapshot",
    "derive_connection_actions_from_wind",
    "derive_connection_actions_simple",
    "derive_support_action",
]
