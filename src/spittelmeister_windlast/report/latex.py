"""LaTeX-/PDF-Report der Windlast-Berechnung.

Produziert ein druckfertiges Statik-PDF mit Kopf-/Fusszeile, Normenverweis,
Zwischenergebnissen und Ergebnistabelle. Benoetigt ``pdflatex`` im System-PATH
(TeX Live / MiKTeX).

Dieses Modul ist OPTIONAL: der Rechenkern (``spittelmeister_windlast.core``)
funktioniert auch ohne installiertes LaTeX.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

from ..core.modelle import Ergebnisse, Geometrie, Projekt, Standort
from ..utils.latex_escape import latex_escape


def render_latex(
    projekt: Projekt,
    standort: Standort,
    geo: Geometrie,
    ergebnisse: Ergebnisse,
) -> str:
    """Erzeugt den vollstaendigen LaTeX-Quelltext des Reports als String."""
    e = ergebnisse
    p = projekt
    st = standort

    hoehen_labels = [
        r"$h \leq 10~\mathrm{m}$",
        r"$10 < h \leq 18~\mathrm{m}$",
        r"$18 < h \leq 25~\mathrm{m}$",
    ]
    _ = hoehen_labels[e.hoehenstufe]  # kept for backward-compat semantics
    gelaende_label = "Binnenland" if st.gelaende == "binnen" else "Kueste"

    return rf"""\documentclass[a4paper,11pt]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage{{geometry}}
\geometry{{left=2.5cm,right=2.5cm,top=2.5cm,bottom=2.5cm}}
\usepackage{{amsmath}}
\usepackage{{booktabs}}
\usepackage{{xcolor}}
\usepackage{{fancyhdr}}
\usepackage{{lastpage}}
\usepackage{{parskip}}
\usepackage{{tabularx}}
\usepackage[hidelinks]{{hyperref}}

\definecolor{{spittel}}{{RGB}}{{30,80,140}}
\definecolor{{resultbg}}{{RGB}}{{230,240,255}}

\pagestyle{{fancy}}
\fancyhf{{}}
\lhead{{\footnotesize\textbf{{Spittelmeister GmbH}} \quad Statik-Abteilung}}
\rhead{{\footnotesize Projekt: {latex_escape(p.bezeichnung)} \quad Nr.: {latex_escape(p.nummer)}}}
\lfoot{{\footnotesize Bearbeiter: {latex_escape(p.bearbeiter)} \quad Datum: {latex_escape(p.datum)}}}
\rfoot{{\footnotesize Seite \thepage\ von \pageref{{LastPage}}}}
\renewcommand{{\headrulewidth}}{{0.4pt}}
\renewcommand{{\footrulewidth}}{{0.4pt}}

\begin{{document}}
\begin{{center}}
{{\color{{spittel}}\rule{{\linewidth}}{{2pt}}}}\\[4pt]
{{\Large\bfseries\color{{spittel}} Windlastermittlung}}\\[2pt]
{{\large Balkonabschluss / Fassadenabschluss}}\\[2pt]
{{\normalsize DIN EN 1991-1-4 / NA:2010-12}}\\[4pt]
{{\color{{spittel}}\rule{{\linewidth}}{{2pt}}}}
\end{{center}}

\vspace{{4pt}}
\begin{{tabularx}}{{\linewidth}}{{lX lX}}
\textbf{{Projekt:}} & {latex_escape(p.bezeichnung)} & \textbf{{Projektnr.:}} & {latex_escape(p.nummer)} \\
\textbf{{Bearbeiter:}} & {latex_escape(p.bearbeiter)} & \textbf{{Datum:}} & {latex_escape(p.datum)} \\
\textbf{{Standort:}} & {latex_escape(st.bezeichnung)} & \textbf{{Hoehe ue.\ NN:}} & {st.hoehe_uNN:.0f}~m \\
\end{{tabularx}}
\vspace{{6pt}}
{{\color{{spittel}}\rule{{\linewidth}}{{0.6pt}}}}

\section*{{1 \quad Eingangsgroessen}}
\begin{{tabular}}{{@{{}}lll@{{}}}}
\toprule
\textbf{{Groesse}} & \textbf{{Wert}} & \textbf{{Bemerkung}} \\
\midrule
Windzone & WZ~{st.windzone} & DIN EN 1991-1-4/NA, Anhang NA.A \\
Gelaendekategorie & {gelaende_label} & Excel 27.02.2026 / NA.B.3 \\
Gebaeudehoehe & $h = {geo.h:.2f}~\mathrm{{m}}$ & massgebend fuer $q_p$ \\
Gebaeudetiefe & $d = {geo.d:.2f}~\mathrm{{m}}$ & Windrichtung 1 \\
Gebaeudebreite & $b = {geo.b:.2f}~\mathrm{{m}}$ & Windrichtung 2 \\
Hoehe OK Balkonabschluss & $z_e = {geo.z_balkon:.2f}~\mathrm{{m}}$ & Geometrie Balkon \\
Balkonausladung & $T = {geo.e_balkon:.3f}~\mathrm{{m}}$ & Seitenflaeche \\
Hoehe Abschlusselement & $h_w = {geo.h_abschluss:.2f}~\mathrm{{m}}$ & \\
Achsabstand Verankerungen & $B = {geo.s_verankerung:.2f}~\mathrm{{m}}$ & Frontflaeche \\
\bottomrule
\end{{tabular}}

