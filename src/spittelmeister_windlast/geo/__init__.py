"""Standortermittlung — Geocoding, Hoehe, Wind-/Schneezonen, Gelaende.

Die `geo`-API bleibt importierbar, auch wenn optionale Abhaengigkeiten wie
`requests` oder Netz-APIs lokal nicht verfuegbar sind. Requests-lastige Module
werden daher erst beim Funktionsaufruf importiert.
"""

from __future__ import annotations

from ._admin_code import area_code_info, state_code_from_name
from .modelle import StandortErgebnis
from .erdbeben import get_erdbeben_coverage, get_erdbeben_records
from .schneelast import get_schneelastzone, get_schneelastzone_detail
from .windzone import get_windzone, get_windzone_detail


def geocode_adresse(*args, **kwargs):
    from .geocoding import geocode_adresse as _impl
    return _impl(*args, **kwargs)


def get_hoehe_uNN(*args, **kwargs):
    from .elevation import get_hoehe_uNN as _impl
    return _impl(*args, **kwargs)


def get_gelaende(*args, **kwargs):
    from .gelaende import get_gelaende as _impl
    return _impl(*args, **kwargs)


def standort_ermitteln(*args, **kwargs):
    from .pipeline import standort_ermitteln as _impl
    return _impl(*args, **kwargs)


__all__ = [
    "StandortErgebnis",
    "area_code_info",
    "state_code_from_name",
    "standort_ermitteln",
    "geocode_adresse",
    "get_hoehe_uNN",
    "get_windzone",
    "get_windzone_detail",
    "get_schneelastzone",
    "get_schneelastzone_detail",
    "get_erdbeben_coverage",
    "get_erdbeben_records",
    "get_gelaende",
]
