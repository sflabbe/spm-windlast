from __future__ import annotations

import pytest

from spittelmeister_windlast import Geometrie, Projekt, Standort, WindlastBerechnung
from spittelmeister_windlast.core.berechnung import _berechne_reaktionen_vereinfacht


def test_reaktionsgroessen_unit_mit_vorgegebenen_aussendruecken():
    werte = _berechne_reaktionen_vereinfacht(
        B=3.94,
        T=1.94,
        b=0.3,
        hw_yz=1.1,
        hw_xz=1.1,
        we_side_pressure=0.760,
        we_side_suction=-0.369,
        we_front_suction=-1.227,
    )

    assert werte["q_seite_1"] == pytest.approx(0.836, abs=1e-3)
    assert werte["q_seite_2"] == pytest.approx(0.406, abs=1e-3)
    assert werte["q_vorne"] == pytest.approx(1.350, abs=1e-3)
    assert werte["s"] == pytest.approx(3.34, abs=1e-3)
    assert werte["Hx_k"] == pytest.approx(2.41, abs=0.01)
    assert werte["M_A_k"] == pytest.approx(11.22, abs=0.02)
    assert werte["Hy_2_k"] == pytest.approx(3.36, abs=0.02)
    assert werte["Hy_1_k"] == pytest.approx(1.96, abs=0.02)
    assert werte["Hx_Ed"] == pytest.approx(3.61, abs=0.02)
    assert werte["Hy_2_Ed"] == pytest.approx(5.04, abs=0.02)
    assert werte["Hy_1_Ed"] == pytest.approx(2.94, abs=0.02)


def test_reaktionsgroessen_integration_aus_windlast_berechnung():
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

    assert e.q_seite_1 == pytest.approx(abs(e.we_side_pressure) * 1.1, abs=1e-12)
    assert e.q_seite_2 == pytest.approx(abs(e.we_side_suction) * 1.1, abs=1e-12)
    assert e.q_vorne == pytest.approx(abs(e.we_front_suction) * 1.1, abs=1e-12)
    assert e.Hx_k == pytest.approx(1.94 * (e.q_seite_1 + e.q_seite_2), abs=1e-12)
    assert e.s == pytest.approx(3.94 - 2 * 0.3, abs=1e-12)
    assert e.auflagerabstand == pytest.approx(e.s, abs=1e-12)
    assert e.Hy_2_k == pytest.approx(e.M_A_k / e.s, abs=1e-12)
    assert e.Hy_1_k == pytest.approx(e.q_vorne * 3.94 - e.Hy_2_k, abs=1e-12)
    assert e.Hx_Ed == pytest.approx(1.5 * e.Hx_k, abs=1e-12)
    assert e.Hy_1_Ed == pytest.approx(1.5 * e.Hy_1_k, abs=1e-12)
    assert e.Hy_2_Ed == pytest.approx(1.5 * e.Hy_2_k, abs=1e-12)


def test_reaktions_validierung_auflagerabstand():
    wb = WindlastBerechnung(
        Projekt("Beispiel", "R-002", "Test"),
        Standort("Demo", windzone=1, gelaende="binnen", hoehe_uNN=0.0),
        Geometrie(
            h=15.13,
            d=12.55,
            b=20.0,
            z_balkon=12.83,
            e_balkon=1.94,
            h_abschluss=1.1,
            s_verankerung=3.94,
            b_auflager_rand=1.97,
        ),
    )

    with pytest.raises(ValueError, match=r"B - 2\*a muss > 0"):
        wb.berechnen()


def test_beispielfall_schliesst_numerisch_im_gleichgewicht():
    """Beispielfall fuer Plausibilitaet: Kraefte- und Momentengleichgewicht."""
    werte = _berechne_reaktionen_vereinfacht(
        B=3.94,
        T=1.94,
        b=0.3,
        hw_yz=1.1,
        hw_xz=1.1,
        we_side_pressure=0.760,
        we_side_suction=-0.369,
        we_front_suction=-1.227,
    )

    assert (werte["Hy_1_k"] + werte["Hy_2_k"]) == pytest.approx(werte["q_vorne"] * 3.94, abs=1e-12)
    assert werte["M_A_k"] == pytest.approx(werte["Hy_2_k"] * werte["s"], abs=1e-12)
