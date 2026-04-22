"""LaTeX-/PDF-Report der Windlast-Berechnung.

Produziert ein druckfertiges Statik-PDF mit Kopf-/Fusszeile, Normenverweis,
Zwischenergebnissen und Ergebnistabelle. Benoetigt ``pdflatex`` im System-PATH
(TeX Live / MiKTeX).

Dieses Modul ist OPTIONAL: der Rechenkern (``spittelmeister_windlast.core``)
funktioniert auch ohne installiertes LaTeX.

Hinweis zur Architektur:
Die Legacy-API ``render_latex`` bleibt erhalten, delegiert jedoch seit dem
Report-Refactor an ``protokoll_windlast.render_windlast_standalone``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

from ..core.modelle import Ergebnisse, Geometrie, Projekt, Standort
from ..utils.assets import copy_assets
from .protokoll_windlast import render_windlast_standalone


def render_latex(
    projekt: Projekt,
    standort: Standort,
    geo: Geometrie,
    ergebnisse: Ergebnisse,
    asset_subdir: str = "assets",
) -> str:
    """Erzeugt den vollständigen LaTeX-Quelltext des Standalone-Reports.

    Die Signatur bleibt aus Kompatibilitätsgründen unverändert.
    """
    return render_windlast_standalone(
        projekt,
        standort,
        geo,
        ergebnisse,
        asset_subdir=asset_subdir,
    )


def export_pdf(
    output_path: str,
    projekt: Projekt,
    standort: Standort,
    geo: Geometrie,
    ergebnisse: Ergebnisse,
) -> str:
    """Kompiliert den LaTeX-Quelltext mit ``pdflatex`` zu einer PDF.

    Args:
        output_path: Zielpfad der PDF-Datei.
        projekt, standort, geo, ergebnisse: wie in ``render_latex``.

    Returns:
        ``output_path`` (zur Verkettung).

    Raises:
        FileNotFoundError: Wenn ``pdflatex`` nicht installiert ist.
        RuntimeError: Wenn die LaTeX-Kompilierung fehlschlaegt.
    """
    if shutil.which("pdflatex") is None:
        raise FileNotFoundError(
            "pdflatex nicht gefunden. Bitte TeX Live oder MiKTeX installieren."
        )

    latex_assets = [
        "building_geometry_zoning.tex",
        "building_geometry_cases.tex",
        "balcony_system.tex",
        "load_scheme.tex",
        "reaction_scheme.tex",
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        copy_assets(tmpdir, latex_assets)
        latex_src = render_latex(projekt, standort, geo, ergebnisse, asset_subdir="assets")
        tex_file = os.path.join(tmpdir, "windlast.tex")
        pdf_tmp = os.path.join(tmpdir, "windlast.pdf")
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(latex_src)

        result = None
        for _ in range(2):
            result = subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-output-directory", tmpdir,
                    tex_file,
                ],
                capture_output=True, text=True,
                encoding="latin-1", errors="replace",
            )

        if not os.path.exists(pdf_tmp):
            tail = (result.stdout if result else "")[-2000:]
            raise RuntimeError("PDF-Kompilierung fehlgeschlagen.\n" + tail)

        shutil.copy(pdf_tmp, output_path)

    return output_path


__all__ = ["render_latex", "export_pdf"]
