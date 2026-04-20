"""Normalisierung von Kreis-/Ortsnamen fuer Tabellen-Lookup."""

from __future__ import annotations

import re

_UMLAUTE = {
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "Ä": "ae", "Ö": "oe", "Ü": "ue",
}

_PREFIXE = re.compile(r"(landkreis|kreis|stadt|lk\.|sk\.|,.*)")
_NONALNUM = re.compile(r"[^a-z0-9 ]")


def norm_kreis(s: str) -> str:
    """Normalisiert Kreis-/Stadtnamen fuer den Lookup in ``daten/windzone_*``.

    Regeln:
      - lowercase
      - Umlaute / ss-Aufloesung
      - Entfernt Praefixe wie "Landkreis", "Stadt" sowie alles nach Komma
      - Nicht-alphanumerisch -> Leerzeichen
      - getrimmt

    Beispiele:
        >>> norm_kreis("Landkreis Würzburg")
        'wuerzburg'
        >>> norm_kreis("Kreis Rhön-Grabfeld, Bayern")
        'rhoen grabfeld'
    """
    s = s.lower()
    for u, r in _UMLAUTE.items():
        s = s.replace(u.lower(), r)
    s = _PREFIXE.sub("", s)
    s = _NONALNUM.sub(" ", s)
    return " ".join(s.split()).strip()


__all__ = ["norm_kreis"]
