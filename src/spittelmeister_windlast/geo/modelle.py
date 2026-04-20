"""Datenstrukturen der Standortermittlung."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StandortErgebnis:
    """Vollstaendiges Ergebnis der Standortermittlung aus einer Adresse."""
    adresse_eingabe: str
    adresse_gefunden: str
    lat: float
    lon: float
    hoehe_uNN: float | None
    hoehe_quelle: str
    windzone: int | str
    windzone_quelle: str
    bundesland: str
    county: str
    gelaende: str   # "binnen" | "kueste" | "nordsee"
    gelaende_begruendung: str


__all__ = ["StandortErgebnis"]
