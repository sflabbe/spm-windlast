"""Heuristische Bestimmung der Gelaendekategorie (Kueste vs. Binnenland).

Diese Heuristik ist bewusst konservativ: sie soll NICHT die Endentscheidung
treffen, sondern eine sinnvolle Voreinstellung liefern, die der Bearbeiter
manuell bestaetigt oder korrigiert.
"""

from __future__ import annotations

from ._normalize import norm_kreis
from .windzone import WindzoneValue

_KUESTE_STATES = {
    "Schleswig-Holstein",
    "Hamburg",
    "Bremen",
    "Mecklenburg-Vorpommern",
}

_KUESTE_KREISE = {
    "nordfriesland", "dithmarschen", "pinneberg", "steinburg",
    "rendsburg eckernfoerde", "flensburg", "kiel", "luebeck",
    "ostholstein", "ploen", "herzogtum lauenburg", "stormarn",
    "aurich", "friesland", "wittmund", "emden", "bremerhaven",
    "vorpommern ruegen", "vorpommern greifswald", "rostock",
    "cuxhaven",
}


def get_gelaende(
    county: str, state: str, windzone: WindzoneValue
) -> tuple[str, str]:
    """Kreis/Bundesland/Windzone -> Gelaendekategorie.

    Returns:
        (gelaende, begruendung) mit ``gelaende in {"binnen", "kueste"}``.
    """
    key = norm_kreis(county)

    # Numerische Windzone? (Sonderwerte wie "2*" ausblenden)
    try:
        wz_num = int(windzone)
    except (TypeError, ValueError):
        wz_num = 0

    if key in _KUESTE_KREISE or wz_num >= 3:
        return "kueste", "Kuesten- oder Inselgebiet (WZ >= 3)"
    if state in _KUESTE_STATES:
        return "kueste", f"Bundesland {state} -> Kueste"
    return "binnen", "Binnenland"


__all__ = ["get_gelaende"]
