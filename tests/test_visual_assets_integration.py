"""Smoke-Tests fuer visuelle Asset-Integration (Streamlit + LaTeX)."""

from __future__ import annotations

from pathlib import Path

from spittelmeister_windlast import Geometrie, Projekt, Standort, WindlastBerechnung
from spittelmeister_windlast.report.latex import render_latex
from spittelmeister_windlast.utils.assets import copy_assets, get_asset_path


REQUIRED_SVG = [
    "building_geometry_zoning.svg",
    "building_geometry_cases.svg",
    "balcony_system.svg",
    "load_scheme.svg",
    "reaction_scheme.svg",
]

REQUIRED_TEX = [
    "building_geometry_zoning.tex",
    "building_geometry_cases.tex",
    "balcony_system.tex",
    "load_scheme.tex",
    "reaction_scheme.tex",
]


def _sample_wb() -> WindlastBerechnung:
    wb = WindlastBerechnung(
        Projekt("Demo", "VIS-001", "Test"),
        Standort("Wuerzburg", 1, "binnen", 192.0),
        Geometrie(15.13, 12.55, 20.0, 12.83, 1.425, 3.0, 4.93, 0.3),
    )
    wb.berechnen()
    return wb


def test_all_visual_assets_exist():
    """Alle benoetigten Dateien sind in assets/ vorhanden."""
    for filename in [*REQUIRED_SVG, *REQUIRED_TEX]:
        path = get_asset_path(filename)
        assert path.exists(), filename
        assert path.stat().st_size > 0, filename


def test_copy_assets_for_latex(tmp_path: Path):
    """Assets werden in den Temp-Ordner fuer pdflatex kopiert."""
    copied_root = copy_assets(tmp_path, REQUIRED_TEX)
    assert copied_root == tmp_path / "assets"

    for filename in REQUIRED_TEX:
        copied = copied_root / filename
        assert copied.exists(), filename
        assert copied.stat().st_size > 0, filename


def test_render_latex_references_visual_subsections():
    """Der LaTeX-Report enthaelt die neuen Diagramm-Unterabschnitte."""
    wb = _sample_wb()
    src = render_latex(wb.projekt, wb.standort, wb.geo, wb.erg)

    assert "Geometrie des Gebaeudes" in src
    assert "Geometrie des Balkonsystems" in src
    assert "Lastansatz in Draufsicht" in src
    assert "Vereinfachte Reaktionsabschaetzung" in src
    assert "assets/building_geometry_zoning.tex" in src
    assert "assets/load_scheme.tex" in src
