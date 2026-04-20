"""Tests fuer den Bequemlichkeits-Wrapper ``WindlastBerechnung.export_pdf``."""

from __future__ import annotations

import shutil
from unittest.mock import patch

import pytest

from spittelmeister_windlast import (
    Geometrie,
    Projekt,
    Standort,
    WindlastBerechnung,
)


def _wb() -> WindlastBerechnung:
    return WindlastBerechnung(
        Projekt("Demo", "T-EXP", "Test"),
        Standort("Pforzheim", 1, "binnen", 280.0),
        Geometrie(h=15.0, d=12.0, b=20.0, z_balkon=13.0,
                  e_balkon=1.4, h_abschluss=3.0, s_verankerung=5.0),
    )


def test_export_pdf_ruft_report_modul(tmp_path):
    """Der Wrapper delegiert an spittelmeister_windlast.report.export_pdf."""
    wb = _wb()
    out = tmp_path / "test.pdf"

    # Patch auf dem import-site (report.export_pdf wird lazy importiert)
    with patch("spittelmeister_windlast.report.export_pdf") as mock_exp:
        mock_exp.return_value = str(out)
        result = wb.export_pdf(str(out))

    mock_exp.assert_called_once()
    args = mock_exp.call_args.args
    assert args[0] == str(out)
    assert args[1] is wb.projekt
    assert args[2] is wb.standort
    assert args[3] is wb.geo
    assert args[4] is wb.erg  # Ergebnis muss vorliegen
    assert result == str(out)


def test_export_pdf_ruft_berechnen_wenn_noetig(tmp_path):
    """Auch ohne explizites berechnen() darf export_pdf nicht crashen."""
    wb = _wb()
    assert wb.erg is None

    with patch("spittelmeister_windlast.report.export_pdf") as mock_exp:
        mock_exp.return_value = str(tmp_path / "x.pdf")
        wb.export_pdf(str(tmp_path / "x.pdf"))

    assert wb.erg is not None


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex nicht installiert")
def test_export_pdf_end_to_end(tmp_path):
    """Wenn pdflatex installiert ist: vollstaendiger Durchlauf bis zur PDF."""
    wb = _wb()
    out = tmp_path / "windlast.pdf"
    wb.export_pdf(str(out))
    assert out.exists()
    assert out.stat().st_size > 1000  # Mindestens 1 kB
