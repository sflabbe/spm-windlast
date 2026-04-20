"""Datenorientierter Zugriff auf das integrierte Erdbeben-Tabellenwerk.

Kein vollwertiger "Bemessungs-Lookup", sondern eine robuste Suchschicht über
das normalisierte JSON-Dataset. Ziel ist vor allem, die Verwaltungslogik
(area_code / Kreiscode / Bundesland) gefahrdungsneutral zu halten, damit
spaeter weitere Kartenwerke sauber andocken koennen.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from ..daten import erdbebenzonen_dataset
from ._admin_code import area_code_info, state_code_from_name
from ._normalize import norm_kreis


@lru_cache(maxsize=1)
def _record_map() -> dict[int, dict[str, Any]]:
    return {int(r["id"]): r for r in erdbebenzonen_dataset()["records"]}


def _state_code_from_inputs(state: str = "", area_code: str = "") -> str | None:
    info = area_code_info(area_code)
    return info.bundesland_code or state_code_from_name(state) or info.state_code


def get_erdbeben_coverage(state: str = "", area_code: str = "") -> dict[str, Any] | None:
    """Gibt den Coverage-/Status-Eintrag des betroffenen Bundeslandes zurück."""
    code = _state_code_from_inputs(state=state, area_code=area_code)
    if not code:
        return None
    return erdbebenzonen_dataset().get("coverage", {}).get(code)


def get_erdbeben_records(
    *,
    area_code: str = "",
    state: str = "",
    county: str = "",
    municipality: str = "",
) -> dict[str, Any]:
    """Sucht Datensätze im integrierten Erdbeben-Tabellenwerk.

    Rückgabeformat:
      {
        "status": "ok" | "external_map_required" | "not_found",
        "state_code": "...",
        "coverage": {...} | None,
        "matches": [records...],
        "zone_values": [...],
        "ground_classes": [...]
      }

    Für Baden-Württemberg liefert das Tabellenwerk bewusst keinen tabellarischen
    Eintrag, sondern einen expliziten Verweis auf die amtliche Kartenquelle.
    """
    data = erdbebenzonen_dataset()
    info = area_code_info(area_code)
    state_code = _state_code_from_inputs(state=state, area_code=area_code)
    coverage = data.get("coverage", {}).get(state_code) if state_code else None

    if coverage and coverage.get("mode") in {"external_map_only", "external_map_reference"}:
        return {
            "status": "external_map_required",
            "state_code": state_code,
            "coverage": coverage,
            "matches": [],
            "zone_values": [],
            "ground_classes": [],
            "query": {
                "area_code": area_code,
                "county": county,
                "municipality": municipality,
                "state": state,
            },
        }

    ids: list[int] = []
    if info.kind == "gemeinde_8" and info.digits:
        ids.extend(int(i) for i in data.get("index", {}).get("area_code_8", {}).get(info.digits, []))
    if not ids and info.kreis_code:
        ids.extend(int(i) for i in data.get("index", {}).get("kreis_code_5", {}).get(info.kreis_code, []))

    county_norm = norm_kreis(county or info.kreis_name or "")
    municipality_norm = norm_kreis(municipality)

    if not ids:
        for rec in data["records"]:
            if state_code and rec.get("state_code") != state_code:
                continue
            if county_norm and rec.get("county_name_normalized") != county_norm:
                continue
            if municipality_norm:
                rec_muni = rec.get("municipality_name_normalized")
                if rec_muni not in {municipality_norm, "alle"}:
                    continue
            ids.append(int(rec["id"]))

    # De-duplicate while preserving order
    seen: set[int] = set()
    uniq_ids: list[int] = []
    for rid in ids:
        if rid not in seen:
            uniq_ids.append(rid)
            seen.add(rid)

    matches = [_record_map()[rid] for rid in uniq_ids if rid in _record_map()]
    zone_values = sorted({m["earthquake_zone"] for m in matches if m.get("earthquake_zone") is not None})
    ground_classes = sorted({m["ground_class"] for m in matches if m.get("ground_class")})

    return {
        "status": "ok" if matches else "not_found",
        "state_code": state_code,
        "coverage": coverage,
        "matches": matches,
        "zone_values": zone_values,
        "ground_classes": ground_classes,
        "query": {
            "area_code": area_code,
            "county": county,
            "municipality": municipality,
            "state": state,
        },
    }


__all__ = [
    "get_erdbeben_coverage",
    "get_erdbeben_records",
]
