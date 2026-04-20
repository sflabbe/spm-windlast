"""Normativen Lookup-Tabellen (DIN EN 1991-1-4/NA:2010-12).

Daten werden als JSON ausgeliefert und ueber `importlib.resources` geladen.
Damit bleiben die Tabellen diff-freundlich und sind ohne Python-Aenderung
aktualisierbar.
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


@lru_cache(maxsize=None)
def qb0_table() -> dict[int, float]:
    """q_{b,0} [kN/m^2] pro Windzone."""
    raw = _load("qb0.json")
    return {int(k): float(v) for k, v in raw.items() if not k.startswith("_")}


@lru_cache(maxsize=None)
def windzone_kreis() -> dict[str, int | str]:
    return _load("windzone_kreis.json")


@lru_cache(maxsize=None)
def windzone_plz() -> dict[str, int | str]:
    return _load("windzone_plz.json")


@lru_cache(maxsize=None)
def windzone_plz_prefix() -> dict[str, int | str]:
    return _load("windzone_plz_prefix.json")


@lru_cache(maxsize=None)
def windzone_bundesland() -> dict[str, int | str]:
    return _load("windzone_bundesland.json")


__all__ = [
    "qb0_table",
    "windzone_kreis",
    "windzone_plz",
    "windzone_plz_prefix",
    "windzone_bundesland",
]
