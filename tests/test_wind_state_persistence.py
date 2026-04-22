from __future__ import annotations

from spittelmeister_windlast.ui.windlast_page import _build_wind_input_snapshot, _merge_live_wind_state


def test_build_wind_input_snapshot_contains_balkon_und_gebaeude_aliases() -> None:
    snapshot = _build_wind_input_snapshot(
        adresse="Testweg 1, Pforzheim",
        h_gebaeude=18.5,
        d_gebaeude=12.0,
        b_gebaeude=24.0,
        z_balkon=14.2,
        e_balkon=1.65,
        h_abschl=3.20,
        s_verank=5.10,
        b_auflager_rand=0.35,
        standort_bez="Pforzheim",
        hoehe_uNN=265.0,
        windzone=2,
        gelaende="binnen",
    )

    assert snapshot["h_gebaeude"] == 18.5
    assert snapshot["d_gebaeude"] == 12.0
    assert snapshot["b_gebaeude"] == 24.0
    assert snapshot["balkon_breite"] == 5.10
    assert snapshot["balkon_tiefe"] == 1.65
    assert snapshot["verankerung_randabstand"] == 0.35
    assert snapshot["hoehe_gelaender_abschattung"] == 3.20


def test_merge_live_wind_state_preserves_existing_results_snapshot() -> None:
    previous_state = {
        "input": {"h_gebaeude": 10.0},
        "results_snapshot": {"qp": 0.93, "Hk": 4.1},
    }
    current_input = {
        "h_gebaeude": 19.0,
        "balkon_breite": 4.9,
        "balkon_tiefe": 1.4,
    }

    merged = _merge_live_wind_state(previous_state, current_input)

    assert merged["input"] == current_input
    assert merged["results_snapshot"] == previous_state["results_snapshot"]
