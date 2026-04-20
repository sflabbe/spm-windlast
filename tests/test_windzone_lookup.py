"""Tests fuer die Windzone-Lookup-Hierarchie."""

from __future__ import annotations

import pytest

from spittelmeister_windlast.geo._normalize import norm_kreis
from spittelmeister_windlast.geo.windzone import get_windzone


class TestNormalisierung:
    @pytest.mark.parametrize("input_str, expected", [
        ("Landkreis Wuerzburg", "wuerzburg"),
        ("Landkreis Würzburg", "wuerzburg"),
        ("Kreis Rhön-Grabfeld", "rhoen grabfeld"),
        ("Stadt München", "muenchen"),
        ("Main-Tauber-Kreis, Bayern", "main tauber"),  # Komma schneidet ab
    ])
    def test_norm_kreis(self, input_str, expected):
        assert norm_kreis(input_str) == expected


class TestHierarchy:
    """Lookup-Reihenfolge: PLZ -> Praefix -> Kreis -> Bundesland -> Default."""

    def test_plz_volltreffer_hat_prioritaet(self):
        # Sylt, Westerland -> 25980 ist in der PLZ-Tabelle als WZ 4
        wz, quelle = get_windzone("Nordfriesland", "Schleswig-Holstein", "25980")
        assert wz == 4
        assert "PLZ 25980" in quelle

    def test_kreis_direkt(self):
        # Ohne PLZ faellt auf Kreis-Lookup zurueck
        wz, quelle = get_windzone("Pforzheim", "Baden-Wuerttemberg", "")
        assert wz == 1
        assert "Pforzheim" in quelle or "pforzheim" in quelle.lower()

    def test_bundesland_fallback(self):
        # Kreis nicht in Tabelle, aber Bundesland bekannt
        wz, quelle = get_windzone("UnbekannterKreis", "Hamburg", "")
        # Hamburg ist in WINDZONE_BY_BUNDESLAND
        assert isinstance(wz, int)
        assert wz >= 1

    def test_default_bei_unbekannt(self):
        # County leer + unbekanntes Bundesland -> Default WZ 2.
        # (Nicht-leerer County kann ueber den Teilstring-Match falsch-positive
        # Treffer erzeugen, siehe test_teilstring_match_ist_aggressiv.)
        wz, quelle = get_windzone("", "Olympus Mons", "")
        assert wz == 2
        assert "Standardwert" in quelle

    def test_teilstring_match_ist_aggressiv(self):
        """Dokumentiert bekanntes Verhalten des legacy Teilstring-Lookups:

        Der originale Lookup aus geo_standort.py nutzt ``k in key or key in k``,
        was zu falsch-positiven Treffern fuehren kann, wenn der eingegebene
        County-Name nach Normalisierung einen kurzen Teilstring enthaelt, der
        in einem Kreisnamen vorkommt.

        Beispiel: "Marsstadt" -> normalisiert zu "mars" (Suffix 'stadt' entfernt)
        -> matcht "dithmarschen" (enthaelt 'mars').

        TODO: Sollte zu word-boundary- oder exact-match umgestellt werden.
        """
        wz, quelle = get_windzone("Marsstadt", "Olympus Mons", "")
        assert wz == 3  # Match auf 'dithmarschen'
        assert "Teiluebereinstimmung" in quelle

    def test_pforzheim_ist_wz1(self):
        # Sanity-Check fuer den Heimatort der Firma
        wz, _ = get_windzone("Pforzheim", "Baden-Wuerttemberg", "75175")
        assert wz == 1

    def test_karlsruhe_ist_wz1(self):
        wz, _ = get_windzone("Karlsruhe", "Baden-Wuerttemberg", "76131")
        assert wz == 1


class TestDatenIntegritaet:
    """Smoke-Tests fuer die JSON-Tabellen."""

    def test_tabellen_werden_geladen(self):
        from spittelmeister_windlast.daten import (
            qb0_table,
            windzone_bundesland,
            windzone_kreis,
            windzone_plz,
            windzone_plz_prefix,
        )
        assert qb0_table() == {1: 0.32, 2: 0.39, 3: 0.47, 4: 0.56}
        assert len(windzone_kreis()) > 300
        assert len(windzone_plz()) > 400
        assert len(windzone_plz_prefix()) > 40
        assert len(windzone_bundesland()) == 16

    def test_tabellen_cached(self):
        """Loader ist lru_cache-annotiert -> identische Referenz bei mehreren Aufrufen."""
        from spittelmeister_windlast.daten import windzone_kreis
        a = windzone_kreis()
        b = windzone_kreis()
        assert a is b
