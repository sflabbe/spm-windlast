"""PDF-/LaTeX-Export der Windlast-Berechnung.

Optional: benoetigt ``pdflatex`` (TeX Live oder MiKTeX) im System-PATH.

Die Legacy-API bleibt unverändert erhalten. Zusätzlich stellt dieses Paket den
Scaffold für modulare Berichte und Combined Reports bereit.
"""

from .base import ProtokolHeader
from .latex import export_pdf, render_latex
from .protokoll_verankerung import verankerung_body
from .protokoll_windlast import (
    render_windlast_modular_document,
    render_windlast_standalone,
    windlast_body,
)
from .report_bundle import compile_latex_to_pdf_bytes, create_report_zip_bundle
from .report_combined import (
    CombinedRuntimeData,
    build_combined_runtime_data,
    protokol_header_from_project_meta,
    render_combined_report,
)
from .report_selection import ModuleSelection, ReportSelection
from .report_figures import render_support_kinematics_figures

__all__ = [
    "render_latex",
    "export_pdf",
    "ProtokolHeader",
    "windlast_body",
    "render_windlast_standalone",
    "render_windlast_modular_document",
    "verankerung_body",
    "ModuleSelection",
    "ReportSelection",
    "CombinedRuntimeData",
    "render_combined_report",
    "create_report_zip_bundle",
    "compile_latex_to_pdf_bytes",
    "build_combined_runtime_data",
    "protokol_header_from_project_meta",
    "render_support_kinematics_figures",
]
