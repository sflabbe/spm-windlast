"""Geocoding: Adresse -> Koordinaten + Admin-Info via Nominatim (OpenStreetMap).

Respektiert Nominatim Usage Policy: max. 1 Request / Sekunde, User-Agent
ist gesetzt (siehe https://operations.osmfoundation.org/policies/nominatim/).
"""

from __future__ import annotations

import time
from typing import Any

import requests

_NOMINATIM_SEARCH = "https://nominatim.openstreetmap.org/search"
_NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"
_USER_AGENT = "SpittelmeisterWindlast/2.0 (statik@spittelmeister.de)"


def _reverse_postcode(
    lat: float, lon: float, timeout: int = 6
) -> str:
    """Reverse-Geocode -> PLZ. Best-effort, kehrt leer zurueck bei Fehler."""
    try:
        time.sleep(1.1)  # Nominatim-Rate-Limit
        resp = requests.get(
            _NOMINATIM_REVERSE,
            params={
                "lat": lat, "lon": lon, "format": "json",
                "addressdetails": 1, "zoom": 18,
            },
            headers={"User-Agent": _USER_AGENT},
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json().get("address", {}).get("postcode", "")
    except Exception:
        return ""


def geocode_adresse(adresse: str, timeout: int = 8) -> dict[str, Any]:
    """Adresse -> Koordinaten + Adminfelder.

    Returns:
        dict mit Schluesseln: ``lat``, ``lon``, ``display_name``, ``county``,
        ``state``, ``postcode``.

    Raises:
        ValueError: Wenn Nominatim keine Treffer liefert.
        requests.HTTPError: Bei Netzwerk-/HTTP-Fehlern.
    """
    resp = requests.get(
        _NOMINATIM_SEARCH,
        params={
            "q": adresse,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
            "countrycodes": "de",
        },
        headers={"User-Agent": _USER_AGENT},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise ValueError(f"Adresse nicht gefunden: {adresse}")

    r = data[0]
    addr = r.get("address", {})
    county = (
        addr.get("county")
        or addr.get("city")
        or addr.get("town")
        or addr.get("municipality")
        or ""
    )
    state = addr.get("state", "")
    postcode = addr.get("postcode") or addr.get("postal_code") or ""

    if not postcode:
        postcode = _reverse_postcode(float(r["lat"]), float(r["lon"]), timeout)
    else:
        # Auch bei bekannter PLZ kurz warten (Nominatim Policy)
        time.sleep(0.5)

    return {
        "lat": float(r["lat"]),
        "lon": float(r["lon"]),
        "display_name": r.get("display_name", ""),
        "county": county,
        "state": state,
        "postcode": postcode,
    }


__all__ = ["geocode_adresse"]