\section*{{2 \quad Boeengeschwindigkeitsdruck $q_p$}}
\begin{{align*}}
q_{{b,0}} &= {e.qb0:.2f}~\mathrm{{kN/m^2}} \\
{e.qp_formel}
\end{{align*}}
\begin{{align*}}
{e.qp_auswertung}
\end{{align*}}

\noindent {e.qp_abschnitt} \\
\noindent \textit{{Normstelle:}} {e.qp_normstelle} \\
\noindent \textit{{Verfahren:}} {e.qp_verfahren}

\section*{{3 \quad Detaillierter Richtungsansatz}}
{e.cscd_begruendung}

\begin{{align*}}
h/d &= \max\left(\frac{{{geo.h:.2f}}}{{{geo.d:.2f}}},\frac{{{geo.h:.2f}}}{{{geo.b:.2f}}}\right) = {e.h_d:.2f}
\end{{align*}}

Angesetzt werden die Aussendruckbeiwerte analog Excel-Vorlage 27.02.2026 / Tafel 3.35:
\begin{{center}}
\begin{{tabular}}{{lcc}}
\toprule
Bereich & Beschreibung & $c_{{pe,10}}$ \\
\midrule
D & Seite Druck & +{e.cpe10_D:.2f} \\
E & Seite Sog & {e.cpe10_E:.2f} \\
A & Front Sog & {e.cpe10_A:.2f} \\
\bottomrule
\end{{tabular}}
\end{{center}}

\section*{{4 \quad Flaechen und Linienlasten}}
\begin{{align*}}
A_{{w,Seite}} &= T \cdot h_w = {geo.e_balkon:.3f} \cdot {geo.h_abschluss:.2f} = {e.A_w_side:.2f}~\mathrm{{m^2}} \\
A_{{w,Front}} &= B \cdot h_w = {geo.s_verankerung:.2f} \cdot {geo.h_abschluss:.2f} = {e.A_w_front:.2f}~\mathrm{{m^2}}
\end{{align*}}

\begin{{center}}
\begin{{tabular}}{{lccc}}
\toprule
Lastfall & $w_e$ [kN/m$^2$] & $q$ [kN/m] & Bemerkung \\
\midrule
Seite Druck (D) & {e.we_side_pressure:.2f} & {e.q_side_pressure:.2f} & \\
Seite Sog (E) & {e.we_side_suction:.2f} & {e.q_side_suction:.2f} & \\
Front Sog (A) & {e.we_front_suction:.2f} & {e.q_front_suction:.2f} & pruefen \\
\bottomrule
\end{{tabular}}
\end{{center}}

\section*{{5 \quad Massgebende Schnittgroessen}}
Massgebender Lastfall: \textbf{{{e.lastfall_massgebend}}}
\begin{{align*}}
q_{{h,k}} &= \mathbf{{{e.qhk:.2f}~\mathrm{{kN/m}}}} \\
H_k &= q_{{h,k}} \cdot B = {e.qhk:.2f} \cdot {geo.s_verankerung:.2f} = \mathbf{{{e.Hk:.2f}~\mathrm{{kN}}}} \\
M_{{k,Fusspunkt}} &= H_k \cdot \frac{{h_w}}{{2}} = {e.Hk:.2f} \cdot {geo.h_abschluss/2:.3f} = \mathbf{{{e.Mk:.2f}~\mathrm{{kNm}}}}
\end{{align*}}

\vspace{{8pt}}
\begin{{center}}
{{\color{{spittel}}\bfseries\large Zusammenfassung Ergebnisse}}\\[6pt]
\colorbox{{resultbg}}{{%
\begin{{tabular}}{{lrl}}
\toprule
\textbf{{Groesse}} & \textbf{{Wert}} & \textbf{{Einheit}} \\
\midrule
$q_p(h)$ & {e.qp:.3f} & $\mathrm{{kN/m^2}}$ \\
$w_k$ (massg.) & {e.wk_massgebend:.2f} & $\mathrm{{kN/m^2}}$ \\
$q_{{h,k}}$ & {e.qhk:.2f} & $\mathrm{{kN/m}}$ \\
$H_k$ je Feld & {e.Hk:.2f} & $\mathrm{{kN}}$ \\
$M_{{k,\mathrm{{Fusspunkt}}}}$ & {e.Mk:.2f} & $\mathrm{{kNm}}$ \\
\bottomrule
\end{{tabular}}%
}}
\end{{center}}

\end{{document}}
"""


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

    latex_src = render_latex(projekt, standort, geo, ergebnisse)

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_file = os.path.join(tmpdir, "windlast.tex")
        pdf_tmp = os.path.join(tmpdir, "windlast.pdf")
        with open(tex_file, "w", encoding="utf-8") as f:
            f.write(latex_src)

        # Zweimal kompilieren fuer korrekte lastpage-Referenzen
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
