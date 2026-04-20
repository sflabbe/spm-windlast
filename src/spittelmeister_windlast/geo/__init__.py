"""Standortermittlung — Geocoding, Hoehe, Windzone, Gelaende.

Abhaengigkeit: ``requests`` (fuer externe APIs).
Keine UI-Abhaengigkeiten (kein Streamlit, kein Folium).
"""

from .elevation import get_hoehe_uNN
from .gelaende import get_gelaende
from .geocoding import geocode_adresse
from .modelle import StandortErgebnis
from .pipeline import standort_ermitteln
from .windzone import get_windzone

__all__ = [
    "StandortErgebnis",
    "standort_ermitteln",
    "geocode_adresse",
    "get_hoehe_uNN",
    "get_windzone",
    "get_gelaende",
]
