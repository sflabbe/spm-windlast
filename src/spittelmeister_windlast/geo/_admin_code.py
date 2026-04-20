"""Hilfen fuer optionale Verwaltungs-/Gebietscodes (AGS / Kreisschluessel).

Diese Schicht ist bewusst gefahrstoff-/norm-neutral gehalten, damit spaeter
weitere Gefaehrdungen (z. B. Schnee, Seismik) auf derselben amtlichen
Verwaltungseinheit aufsetzen koennen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..daten import admin_kreise_codes

KreisTyp = Literal["stadt", "landkreis"]
CodeKind = Literal["kreis_5", "gemeinde_8", "unknown"]


@dataclass(frozen=True)
class AreaCodeInfo:
    """Aufgeloeste Informationen zu einem optionalen Gebietscode."""

    raw: str
    digits: str
    kind: CodeKind
    state_code: str | None
    kreis_code: str | None
    kreis_typ_hint: KreisTyp | None
    kreis_name: str | None
    kreis_name_norm: str | None
    kreis_basis_norm: str | None
    bundesland_code: str | None
    bundesland_name: str | None


_STATE_ALIASES = {
    "sh": "SH", "schleswig holstein": "SH",
    "hh": "HH", "hamburg": "HH",
    "ni": "NI", "niedersachsen": "NI",
    "hb": "HB", "bremen": "HB",
    "nw": "NW", "nordrhein westfalen": "NW",
    "he": "HE", "hessen": "HE",
    "rp": "RP", "rheinland pfalz": "RP",
    "bw": "BW", "baden wuerttemberg": "BW", "baden wurttemberg": "BW",
    "by": "BY", "bayern": "BY",
    "sl": "SL", "saarland": "SL",
    "be": "BE", "berlin": "BE",
    "bb": "BB", "brandenburg": "BB",
    "mv": "MV", "mecklenburg vorpommern": "MV",
    "sn": "SN", "sachsen": "SN",
    "st": "ST", "sachsen anhalt": "ST",
    "th": "TH", "thueringen": "TH", "thuringen": "TH",
}


def state_code_from_name(value: str) -> str | None:
    digits = _digits_only(value)
    if len(digits) == 2 and digits in {
        "01","02","03","04","05","06","07","08","09","10","11","12","13","14","15","16"
    }:
        # Falls jemand versehentlich nur den numerischen BL-Code uebergibt, nicht auf Akronym mappen.
        return None
    key = " ".join(str(value or "").lower().replace("-", " ").split())
    return _STATE_ALIASES.get(key)


def _digits_only(value: str) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _kreis_codes_table() -> dict:
    return admin_kreise_codes().get("codes", {})


def area_code_info(area_code: str) -> AreaCodeInfo:
    """Parst einen optionalen AGS/Kreisschluessel und reichert ihn an.

    Unterstuetzt:
    - 5-stelligen Kreisschluessel / Kreis-ARS (amtlicher Kreiscode)
    - 8-stelligen AGS/Gemeindeschluessel; der Kreiscode ist dann ``digits[:5]``

    Wenn der Kreiscode in der amtlichen Destatis-Tabelle vorhanden ist, werden
    Name, Bundesland und Kreis-Typ direkt aus dieser Tabelle gezogen.
    """
    digits = _digits_only(area_code)
    if len(digits) == 5:
        kind: CodeKind = "kreis_5"
        kreis_code = digits
    elif len(digits) == 8:
        kind = "gemeinde_8"
        kreis_code = digits[:5]
    else:
        return AreaCodeInfo(
            raw=area_code,
            digits=digits,
            kind="unknown",
            state_code=digits[:2] if len(digits) >= 2 else None,
            kreis_code=None,
            kreis_typ_hint=None,
            kreis_name=None,
            kreis_name_norm=None,
            kreis_basis_norm=None,
            bundesland_code=None,
            bundesland_name=None,
        )

    rec = _kreis_codes_table().get(kreis_code)
    typ = rec.get("type") if rec else None
    return AreaCodeInfo(
        raw=area_code,
        digits=digits,
        kind=kind,
        state_code=kreis_code[:2],
        kreis_code=kreis_code,
        kreis_typ_hint=typ,
        kreis_name=rec.get("name") if rec else None,
        kreis_name_norm=rec.get("name_normalized") if rec else None,
        kreis_basis_norm=rec.get("base_name_normalized") if rec else None,
        bundesland_code=rec.get("bundesland_code") if rec else None,
        bundesland_name=rec.get("bundesland_name") if rec else None,
    )


def kreis_typ_from_area_code(area_code: str) -> KreisTyp | None:
    """Leitet den Kreis-Typ aus 5- oder 8-stelligem Gebietscode ab."""
    return area_code_info(area_code).kreis_typ_hint


__all__ = [
    "AreaCodeInfo",
    "CodeKind",
    "KreisTyp",
    "area_code_info",
    "kreis_typ_from_area_code",
    "state_code_from_name",
]
