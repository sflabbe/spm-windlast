"""Windzone-Lookup nach DIN EN 1991-1-4/NA:2010-12, Anhang NA.A.

Lookup-Hierarchie (erste Treffer gewinnt):
  1. Volle PLZ (5-stellig)  -> Tabelle NA.A (gemeindegenau, soweit vorhanden)
  2. PLZ-Praefix (3-stellig) -> Tabelle NA.A (Gebiet)
  3. Amtlicher Kreis-/Gebietscode (5/8-stellig) + Detailtabelle
  4. Kreis / Stadt via Detaildaten + optionaler Disambiguierung
     (``kreis_typ`` oder ``area_code``/AGS)
  5. Flacher Kreisname (Legacy-Tabelle)
  6. Kreisname (Teilstring-Match)
  7. Bundesland (Fallback / Standardwert)
  8. Default: WZ 2

Tabellen werden aus dem ``daten``-Paket geladen.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from ..daten import (
    windzone_bundesland,
    windzone_kreis,
    windzone_kreis_detail,
    windzone_plz,
    windzone_plz_prefix,
)
from ._admin_code import AreaCodeInfo, KreisTyp, area_code_info, state_code_from_name
from ._normalize import norm_kreis, norm_kreis_basis

WindzoneValue = int | str  # "2*" ist ein gueltiger Wert (Spezialzone)


@lru_cache(maxsize=1)
def _bundesland_normalized_index() -> dict[str, tuple[str, WindzoneValue]]:
    return {
        norm_kreis(name): (name, wz)
        for name, wz in windzone_bundesland().items()
    }


def _guess_type_from_name(name: str) -> KreisTyp | None:
    n = (name or "").lower()
    if n.startswith(("landeshauptstadt ", "kreisfreie stadt ", "kreisfreie staedte ", "stadtkreis ", "stadt ")):
        return "stadt"
    if n.startswith(("landkreis ", "kreis ")):
        return "landkreis"
    return None


def _state_matches(entry: dict[str, Any], state_code: str | None) -> bool:
    if not state_code:
        return True
    return str(entry.get("bundesland") or "") == state_code


@lru_cache(maxsize=1)
def _detail_alias_index() -> dict[tuple[str, str | None, KreisTyp], str]:
    """Index: (Basisname, BL, Typ) -> Key in ``windzone_kreis_detail``."""
    detail = windzone_kreis_detail().get("kreise", {})
    by_base_state: dict[tuple[str, str | None], dict[str, list[str]]] = {}
    for key, entry in detail.items():
        name = str(entry.get("name") or key)
        base = norm_kreis_basis(name or key)
        if not base:
            continue
        state = entry.get("bundesland")
        typ = entry.get("typ") or _guess_type_from_name(name)
        bucket = by_base_state.setdefault((base, state), {"stadt": [], "landkreis": [], "untyped": []})
        if typ in ("stadt", "landkreis"):
            bucket[typ].append(key)
        else:
            bucket["untyped"].append(key)

    index: dict[tuple[str, str | None, KreisTyp], str] = {}
    for (base, state), bucket in by_base_state.items():
        if bucket["stadt"]:
            index[(base, state, "stadt")] = bucket["stadt"][0]
        if bucket["landkreis"]:
            index[(base, state, "landkreis")] = bucket["landkreis"][0]
        if not bucket["landkreis"] and bucket["untyped"] and bucket["stadt"]:
            index[(base, state, "landkreis")] = bucket["untyped"][0]
        if not bucket["stadt"] and not bucket["landkreis"] and bucket["untyped"]:
            index[(base, state, "stadt")] = bucket["untyped"][0]
            index[(base, state, "landkreis")] = bucket["untyped"][0]
    return index


def _resolve_typ_hint(county: str, kreis_typ: KreisTyp | None, info: AreaCodeInfo) -> KreisTyp | None:
    return kreis_typ or info.kreis_typ_hint or _guess_type_from_name(county)


def _candidate_norm_keys(county: str, info: AreaCodeInfo) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for key in [norm_kreis(county), info.kreis_name_norm, info.kreis_basis_norm]:
        if key and key not in seen:
            out.append(key)
            seen.add(key)
    return out


def _detail_lookup(
    county: str,
    state: str = "",
    kreis_typ: KreisTyp | None = None,
    area_code: str = "",
) -> tuple[str, dict[str, Any], str] | None:
    detail = windzone_kreis_detail().get("kreise", {})
    info = area_code_info(area_code)
    state_code = info.bundesland_code or state_code_from_name(state)
    basis = info.kreis_basis_norm or norm_kreis_basis(county)
    exact_keys = _candidate_norm_keys(county, info)
    typ_hint = _resolve_typ_hint(county, kreis_typ, info)

    if typ_hint and basis:
        for state_key in [state_code, None]:
            alias = _detail_alias_index().get((basis, state_key, typ_hint))
            if alias and alias in detail:
                grund = f"Disambiguierung '{typ_hint}'"
                if info.kreis_code:
                    grund += f" aus area_code {area_code}"
                return alias, detail[alias], grund

    for key in exact_keys:
        if key in detail and _state_matches(detail[key], state_code):
            grund = "Detailtabelle"
            if info.kreis_code:
                grund += f" (area_code {area_code})"
            return key, detail[key], grund

    if basis:
        for k, entry in detail.items():
            key_base = norm_kreis_basis(str(entry.get("name") or k))
            if key_base == basis and _state_matches(entry, state_code):
                grund = "Detailtabelle (Basisname-Scan)"
                if info.kreis_code:
                    grund += f" aus area_code {area_code}"
                return k, entry, grund

    return None


def _flat_lookup_by_candidates(
    table: dict[str, WindzoneValue],
    county: str,
    info: AreaCodeInfo,
) -> tuple[WindzoneValue, str] | None:
    for key in _candidate_norm_keys(county, info):
        if key in table:
            if info.kreis_code and key in {info.kreis_name_norm, info.kreis_basis_norm}:
                return table[key], (
                    f"area_code {info.raw} -> Kreisschluessel {info.kreis_code} "
                    f"({info.kreis_name}) -> Tabelle NA.A"
                )
            return table[key], f"Kreis '{county or info.kreis_name}' -> Tabelle NA.A"
    return None


def get_windzone(
    county: str,
    state: str,
    postcode: str = "",
    *,
    kreis_typ: KreisTyp | None = None,
    area_code: str = "",
) -> tuple[WindzoneValue, str]:
    """PLZ / Kreis / Bundesland / amtlicher Gebietscode -> Windzone."""
    plz_table = windzone_plz()
    prefix_table = windzone_plz_prefix()
    kreis_table = windzone_kreis()
    info = area_code_info(area_code)

    if postcode and postcode in plz_table:
        return plz_table[postcode], f"PLZ {postcode} -> Tabelle NA.A"

    if postcode and len(postcode) >= 3:
        prefix = postcode[:3]
        if prefix in prefix_table:
            return prefix_table[prefix], f"PLZ-Bereich {prefix}xx -> Tabelle NA.A"

    detail_hit = _detail_lookup(county, state=state, kreis_typ=kreis_typ, area_code=area_code)
    if detail_hit:
        matched_key, entry, grund = detail_hit
        wz = entry.get("windzone_dominant")
        if wz is not None:
            label = county or info.kreis_name or matched_key
            return wz, f"Kreis '{label}' -> Tabelle NA.A ({grund}, Key: '{matched_key}')"

    flat_hit = _flat_lookup_by_candidates(kreis_table, county, info)
    if flat_hit:
        return flat_hit

    key = norm_kreis(county)
    if key:
        for k, v in kreis_table.items():
            if k in key or key in k:
                return v, f"Kreis '{county}' (Teiluebereinstimmung '{k}') -> Tabelle NA.A"

    land_index = _bundesland_normalized_index()
    state_key = norm_kreis(info.bundesland_name or state)
    if state_key in land_index:
        canonical_name, wz = land_index[state_key]
        return wz, f"Bundesland '{canonical_name}' (Standardwert, Kreis nicht in Tabelle)"

    return 2, "Standardwert WZ 2 (Kreis/Bundesland nicht gefunden)"


def get_windzone_detail(
    county: str,
    *,
    state: str = "",
    kreis_typ: KreisTyp | None = None,
    area_code: str = "",
) -> dict[str, Any] | None:
    """Detaildatensatz fuer Kreis/Stadt, optional code-disambiguiert."""
    hit = _detail_lookup(county, state=state, kreis_typ=kreis_typ, area_code=area_code)
    if hit:
        return hit[1]
    return None


__all__ = ["get_windzone", "get_windzone_detail", "WindzoneValue"]
