"""Hoehenmodell-Abfrage (Hoehe ueber NN).

Primaer: open-elevation.com (SRTM, weltweit, kostenlos).
Fallback: opentopodata.org (SRTM30m).
"""

from __future__ import annotations

import requests

_OPEN_ELEVATION = "https://api.open-elevation.com/api/v1/lookup"
_OPENTOPODATA = "https://api.opentopodata.org/v1/srtm30m"


def get_hoehe_uNN(
    lat: float, lon: float, timeout: int = 8
) -> tuple[float | None, str]:
    """Koordinaten -> Hoehe ueber NN [m].

    Returns:
        (hoehe, quelle). ``hoehe`` ist ``None``, wenn beide APIs fehlschlagen.
    """
    # Primaer: open-elevation
    try:
        resp = requests.post(
            _OPEN_ELEVATION,
            json={"locations": [{"latitude": lat, "longitude": lon}]},
            timeout=timeout,
        )
        resp.raise_for_status()
        h = resp.json()["results"][0]["elevation"]
        return float(h), "open-elevation.com (SRTM)"
    except Exception:
        pass

    # Fallback: opentopodata
    try:
        resp = requests.get(
            f"{_OPENTOPODATA}?locations={lat},{lon}", timeout=timeout
        )
        resp.raise_for_status()
        h = resp.json()["results"][0]["elevation"]
        return float(h), "opentopodata.org (SRTM30m)"
    except Exception:
        pass

    return None, "nicht verfuegbar"


__all__ = ["get_hoehe_uNN"]
