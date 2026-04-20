#!/usr/bin/env python3
"""Beispiel: Nutzung des Kerns aus einem anderen Python-Programm.

Dieses Skript zeigt, wie z. B. `balkonsystem` die Windlast-Berechnung
aufruft, ohne eine UI- oder Netzwerk-Abhaengigkeit zu erben.

Aufruf:
    python scripts/example_headless.py
"""

from __future__ import annotations

from spittelmeister_windlast import (
    Geometrie,
    Projekt,
    Standort,
    WindlastBerechnung,
)


def berechne_balkon(
    projekt_nr: str,
    bearbeiter: str,
    standort_name: str,
    windzone: int,
    gelaende: str,
    hoehe_uNN: float,
    **geometrie_kwargs: float,
) -> dict:
    """Thin-wrapper, den balkonsystem direkt nutzen kann.

    Gibt die massgebenden Schnittgroessen als dict zurueck — verzichtet
    auf LaTeX/PDF, um keine Systemabhaengigkeit zu benoetigen.
    """
    wb = WindlastBerechnung(
        Projekt(bezeichnung=f"Balkon {projekt_nr}", nummer=projekt_nr, bearbeiter=bearbeiter),
        Standort(standort_name, windzone, gelaende, hoehe_uNN),
        Geometrie(**geometrie_kwargs),
    )
    e = wb.berechnen()
    return {
        "qp_kN_m2": e.qp,
        "qhk_kN_m": e.qhk,
        "Hk_kN": e.Hk,
        "Mk_kNm": e.Mk,
        "wk_kN_m2": e.wk_massgebend,
        "lastfall": e.lastfall_massgebend,
        "zone": e.zone_massgebend,
    }


def main() -> None:
    # Realistisches Beispiel aus einem Pforzheim-Projekt
    ergebnisse = berechne_balkon(
        projekt_nr="2026-WB-017",
        bearbeiter="S. Montero",
        standort_name="Pforzheim",
        windzone=1,
        gelaende="binnen",
        hoehe_uNN=280.0,
        h=18.5, d=15.0, b=22.0,
        z_balkon=16.2, e_balkon=1.4,
        h_abschluss=2.8, s_verankerung=4.5,
    )

    print("Windlast-Ergebnisse (Balkon):")
    for k, v in ergebnisse.items():
        if isinstance(v, float):
            print(f"  {k:<14} = {v:>8.3f}")
        else:
            print(f"  {k:<14} = {v}")


if __name__ == "__main__":
    main()
