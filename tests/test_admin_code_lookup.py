from __future__ import annotations

from spittelmeister_windlast.daten import admin_kreise_codes
from spittelmeister_windlast.geo._admin_code import area_code_info, state_code_from_name


def test_destatis_kreis_codes_loaded():
    data = admin_kreise_codes()
    assert data["metadata"]["n_codes"] >= 399
    assert "09162" in data["codes"]
    assert data["codes"]["09184"]["type"] == "landkreis"


def test_area_code_info_for_8_digit_ags_city():
    info = area_code_info("09162000")
    assert info.kind == "gemeinde_8"
    assert info.kreis_code == "09162"
    assert info.kreis_typ_hint == "stadt"
    assert info.kreis_basis_norm == "muenchen"
    assert info.bundesland_code == "BY"


def test_area_code_info_for_5_digit_kreis_code_landkreis():
    info = area_code_info("09184")
    assert info.kind == "kreis_5"
    assert info.kreis_code == "09184"
    assert info.kreis_typ_hint == "landkreis"
    assert info.kreis_basis_norm == "muenchen"


def test_area_code_info_for_karlsruhe_city_and_county():
    city = area_code_info("08212")
    county = area_code_info("08215")
    assert city.kreis_typ_hint == "stadt"
    assert county.kreis_typ_hint == "landkreis"
    assert city.kreis_basis_norm == county.kreis_basis_norm == "karlsruhe"


def test_state_code_from_name_accepts_full_names():
    assert state_code_from_name("Baden-Wuerttemberg") == "BW"
    assert state_code_from_name("Nordrhein-Westfalen") == "NW"
