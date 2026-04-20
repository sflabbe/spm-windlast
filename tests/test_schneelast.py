"""Tests fuer den Schneelastzone-Lookup."""

from __future__ import annotations

import pytest

from spittelmeister_windlast.geo.schneelast import (
    get_schneelastzone,
    get_schneelastzone_detail,
)


class TestSchneelastLookup:
    def test_kreis_direkt(self):
        # Nordfriesland ist im amtlichen Tabellenwerk SLZ 2
        slz, quelle = get_schneelastzone("Nordfriesland", "Schleswig-Holstein")
        assert slz == "2"
        assert "Nordfriesland" in quelle or "nordfriesland" in quelle.lower()

    def test_default_bei_unbekannt(self):
        slz, quelle = get_schneelastzone("", "Olympus Mons")
        assert slz == "2"
        assert "Standardwert" in quelle

    def test_muenchen_ohne_typ_ist_landkreis(self):
        """Ohne expliziten Typ wird der Landkreis bevorzugt (konservativ)."""
        slz, _ = get_schneelastzone("München")
        assert slz == "2"

    def test_muenchen_stadt_ist_1a(self):
        """Stadt Muenchen explizit abgefragt -> SLZ 1a."""
        slz, quelle = get_schneelastzone("München", kreis_typ="stadt")
        assert slz == "1a"
        assert "muenchen stadt" in quelle

    def test_muenchen_landkreis_ist_2(self):
        slz, _ = get_schneelastzone("München", kreis_typ="landkreis")
        assert slz == "2"

    def test_kreis_umlaut_tolerant(self):
        """Umlaut-Toleranz via norm_kreis."""
        a, _ = get_schneelastzone("München")
        b, _ = get_schneelastzone("Muenchen")
        assert a == b


class TestSchneelastDetail:
    def test_detail_enthaelt_varianten(self):
        d = get_schneelastzone_detail("München")
        assert d is not None
        assert "varianten" in d
        assert "slz_dominant" in d
        assert "bundesland" in d

    def test_detail_unbekannt(self):
        # String, der keinen Teilstring-Match erzeugt (kurz + ungewoehnlich)
        assert get_schneelastzone_detail("XYZ-999") is None


class TestDatenIntegritaetSchnee:
    def test_alle_bundeslaender_vertreten(self):
        from spittelmeister_windlast.daten import schneelastzone_kreis_detail
        detail = schneelastzone_kreis_detail()["kreise"]
        bls = set()
        for v in detail.values():
            bl = v["bundesland"]
            if isinstance(bl, list):
                bls.update(bl)
            else:
                bls.add(bl)
        assert len(bls) == 16, f"Fehlende Bundeslaender: {set(['SH','HH','NI','HB','NW','HE','RP','BW','BY','SL','BE','BB','MV','SN','ST','TH']) - bls}"

    def test_nur_gueltige_zonen(self):
        from spittelmeister_windlast.daten import schneelastzone_kreis
        gueltig = {"1", "1a", "2", "2a", "3", "3a"}
        for kreis, slz in schneelastzone_kreis().items():
            assert slz in gueltig, f"Ungueltige SLZ {slz!r} fuer {kreis!r}"

    @pytest.mark.parametrize("kreis,kreis_typ,expected", [
        ("Nordfriesland", None, "2"),
        ("Dithmarschen", None, "2"),
        ("München", "stadt", "1a"),
        ("München", "landkreis", "2"),
        ("München", None, "2"),   # default = Landkreis
        ("Berlin", None, "2"),
        ("Hamburg", None, "2"),
    ])
    def test_bekannte_werte(self, kreis, kreis_typ, expected):
        slz, _ = get_schneelastzone(kreis, kreis_typ=kreis_typ)
        assert slz == expected


class TestAreaCodeSchnee:
    def test_muenchen_stadt_mit_ags(self):
        slz, quelle = get_schneelastzone("München", area_code="09162000")
        assert slz == "1a"
        assert "area_code 09162000" in quelle

    def test_muenchen_landkreis_mit_ags(self):
        slz, quelle = get_schneelastzone("München", area_code="09184112")
        assert slz == "2"
        assert "area_code 09184112" in quelle

    def test_detail_muenchen_stadt_mit_ags(self):
        d = get_schneelastzone_detail("München", area_code="09162000")
        assert d is not None
        assert d["name"] == "München (Stadt)"


class TestAreaCodeSchneeFiveDigit:
    def test_muenchen_stadt_mit_5_stelligem_kreisschluessel(self):
        slz, quelle = get_schneelastzone("", area_code="09162")
        assert slz == "1a"
        assert "09162" in quelle

    def test_muenchen_landkreis_mit_5_stelligem_kreisschluessel(self):
        slz, quelle = get_schneelastzone("", area_code="09184")
        assert slz == "2"
        assert "09184" in quelle

    def test_karlsruhe_stadt_vs_landkreis_mit_5_stelligem_kreisschluessel(self):
        city, _ = get_schneelastzone("", area_code="08212")
        county, _ = get_schneelastzone("", area_code="08215")
        assert city == "1"
        assert county == "2"
