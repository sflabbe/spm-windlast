from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..core.modelle import Ergebnisse, Geometrie, Projekt, Standort
from ..transfer import derive_support_action
from ..transfer.mapping import derive_connection_actions_from_snapshot
from ..transfer.modelle import ConnectionActions, SupportAction
from ..verankerung.modelle import AnchorageAssessment, AnchorageInput
from .base import PreambleStyle, ProtokolHeader, build_document
from .protokoll_verankerung import verankerung_body
from .protokoll_windlast import windlast_body
from .report_selection import ReportSelection


@dataclass
class CombinedRuntimeData:
    projekt: Projekt
    standort: Standort
    geo: Geometrie
    windlast: Ergebnisse | None = None
    connection_actions: ConnectionActions | None = None
    anchorage_input: AnchorageInput | None = None
    anchorage_assessment: AnchorageAssessment | None = None
    support_action: SupportAction | None = None


def protokol_header_from_project_meta(meta: Mapping[str, Any] | None) -> ProtokolHeader:
    meta = meta or {}
    return ProtokolHeader(
        projekt_nr=str(meta.get("project_id", "2026-WB-001")),
        projekt_bez=str(meta.get("title", "Windnachweis Balkonanschluss")),
        strasse=str(meta.get("street", "")),
        ort=str(meta.get("city", "")),
        bauherr=str(meta.get("client", "")),
        bearbeiter=str(meta.get("bearbeiter", "")),
        revision=str(meta.get("revision", "0")),
        datum=str(meta.get("datum", "")),
    )


def _project_from_meta(meta: Mapping[str, Any] | None) -> Projekt:
    meta = meta or {}
    return Projekt(
        bezeichnung=str(meta.get("title", "Windnachweis Balkonanschluss")),
        nummer=str(meta.get("project_id", "2026-WB-001")),
        bearbeiter=str(meta.get("bearbeiter", "")),
        datum=str(meta.get("datum", "")),
    )


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return int(default)
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _standort_from_wind_input(wind_input: Mapping[str, Any]) -> Standort:
    return Standort(
        bezeichnung=str(wind_input.get("standort_bez", wind_input.get("adresse", "Standort"))),
        windzone=_as_int(wind_input.get("windzone", 1), 1),
        gelaende=str(wind_input.get("gelaende", "binnen")),
        hoehe_uNN=_as_float(wind_input.get("hoehe_uNN", 0.0)),
    )


def _geo_from_wind_input(wind_input: Mapping[str, Any]) -> Geometrie:
    return Geometrie(
        h=_as_float(wind_input.get("h_gebaeude", 0.0)),
        d=max(_as_float(wind_input.get("d_gebaeude", 1.0), 1.0), 1e-6),
        b=max(_as_float(wind_input.get("b_gebaeude", 1.0), 1.0), 1e-6),
        z_balkon=_as_float(wind_input.get("z_balkon", 0.0)),
        e_balkon=_as_float(wind_input.get("e_balkon", wind_input.get("balkon_tiefe", 0.0))),
        h_abschluss=_as_float(wind_input.get("h_abschl", wind_input.get("hoehe_gelaender_abschattung", 0.0))),
        s_verankerung=_as_float(wind_input.get("s_verank", wind_input.get("balkon_breite", 0.0))),
        b_auflager_rand=_as_float(wind_input.get("b_auflager_rand", wind_input.get("verankerung_randabstand", 0.0))),
    )


def _wind_results_from_snapshot(wind_results: Mapping[str, Any]) -> Ergebnisse | None:
    if not wind_results:
        return None
    try:
        return Ergebnisse(**dict(wind_results))
    except TypeError:
        return None


def build_combined_runtime_data(
    project_meta: Mapping[str, Any] | None,
    wind_state: Mapping[str, Any] | None,
    verankerung_state: Mapping[str, Any] | None,
) -> CombinedRuntimeData:
    wind_state = wind_state or {}
    verankerung_state = verankerung_state or {}
    wind_input = dict(wind_state.get("input", {}))
    wind_results = dict(wind_state.get("results_snapshot", {}))
    ver_input = dict(verankerung_state.get("input", {}))
    ver_results = dict(verankerung_state.get("results_snapshot", {}))

    projekt = _project_from_meta(project_meta)
    standort = _standort_from_wind_input(wind_input)
    geo = _geo_from_wind_input(wind_input)
    windlast = _wind_results_from_snapshot(wind_results)

    connection_actions: ConnectionActions | None = None
    if wind_input and wind_results:
        try:
            connection_actions = derive_connection_actions_from_snapshot(wind_input, wind_results)
        except Exception:
            connection_actions = None

    anchorage_input = AnchorageInput.from_mapping(ver_input) if ver_input else None
    anchorage_assessment = AnchorageAssessment.from_mapping(ver_results) if ver_results else None
    support_action: SupportAction | None = None
    raw_support_action = ver_results.get("support_action")
    if isinstance(raw_support_action, Mapping):
        support_action = SupportAction.from_mapping(raw_support_action)
    elif anchorage_input is not None and connection_actions is not None:
        support_action = derive_support_action(
            connection_actions,
            support_index=anchorage_input.support_index,
            support_role=anchorage_input.support_role,
            slide_direction=anchorage_input.slide_direction,
            local_eccentricity_mm=anchorage_input.local_eccentricity_mm,
            platform_eccentricity_mm=float(anchorage_input.platform_eccentricity_mm or 0.0),
        )
    return CombinedRuntimeData(
        projekt=projekt,
        standort=standort,
        geo=geo,
        windlast=windlast,
        connection_actions=connection_actions,
        anchorage_input=anchorage_input,
        anchorage_assessment=anchorage_assessment,
        support_action=support_action,
    )


def _cover_page(header: ProtokolHeader, selection: ReportSelection) -> str:
    modules = ", ".join(selection.selected_module_labels()) or "Keine Module"
    address_line = ""
    if header.strasse or header.ort:
        address_line = f"{header.strasse} {header.ort}".strip()
    return rf"""
\begin{{titlepage}}
{{\Large\bfseries Statische Berechnung}}\\[6pt]
{{\large {header.projekt_bez}}}\\[4pt]
Projekt-Nr.: {header.projekt_nr}\\
Bearbeiter: {header.bearbeiter}\\
Datum: {header.datum}\\
Revision: {header.revision}\\
Auftraggeber: {header.bauherr}\\
Objekt: {address_line}\\[8pt]
Berichtsgegenstand: {modules}
\end{{titlepage}}
"""


def render_combined_report(
    header: ProtokolHeader,
    selection: ReportSelection,
    runtime_data: CombinedRuntimeData,
) -> str:
    parts = [_cover_page(header, selection)]
    if selection.windlast.include and runtime_data.windlast is not None:
        parts.append(
            windlast_body(
                runtime_data.projekt,
                runtime_data.standort,
                runtime_data.geo,
                runtime_data.windlast,
                report_style="combined",
            )
        )
    if selection.verankerung.include and runtime_data.connection_actions is not None:
        parts.append(
            verankerung_body(
                runtime_data.connection_actions,
                runtime_data.anchorage_assessment,
                runtime_data.anchorage_input,
                runtime_data.support_action,
                report_style="combined",
            )
        )
    body = "\n\n".join(parts)
    return build_document(header.modus, body, style=PreambleStyle.COMBINED_NEUTRAL.value)
