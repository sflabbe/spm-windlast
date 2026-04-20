"""Paritaets-Test: neue Architektur vs. alter flacher Code.

Dieses Fixture haelt eine Kopie des urspruenglichen ``windlast_generator.py``
vor und vergleicht fuer eine Reihe von Eingangsgroessen die Ergebnisse
numerisch. Der Test garantiert, dass die Reorganisation keine Zahl veraendert
hat.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from spittelmeister_windlast import (
    Geometrie,
    Projekt,
    Standort,
    WindlastBerechnung,
)

LEGACY_DIR = Path(__file__).parent / "_legacy"


@pytest.fixture(scope="module")
def legacy_module():
    """Importiert das alte flache windlast_generator-Modul als Vergleich."""
    if not LEGACY_DIR.exists():
        pytest.skip("Legacy-Referenz nicht installiert — tests/_legacy/ fehlt.")
    sys.path.insert(0, str(LEGACY_DIR))
    try:
        import windlast_generator as legacy  # type: ignore[import-not-found]
        return legacy
    finally:
        sys.path.remove(str(LEGACY_DIR))


# Drei repraesentative Testfaelle, die die drei Hoehenbereiche + drei
# cpe-Interpolationszweige + zwei Gelaendekategorien abdecken.
CASES = [
    pytest.param(
        # h <= 7m, Binnen, h/d>1 (cpe,D klemmt), WZ 1
        Projekt("Demo1", "T-001", "Test"),
        Standort("Pforzheim", 1, "binnen", 280.0),
        Geometrie(h=6.5, d=4.0, b=8.0, z_balkon=6.0,
                  e_balkon=1.4, h_abschluss=2.0, s_verankerung=5.0),
        id="klein-binnen",
    ),
    pytest.param(
        # 7<h<50m, Binnen, h/d<1 (cpe D interpoliert), WZ 1
        Projekt("Demo2", "T-002", "Test"),
        Standort("Wuerzburg", 1, "binnen", 192.0),
        Geometrie(h=15.13, d=42.5, b=42.5, z_balkon=12.83,
                  e_balkon=1.425, h_abschluss=3.00, s_verankerung=4.93),
        id="wuerzburg-original",
    ),
    pytest.param(
        # h>4m Kueste, WZ 4, h/d>5 (cpe A klemmt)
        Projekt("Demo3", "T-003", "Test"),
        Standort("Sylt", 4, "kueste", 5.0),
        Geometrie(h=20.0, d=3.0, b=4.0, z_balkon=18.0,
                  e_balkon=1.5, h_abschluss=2.5, s_verankerung=4.0),
        id="gross-kueste",
    ),
]


@pytest.mark.parametrize("projekt,standort,geo", CASES)
def test_parity_with_legacy(legacy_module, projekt, standort, geo):
    """Jeder numerische Ergebniswert muss bit-genau identisch sein."""
    # Neue API
    wb_neu = WindlastBerechnung(projekt, standort, geo)
    e_neu = wb_neu.berechnen()

    # Legacy-API
    leg_projekt = legacy_module.Projekt(projekt.bezeichnung, projekt.nummer, projekt.bearbeiter)
    leg_standort = legacy_module.Standort(
        standort.bezeichnung, standort.windzone, standort.gelaende, standort.hoehe_uNN
    )
    leg_geo = legacy_module.Geometrie(
        geo.h, geo.d, geo.b, geo.z_balkon, geo.e_balkon, geo.h_abschluss, geo.s_verankerung
    )
    wb_alt = legacy_module.WindlastBerechnung(leg_projekt, leg_standort, leg_geo)
    e_alt = wb_alt.berechnen()

    # Numerische Felder bit-genau vergleichen
    numeric_fields = [
        "qb0", "qp", "qp_faktor",
        "cscd", "h_d", "A_ref", "A_w_side", "A_w_front",
        "cpe10_D", "cpe10_E", "cpe10_A",
        "we_side_pressure", "we_side_suction", "we_front_suction",
        "q_side_pressure", "q_side_suction", "q_front_suction",
        "wk_sog", "wk_druck", "wk_massgebend",
        "qhk", "Hk", "Mk",
    ]
    for field in numeric_fields:
        v_neu = getattr(e_neu, field)
        v_alt = getattr(e_alt, field)
        assert v_neu == pytest.approx(v_alt, abs=1e-12, rel=1e-12), (
            f"Paritaetsbruch im Feld '{field}': neu={v_neu}, alt={v_alt}"
        )

    # Kategorische Felder
    assert e_neu.lastfall_massgebend == e_alt.lastfall_massgebend
    assert e_neu.zone_massgebend == e_alt.zone_massgebend
    assert e_neu.qp_normstelle == e_alt.qp_normstelle
