"""Windzone-Lookup nach DIN EN 1991-1-4/NA:2010-12, Anhang NA.A.

Lookup-Hierarchie (erste Treffer gewinnt):
  1. Volle PLZ (5-stellig)  -> Tabelle NA.A (Gemeindegenau)
  2. PLZ-Praefix (3-stellig) -> Tabelle NA.A (Gebiet)
  3. Kreisname (normalisiert) -> Tabelle NA.A
  4. Kreisname (Teilstring-Match) -> Tabelle NA.A
  5. Bundesland (Fallback / Standardwert)
  6. Default: WZ 2

Tabellen werden aus dem ``daten``-Paket geladen.
"""

from __future__ import annotations

from ..daten import (
    windzone_bundesland,
    windzone_kreis,
    windzone_plz,
    windzone_plz_prefix,
)
from ._normalize import norm_kreis

WindzoneValue = int | str  # "2*" ist ein gueltiger Wert (Spezialzone)


def get_windzone(
    county: str,
    state: str,
    postcode: str = "",
) -> tuple[WindzoneValue, str]:
    """PLZ / Kreis / Bundesland -> Windzone.

    Args:
        county:   Kreis- oder Stadtname (aus Nominatim ``county``/``city``/``town``)
        state:    Bundesland (aus Nominatim ``state``)
        postcode: Optional, 5-stellige PLZ. Hoechste Prioritaet.

    Returns:
        (windzone, quelle). ``quelle`` ist ein Menschen-lesbarer Text
        (fuer Statik-Doku / Nachvollziehbarkeit).
    """
    plz_table = windzone_plz()
    prefix_table = windzone_plz_prefix()
    kreis_table = windzone_kreis()
    land_table = windzone_bundesland()

    # 1. Volle PLZ
    if postcode and postcode in plz_table:
        return plz_table[postcode], f"PLZ {postcode} -> Tabelle NA.A"

    # 2. PLZ-Praefix (erste 3 Stellen)
    if postcode and len(postcode) >= 3:
        prefix = postcode[:3]
        if prefix in prefix_table:
            return prefix_table[prefix], f"PLZ-Bereich {prefix}xx -> Tabelle NA.A"

    # 3. Kreis direkt
    key = norm_kreis(county)
    if key in kreis_table:
        return kreis_table[key], f"Kreis '{county}' -> Tabelle NA.A"

    # 4. Kreis via Teilstring (z. B. "Landkreis Würzburg" -> "wuerzburg")
    if key:
        for k, v in kreis_table.items():
            if k in key or key in k:
                return v, f"Kreis '{county}' (Teiluebereinstimmung '{k}') -> Tabelle NA.A"

    # 5. Bundesland-Fallback
    if state in land_table:
        return land_table[state], f"Bundesland '{state}' (Standardwert, Kreis nicht in Tabelle)"

    # 6. Default
    return 2, "Standardwert WZ 2 (Kreis/Bundesland nicht gefunden)"


__all__ = ["get_windzone", "WindzoneValue"]
