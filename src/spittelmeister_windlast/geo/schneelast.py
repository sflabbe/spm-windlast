"""Schneelastzone-Lookup nach DIN EN 1991-1-3/NA.

Lookup-Hierarchie (erste Treffer gewinnt):
  1. Amtlicher Kreis-/Gebietscode (5/8-stellig) + Detailtabelle
  2. Exact Match: Kreisname (normalisiert) in der Tabelle
  3. Disambiguierung ueber ``kreis_typ`` oder amtlichen Code
  4. Ambigue-Match: Bei Namenskollision Stadt/Landkreis (z. B. 'muenchen')
     wird der Landkreis-Eintrag bevorzugt (konservativ), wenn kein Typ-Hinweis
     vorliegt.
  5. Teilstring-Match (Legacy-Verhalten)
  6. Default: SLZ '2'

Die amtlichen Gebietscodes sind gefahrdungsneutral und koennen spaeter auch
fuer weitere Kartenwerke (z. B. Seismik) wiederverwendet werden.
"""

from __future__ import annotations

from ..daten import schneelastzone_kreis, schneelastzone_kreis_detail
from ._admin_code import AreaCodeInfo, KreisTyp, area_code_info, state_code_from_name
from ._normalize import norm_kreis

SchneeZoneValue = str  # '1', '1a', '2', '2a', '3', '3a'


def _state_matches(entry: dict | str, state_code: str | None) -> bool:
    if not state_code or not isinstance(entry, dict):
        return True
    bl = entry.get("bundesland")
    if isinstance(bl, list):
        return state_code in bl
    return bl == state_code


def _candidate_keys(county: str, info: AreaCodeInfo, kreis_typ: KreisTyp | None) -> list[str]:
    base = info.kreis_basis_norm or norm_kreis(county)
    typ = kreis_typ or info.kreis_typ_hint
    keys: list[str] = []
    if base and typ:
        keys.append(f"{base} {typ}")
    if base:
        keys.append(base)
        keys.append(f"{base} landkreis")
        keys.append(f"{base} stadt")
    seen: set[str] = set()
    out: list[str] = []
    for k in keys:
        if k and k not in seen:
            out.append(k)
            seen.add(k)
    return out


def _lookup_with_disambig(
    table: dict,
    county: str,
    info: AreaCodeInfo,
    kreis_typ: KreisTyp | None,
    *,
    state: str = "",
) -> tuple[str, str] | None:
    state_code = info.bundesland_code or state_code_from_name(state)
    for key in _candidate_keys(county, info, kreis_typ):
        if key in table and _state_matches(table[key], state_code):
            return key, table[key]
    return None


def get_schneelastzone(
    county: str,
    state: str = "",
    kreis_typ: KreisTyp | None = None,
    area_code: str = "",
) -> tuple[SchneeZoneValue, str]:
    info = area_code_info(area_code)
    table = schneelastzone_kreis()
    key = info.kreis_basis_norm or norm_kreis(county)
    typ_hint = kreis_typ or info.kreis_typ_hint

    hit = _lookup_with_disambig(table, county, info, typ_hint, state=state)
    if hit:
        matched_key, slz = hit
        quelle = f"Kreis '{county or info.kreis_name or matched_key}' -> Tabelle 2022-06-02 (Key: '{matched_key}')"
        if info.kreis_code and matched_key.endswith((" stadt", " landkreis")):
            quelle += f", Disambiguierung aus area_code {area_code}"
        elif info.kreis_code and county == "":
            quelle += f", Lookup via area_code {area_code}"
        return slz, quelle

    if key:
        for k, v in table.items():
            base = k.rsplit(" ", 1)[0] if k.endswith((" stadt", " landkreis")) else k
            if base in key or key in base:
                return v, f"Kreis '{county or info.kreis_name or key}' (Teiluebereinstimmung '{k}') -> Tabelle 2022-06-02"

    return "2", "Standardwert SLZ 2 (Kreis nicht in Tabelle gefunden)"


def get_schneelastzone_detail(
    county: str,
    kreis_typ: KreisTyp | None = None,
    area_code: str = "",
    *,
    state: str = "",
) -> dict | None:
    info = area_code_info(area_code)
    detail = schneelastzone_kreis_detail().get("kreise", {})
    key = info.kreis_basis_norm or norm_kreis(county)
    typ_hint = kreis_typ or info.kreis_typ_hint
    hit = _lookup_with_disambig(detail, county, info, typ_hint, state=state)
    if hit:
        return hit[1]
    for k, v in detail.items():
        base = k.rsplit(" ", 1)[0] if k.endswith((" stadt", " landkreis")) else k
        if base in key or key in base:
            return v
    return None


__all__ = [
    "get_schneelastzone",
    "get_schneelastzone_detail",
    "SchneeZoneValue",
    "KreisTyp",
]
