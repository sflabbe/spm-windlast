from __future__ import annotations

from typing import Any, Mapping

from ..core.modelle import Ergebnisse, Geometrie
from .modelle import ConnectionActions
from .vereinfachtes_balkonsystem import derive_connection_actions_simple


def _has_existing_actions(data: Mapping[str, Any]) -> bool:
    keys = ("Hx_k", "Hy_1_k", "Hy_2_k", "M_A_k", "Hx_Ed", "Hy_1_Ed", "Hy_2_Ed")
    for key in keys:
        raw = data.get(key, 0.0)
        try:
            if abs(float(raw)) > 0.0:
                return True
        except (TypeError, ValueError):
            continue
    return False


def derive_connection_actions_from_wind(
    geo: Geometrie,
    ergebnisse: Ergebnisse,
) -> ConnectionActions:
    """Leitet Anschlussgrößen aus dem bestehenden Wind-Ergebnis ab."""
    if _has_existing_actions(vars(ergebnisse)):
        return ConnectionActions.from_mapping(
            {
                **vars(ergebnisse),
                "trace": ["Aus bestehendem Ergebnisse-Objekt übernommen."],
            }
        )

    return derive_connection_actions_simple(
        B=geo.s_verankerung,
        T=geo.e_balkon,
        hw_yz=geo.h_abschluss,
        a=geo.b_auflager_rand,
        hw_xz=geo.h_abschluss,
        we_side_pressure=ergebnisse.we_side_pressure,
        we_side_suction=ergebnisse.we_side_suction,
        we_front_suction=ergebnisse.we_front_suction,
        gamma_Q=ergebnisse.gamma_Q_reaktionen,
    )


def derive_connection_actions_from_snapshot(
    wind_input: Mapping[str, Any] | None,
    wind_results: Mapping[str, Any] | None,
) -> ConnectionActions:
    """Rekonstruiert Anschlussgrößen aus gespeichertem Projekt-/Session-State."""
    wind_input = wind_input or {}
    wind_results = wind_results or {}

    if _has_existing_actions(wind_results):
        return ConnectionActions.from_mapping(
            {
                **wind_results,
                "trace": ["Aus gespeichertem Wind-Snapshot übernommen."],
            }
        )

    try:
        geo = Geometrie(
            h=float(wind_input["h_gebaeude"]),
            d=float(wind_input["d_gebaeude"]),
            b=float(wind_input["b_gebaeude"]),
            z_balkon=float(wind_input["z_balkon"]),
            e_balkon=float(wind_input.get("e_balkon", wind_input.get("balkon_tiefe", 0.0))),
            h_abschluss=float(wind_input.get("h_abschl", wind_input.get("hoehe_gelaender_abschattung", 0.0))),
            s_verankerung=float(wind_input.get("s_verank", wind_input.get("balkon_breite", 0.0))),
            b_auflager_rand=float(wind_input.get("b_auflager_rand", wind_input.get("verankerung_randabstand", 0.0))),
        )
    except KeyError as exc:
        raise ValueError(f"Wind-Input unvollständig; fehlender Schlüssel: {exc.args[0]}") from exc

    try:
        we_side_pressure = float(wind_results["we_side_pressure"])
        we_side_suction = float(wind_results["we_side_suction"])
        we_front_suction = float(wind_results["we_front_suction"])
    except KeyError as exc:
        raise ValueError(f"Wind-Ergebnis unvollständig; fehlender Schlüssel: {exc.args[0]}") from exc

    gamma_q = float(wind_results.get("gamma_Q_reaktionen", 1.5))
    actions = derive_connection_actions_simple(
        B=geo.s_verankerung,
        T=geo.e_balkon,
        hw_yz=geo.h_abschluss,
        a=geo.b_auflager_rand,
        hw_xz=geo.h_abschluss,
        we_side_pressure=we_side_pressure,
        we_side_suction=we_side_suction,
        we_front_suction=we_front_suction,
        gamma_Q=gamma_q,
    )
    actions.trace.insert(0, "Aus Wind-Input und Wind-Ergebnis-Snapshot rekonstruiert.")
    return actions
