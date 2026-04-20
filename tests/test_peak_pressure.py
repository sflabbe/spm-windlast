"""Smoke-Tests fuer qp(z) — Wertegleichheit mit der urspruenglichen Implementation."""

from __future__ import annotations

import math

import pytest

from spittelmeister_windlast.core.peak_pressure import (
    berechne_qp,
    berechne_qp_ausfuehrlich,
    get_hoehenstufe,
)


class TestBinnen:
    def test_bis_7m_konstant(self):
        r = berechne_qp(5.0, windzone=1, gelaende="binnen")
        # qb0=0.32 -> qp = 1.5 * 0.32 = 0.48
        assert r.qp == pytest.approx(0.48, abs=1e-6)
        assert r.faktor == 1.5
        assert r.normstelle == "NA.B.1"

    def test_bis_50m(self):
        r = berechne_qp(25.0, windzone=2, gelaende="binnen")
        # qb0=0.39 -> faktor = 1.7 * (25/10)^0.37
        expected = 1.7 * (25.0 / 10.0) ** 0.37 * 0.39
        assert r.qp == pytest.approx(expected, abs=1e-6)
        assert r.normstelle == "NA.B.2"

    def test_ueber_50m(self):
        r = berechne_qp(80.0, windzone=1, gelaende="binnen")
        expected = 2.1 * (80.0 / 10.0) ** 0.24 * 0.32
        assert r.qp == pytest.approx(expected, abs=1e-6)
        assert r.normstelle == "NA.B.3"


class TestKueste:
    def test_bis_4m(self):
        r = berechne_qp(3.0, windzone=4, gelaende="kueste")
        assert r.qp == pytest.approx(1.8 * 0.56, abs=1e-6)

    def test_ueber_4m(self):
        r = berechne_qp(20.0, windzone=4, gelaende="kueste")
        expected = 2.3 * (20.0 / 10.0) ** 0.27 * 0.56
        assert r.qp == pytest.approx(expected, abs=1e-6)


class TestNordsee:
    def test_bis_2m_konstant(self):
        r = berechne_qp(1.5, windzone=4, gelaende="nordsee")
        assert r.qp == pytest.approx(1.1, abs=1e-6)

    def test_ueber_2m(self):
        r = berechne_qp(10.0, windzone=4, gelaende="nordsee")
        expected = 1.05 * (10.0 / 10.0) ** 0.19
        assert r.qp == pytest.approx(expected, abs=1e-6)


class TestFehlerfaelle:
    def test_hoehe_ueber_300m(self):
        with pytest.raises(ValueError, match="> 300"):
            berechne_qp(301.0, windzone=1, gelaende="binnen")

    def test_ungueltige_windzone(self):
        with pytest.raises(ValueError, match="Windzone"):
            berechne_qp(10.0, windzone=5, gelaende="binnen")

    def test_ungueltige_gelaendekategorie(self):
        with pytest.raises(ValueError, match="Gelaendekategorie"):
            berechne_qp(10.0, windzone=1, gelaende="wuestenstadt")  # type: ignore[arg-type]


class TestLegacyAlias:
    def test_berechne_qp_ausfuehrlich_gibt_dict(self):
        r = berechne_qp_ausfuehrlich(15.0, 1, "binnen")
        assert isinstance(r, dict)
        assert "qp" in r and "qb0" in r and "formel" in r
        # Wert identisch mit neuer API
        r2 = berechne_qp(15.0, 1, "binnen")
        assert r["qp"] == pytest.approx(r2.qp, abs=1e-12)


class TestHoehenstufe:
    @pytest.mark.parametrize(
        "h, expected",
        [(8.0, 0), (10.0, 0), (15.0, 1), (18.0, 1), (22.0, 2), (25.0, 2), (30.0, None)],
    )
    def test_hoehenstufe(self, h, expected):
        assert get_hoehenstufe(h) == expected
