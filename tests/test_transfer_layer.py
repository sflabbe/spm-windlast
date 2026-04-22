from __future__ import annotations

import pytest

from spittelmeister_windlast import Geometrie, Projekt, Standort, WindlastBerechnung
from spittelmeister_windlast.transfer import (
    ConnectionActions,
    derive_connection_actions_from_snapshot,
    derive_connection_actions_from_wind,
    derive_connection_actions_simple,
)


def test_transfer_simple_matches_known_example():
    actions = derive_connection_actions_simple(
        B=3.94,
        T=1.94,
        b=0.3,
        hw_yz=1.1,
        hw_xz=1.1,
        we_side_pressure=0.760,
        we_side_suction=-0.369,
        we_front_suction=-1.227,
    )

    assert actions.q_seite_1 == pytest.approx(0.836, abs=1e-3)
    assert actions.q_seite_2 == pytest.approx(0.406, abs=1e-3)
    assert actions.q_vorne == pytest.approx(1.350, abs=1e-3)
    assert actions.Hx_k == pytest.approx(2.41, abs=0.01)
    assert actions.Hx_Ed == pytest.approx(3.61, abs=0.02)
    assert actions.Hy_2_Ed == pytest.approx(5.04, abs=0.02)


def test_transfer_from_wind_uses_existing_result_values():
    wb = WindlastBerechnung(
        Projekt("Beispiel", "R-001", "Test"),
        Standort("Demo", windzone=1, gelaende="binnen", hoehe_uNN=0.0),
        Geometrie(
            h=15.13,
            d=12.55,
            b=20.0,
            z_balkon=12.83,
            e_balkon=1.94,
            h_abschluss=1.1,
            s_verankerung=3.94,
            b_auflager_rand=0.3,
        ),
    )
    e = wb.berechnen()
    actions = derive_connection_actions_from_wind(wb.geo, e)

    assert actions.Hx_k == pytest.approx(e.Hx_k)
    assert actions.Hy_1_k == pytest.approx(e.Hy_1_k)
    assert actions.Hy_2_k == pytest.approx(e.Hy_2_k)
    assert actions.note == e.reaktionsmodell_hinweis


def test_transfer_from_snapshot_reconstructs_actions():
    wind_input = {
        "h_gebaeude": 15.13,
        "d_gebaeude": 12.55,
        "b_gebaeude": 20.0,
        "z_balkon": 12.83,
        "e_balkon": 1.94,
        "h_abschl": 1.1,
        "s_verank": 3.94,
        "b_auflager_rand": 0.3,
    }
    wind_results = {
        "we_side_pressure": 0.760,
        "we_side_suction": -0.369,
        "we_front_suction": -1.227,
        "gamma_Q_reaktionen": 1.5,
    }
    actions = derive_connection_actions_from_snapshot(wind_input, wind_results)

    assert actions.Hx_Ed == pytest.approx(3.61, abs=0.02)
    assert actions.Hy_1_Ed == pytest.approx(2.94, abs=0.02)
    assert actions.trace[0].startswith("Aus Wind-Input")


def test_connection_actions_from_mapping_is_robust():
    actions = ConnectionActions.from_mapping({"Hx_Ed": "3.5", "Hy_1_Ed": 2, "note": "ok"})
    assert actions.Hx_Ed == pytest.approx(3.5)
    assert actions.Hy_1_Ed == pytest.approx(2.0)
    assert actions.note == "ok"
