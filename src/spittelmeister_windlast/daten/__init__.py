"""Normativen Lookup-Tabellen (DIN EN 1991-1-4/NA:2010-12 + 1991-1-3/NA).

Daten werden als JSON ausgeliefert und ueber `importlib.resources` geladen.
Damit bleiben die Tabellen diff-freundlich und sind ohne Python-Aenderung
aktualisierbar.

Quellen:
  - qb0.json: DIN EN 1991-1-4/NA:2010-12, Tabelle NA.A.1 (Basiswindgeschwindigkeitsdruck)
  - windzone_*.json: "Windzonen nach Verwaltungsgrenzen", Stand 2022-06-02 (amtliche Daten, mit Legacy-Alias-Schluesseln zusammengefuehrt)
  - schneelastzone_*.json: "Schneelastzonen nach Verwaltungsgrenzen", Stand 2022-06-02
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any


def _load(name: str) -> Any:
    """JSON-Datei aus dem `daten`-Paket laden."""
    text = files(__name__).joinpath(name).read_text(encoding="utf-8")
    return json.loads(text)


# ── Peak-Pressure ──────────────────────────────────────────────────────────


@lru_cache(maxsize=None)
def qb0_table() -> dict[int, float]:
    """q_{b,0} [kN/m^2] pro Windzone."""
    raw = _load("qb0.json")
    return {int(k): float(v) for k, v in raw.items() if not k.startswith("_")}


# ── Wind ───────────────────────────────────────────────────────────────────


@lru_cache(maxsize=None)
def windzone_kreis() -> dict[str, int | str]:
    """Flaches Lookup: normalisierter Kreisname -> dominante Windzone."""
    return _load("windzone_kreis.json")


@lru_cache(maxsize=None)
def windzone_kreis_detail() -> dict[str, Any]:
    """Reiches Lookup mit Varianten pro Kreis.

    Struktur:
        {
          "metadata": {...},
          "kreise": {
            "ostholstein": {
              "name": "Ostholstein",
              "bundesland": "SH",
              "windzone_dominant": 4,
              "varianten": [
                {"windzone": 2, "gemeinden": "alle Gemeinden, soweit nicht ..."},
                {"windzone": 3, "gemeinden": "Amtsbereich Oldenburg Land ..."},
                {"windzone": 4, "gemeinden": "Insel Fehmarn"}
              ]
            }, ...
          }
        }
    """
    return _load("windzone_kreis_detail.json")


@lru_cache(maxsize=None)
def windzone_plz() -> dict[str, int | str]:
    return _load("windzone_plz.json")


@lru_cache(maxsize=None)
def windzone_plz_prefix() -> dict[str, int | str]:
    return _load("windzone_plz_prefix.json")


@lru_cache(maxsize=None)
def windzone_bundesland() -> dict[str, int | str]:
    return _load("windzone_bundesland.json")


# ── Schnee ─────────────────────────────────────────────────────────────────


@lru_cache(maxsize=None)
def schneelastzone_kreis() -> dict[str, str]:
    """Flaches Lookup: Kreisname -> dominante Schneelastzone ('1', '1a', '2', '2a', '3')."""
    return _load("schneelastzone_kreis.json")


@lru_cache(maxsize=None)
def schneelastzone_kreis_detail() -> dict[str, Any]:
    """Reiches Lookup mit SLZ-Varianten pro Kreis (inkl. Fussnoten, Beispiel-Gemeinden)."""
    return _load("schneelastzone_kreis_detail.json")


@lru_cache(maxsize=None)
def admin_kreise_codes() -> dict[str, Any]:
    """Amtliche Kreis-/Stadtschluessel nach Destatis (5-stellig)."""
    return _load("admin_kreise_codes.json")


# ── Erdbeben / DIN 4149 Tabellenwerk ───────────────────────────────────────


@lru_cache(maxsize=None)
def erdbebenzonen_dataset() -> dict[str, Any]:
    """Normatives Erdbeben-Tabellenwerk aus dem bereitgestellten Excel-Export.

    Enthält:
      - coverage: Bundesland-Status (tabellarisch vs. externer Kartenverweis)
      - index: vorbereitete Indizes für 5-/8-stellige Verwaltungscodes
      - records: normalisierte Datensätze je Gemeinde/Gemarkung
    """
    return _load("erdbebenzonen_dataset.json")


__all__ = [
    # Peak-Pressure
    "qb0_table",
    # Wind
    "windzone_kreis",
    "windzone_kreis_detail",
    "windzone_plz",
    "windzone_plz_prefix",
    "windzone_bundesland",
    # Schnee
    "schneelastzone_kreis",
    "schneelastzone_kreis_detail",
    # Amtliche Verwaltungsschluessel
    "admin_kreise_codes",
    # Erdbeben / DIN 4149
    "erdbebenzonen_dataset",
]
