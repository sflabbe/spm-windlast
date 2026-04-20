from __future__ import annotations

from spittelmeister_windlast.daten import erdbebenzonen_dataset
from spittelmeister_windlast.geo.erdbeben import (
    get_erdbeben_coverage,
    get_erdbeben_records,
)


def test_erdbebenzonen_dataset_loaded():
    data = erdbebenzonen_dataset()
    assert data["metadata"]["n_records"] >= 7000
    assert "BW" in data["coverage"]
    assert data["coverage"]["BW"]["mode"] == "external_map_only"


def test_bw_is_explicitly_covered_as_external_map_only():
    cov = get_erdbeben_coverage(state="Baden-Wuerttemberg")
    assert cov is not None
    assert cov["mode"] == "external_map_only"
    assert "Karte der Erdbebenzonen" in cov["note"]


def test_bw_area_code_returns_external_map_required():
    result = get_erdbeben_records(area_code="08212000")
    assert result["status"] == "external_map_required"
    assert result["state_code"] == "BW"
    assert result["coverage"]["mode"] == "external_map_only"


def test_hessen_exact_area_code_lookup():
    result = get_erdbeben_records(area_code="06433004")
    assert result["status"] == "ok"
    assert result["state_code"] == "HE"
    assert 1 in result["zone_values"]
    assert "S" in result["ground_classes"]
    assert any(m["municipality_name"] == "Gernsheim" for m in result["matches"])


def test_muenchen_bayern_kreis_row_is_present_via_county_lookup():
    result = get_erdbeben_records(state="Bayern", county="München")
    assert result["status"] == "ok"
    assert any(m["county_name"] == "München" for m in result["matches"])
