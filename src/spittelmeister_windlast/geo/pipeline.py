"""End-to-End-Pipeline: Adresse -> vollstaendige Standortdaten fuer EC1.

Fuehrt nacheinander Geocoding, Hoehenermittlung, Windzone-Lookup und
Gelaendeheuristik aus und retourniert ein ``StandortErgebnis``.
"""

from __future__ import annotations

from .elevation import get_hoehe_uNN
from .gelaende import get_gelaende
from .geocoding import geocode_adresse
from .modelle import StandortErgebnis
from .windzone import get_windzone


def standort_ermitteln(adresse: str) -> StandortErgebnis:
    """Vollstaendige Standortermittlung aus einem Adressstring.

    Args:
        adresse: Freitext-Adresse, z. B. "Marktplatz 1, 97070 Wuerzburg"

    Returns:
        ``StandortErgebnis`` mit Koordinaten, Hoehe, Windzone, Gelaende etc.
    """
    geo = geocode_adresse(adresse)
    lat, lon = geo["lat"], geo["lon"]
    county = geo["county"]
    state = geo["state"]
    postcode = geo.get("postcode", "")

    hoehe, hoehe_quelle = get_hoehe_uNN(lat, lon)
    windzone, wz_quelle = get_windzone(county, state, postcode)
    gelaende, gel_begruendung = get_gelaende(county, state, windzone)

    return StandortErgebnis(
        adresse_eingabe=adresse,
        adresse_gefunden=geo["display_name"],
        lat=lat,
        lon=lon,
        hoehe_uNN=hoehe,
        hoehe_quelle=hoehe_quelle,
        windzone=windzone,
        windzone_quelle=wz_quelle,
        bundesland=state,
        county=county,
        gelaende=gelaende,
        gelaende_begruendung=gel_begruendung,
    )


__all__ = ["standort_ermitteln"]
