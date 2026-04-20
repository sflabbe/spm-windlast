"""Tests fuer cpe,10 Interpolation nach Excel-Vorlage 27.02.2026."""

from __future__ import annotations

import pytest

from spittelmeister_windlast.core.druckbeiwerte import (
    cpe10,
    interpolate_cpe_excel,
    interpolate_linear,
)


class TestBereichD:
    def test_unten_klemmt_nicht(self):
        # h/d = 0.25 -> cpe,10 = 0.7
        assert cpe10("D", 0.25) == pytest.approx(0.7, abs=1e-9)

    def test_zwischenpunkt(self):
        # h/d = 0.5 -> linear zwischen (0.25, 0.7) und (1.0, 0.8)
        expected = 0.7 + (0.5 - 0.25) / (1.0 - 0.25) * (0.8 - 0.7)
        assert cpe10("D", 0.5) == pytest.approx(expected, abs=1e-9)

    def test_h_d_exakt_1(self):
        assert cpe10("D", 1.0) == pytest.approx(0.8, abs=1e-9)

    def test_ueber_1_klemmt(self):
        assert cpe10("D", 3.0) == 0.8
        assert cpe10("D", 10.0) == 0.8


class TestBereichE:
    def test_h_d_unter_1_interpoliert(self):
        assert cpe10("E", 0.25) == pytest.approx(-0.3, abs=1e-9)
        assert cpe10("E", 1.0) == pytest.approx(-0.5, abs=1e-9)

    def test_h_d_ueber_1_klemmt(self):
        assert cpe10("E", 5.0) == -0.5


class TestBereichA:
    def test_h_d_1(self):
        assert cpe10("A", 1.0) == pytest.approx(-1.2, abs=1e-9)

    def test_h_d_5(self):
        assert cpe10("A", 5.0) == pytest.approx(-1.4, abs=1e-9)

    def test_h_d_ueber_5_klemmt(self):
        assert cpe10("A", 10.0) == -1.4

    def test_h_d_zwischen_1_und_5(self):
        # Linear zwischen (1, -1.2) und (5, -1.4)
        expected = -1.2 + (3.0 - 1.0) / (5.0 - 1.0) * (-1.4 - -1.2)
        assert cpe10("A", 3.0) == pytest.approx(expected, abs=1e-9)


class TestFehlerfaelle:
    def test_unbekannter_bereich(self):
        with pytest.raises(ValueError, match="Bereich"):
            cpe10("Z", 1.0)  # type: ignore[arg-type]

    def test_identische_stuetzstellen(self):
        with pytest.raises(ValueError, match="identische"):
            interpolate_linear(0.5, 1.0, 0.0, 1.0, 1.0)


class TestLegacyAlias:
    def test_interpolate_cpe_excel_funktioniert(self):
        assert interpolate_cpe_excel("D", 0.5) == pytest.approx(cpe10("D", 0.5))
        assert interpolate_cpe_excel("A", 3.0) == pytest.approx(cpe10("A", 3.0))
