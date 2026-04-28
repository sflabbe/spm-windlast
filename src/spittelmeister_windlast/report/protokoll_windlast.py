from __future__ import annotations

from ..core.modelle import Ergebnisse, Geometrie, Projekt, Standort
from ..transfer import derive_connection_actions_from_wind
from ..transfer.modelle import ConnectionActions
from ..utils.latex_escape import latex_escape
from .base import MODUS_STATIK, PreambleStyle, build_document


def _gelaende_label(standort: Standort, ergebnisse: Ergebnisse) -> str:
    if getattr(ergebnisse, "gelaende_label", None):
        return ergebnisse.gelaende_label
    return "Binnenland" if standort.gelaende == "binnen" else "Küste"


def _title_block(projekt: Projekt, standort: Standort) -> str:
    return rf"""
\begin{{center}}
{{\color{{SPAccent}}\rule{{\linewidth}}{{2pt}}}}\\[4pt]
{{\Large\bfseries\color{{SPAccent}} Windlastermittlung}}\\[2pt]
{{\large Balkonabschluss / Fassadenabschluss}}\\[2pt]
{{\normalsize DIN EN 1991-1-4 / NA:2010-12}}\\[4pt]
{{\color{{SPAccent}}\rule{{\linewidth}}{{2pt}}}}
\end{{center}}

\vspace{{4pt}}
\begin{{tabularx}}{{\linewidth}}{{lX lX}}
\textbf{{Projekt:}} & {latex_escape(projekt.bezeichnung)} & \textbf{{Projektnr.:}} & {latex_escape(projekt.nummer)} \\
\textbf{{Bearbeiter:}} & {latex_escape(projekt.bearbeiter)} & \textbf{{Datum:}} & {latex_escape(projekt.datum)} \\
\textbf{{Standort:}} & {latex_escape(standort.bezeichnung)} & \textbf{{Höhe ü. NN:}} & {standort.hoehe_uNN:.0f}~m \\
\end{{tabularx}}
\vspace{{6pt}}
{{\color{{SPAccent}}\rule{{\linewidth}}{{0.6pt}}}}
"""


def _asset_figure_block(
    *,
    asset_subdir: str,
    tex_name: str | None = None,
    pdf_name: str | None = None,
    caption: str,
    width: str = r"\linewidth",
) -> str:
    """Render a report figure with legacy PDF assets first and TikZ fallback."""
    figure_body = r"\fbox{Figure asset missing}"
    if tex_name:
        figure_body = (
            rf"\IfFileExists{{{asset_subdir}/{tex_name}}}{{\input{{{asset_subdir}/{tex_name}}}}}"
            + "{"
            + figure_body
            + "}"
        )
    if pdf_name:
        figure_body = (
            rf"\IfFileExists{{{asset_subdir}/{pdf_name}}}{{\includegraphics[width={width}]{{{asset_subdir}/{pdf_name}}}}}"
            + "{"
            + figure_body
            + "}"
        )

    return rf"""
\begin{{figure}}[H]
\centering
{figure_body}
\caption{{{caption}}}
\end{{figure}}
"""


def _section_1_inputs(geo: Geometrie, standort: Standort, ergebnisse: Ergebnisse) -> str:
    gelaende_label = _gelaende_label(standort, ergebnisse)
    return rf"""
\section*{{1 \quad Eingangsgroessen}}
\begin{{tabular}}{{@{{}}lll@{{}}}}
\toprule
\textbf{{Groesse}} & \textbf{{Wert}} & \textbf{{Bemerkung}} \\
\midrule
Windzone & WZ~{standort.windzone} & DIN EN 1991-1-4/NA, Anhang NA.A \\
Geländekategorie & {gelaende_label} & NA.B.3 \\
Gebäudehöhe & $h = {geo.h:.2f}~\mathrm{{m}}$ & massgebend für $q_p$ \\
Gebäudetiefe & $d = {geo.d:.2f}~\mathrm{{m}}$ & Windrichtung 1 \\
Gebäudebreite & $b = {geo.b:.2f}~\mathrm{{m}}$ & Windrichtung 2 \\
Höhe OK Balkon / Geländeroberkante & $z_e = {geo.z_balkon:.2f}~\mathrm{{m}}$ & Geometrie Balkon \\
Balkon Tiefe & $T = {geo.e_balkon:.3f}~\mathrm{{m}}$ & Seitenfläche \\
Höhe Geländer bzw. Abschattung & $h_w = {geo.h_abschluss:.2f}~\mathrm{{m}}$ & wirksame Höhe \\
Balkon Breite & $B = {geo.s_verankerung:.2f}~\mathrm{{m}}$ & Frontfläche \\
Verankerung Abstand zum Rand & $a = {geo.b_auflager_rand:.2f}~\mathrm{{m}}$ & Randabstand je Seite \\
\bottomrule
\end{{tabular}}
"""


def _section_2_figures(asset_subdir: str) -> str:
    return (
        r"\section*{2 \quad Geometrische Systemskizzen}"
        + "\n\n"
        + r"\subsection*{2.1 \quad Geometrie des Gebaeudes}"
        + "\n"
        + _asset_figure_block(
            asset_subdir=asset_subdir,
            tex_name="building_geometry_zoning.tex",
            pdf_name="wind_geb.pdf",
            caption=r"Zonierung und Parameterzuordnung $h,d,b,e$.",
        )
        + "\n"
        + _asset_figure_block(
            asset_subdir=asset_subdir,
            tex_name="building_geometry_cases.tex",
            pdf_name="building_geometry_cases.pdf",
            caption=r"Geometrie-Fallunterscheidung fuer den vereinfachten Windlastansatz.",
        )
        + "\n"
        + r"\subsection*{2.2 \quad Geometrie des Balkonsystems}"
        + "\n"
        + _asset_figure_block(
            asset_subdir=asset_subdir,
            tex_name="balcony_system.tex",
            pdf_name="balcony_system.pdf",
            caption=r"Draufsicht mit Balkonbreite $B$, Balkontiefe $T$, Randabstand $a$ sowie Festlager/Gleitlager in $x$.",
        )
    )


def _section_3_qp(ergebnisse: Ergebnisse) -> str:
    return rf"""
\section*{{3 \quad Boeengeschwindigkeitsdruck $q_p$}}
\begin{{align*}}
q_{{b,0}} &= {ergebnisse.qb0:.2f}~\mathrm{{kN/m^2}} \\
{ergebnisse.qp_formel}
\end{{align*}}
\begin{{align*}}
{ergebnisse.qp_auswertung}
\end{{align*}}

\noindent {ergebnisse.qp_abschnitt} \\
\noindent \textit{{Normstelle:}} {ergebnisse.qp_normstelle} \\
\noindent \textit{{Verfahren:}} {ergebnisse.qp_verfahren}
"""


def _section_4_directional(geo: Geometrie, ergebnisse: Ergebnisse) -> str:
    return rf"""
\section*{{4 \quad Detaillierter Richtungsansatz}}
{ergebnisse.cscd_begruendung}

\begin{{align*}}
h/d &= \max\left(\frac{{{geo.h:.2f}}}{{{geo.d:.2f}}},\frac{{{geo.h:.2f}}}{{{geo.b:.2f}}}\right) = {ergebnisse.h_d:.2f}
\end{{align*}}

Angesetzt werden die Aussendruckbeiwerte analog Excel-Vorlage 27.02.2026 / Tafel 3.35:
\begin{{center}}
\begin{{tabular}}{{lcc}}
\toprule
Bereich & Beschreibung & $c_{{pe,10}}$ \\
\midrule
D & Seite Druck & +{ergebnisse.cpe10_D:.2f} \\
E & Seite Sog & {ergebnisse.cpe10_E:.2f} \\
A & Front Sog & {ergebnisse.cpe10_A:.2f} \\
\bottomrule
\end{{tabular}}
\end{{center}}
"""

def _section_5_loads(geo: Geometrie, ergebnisse: Ergebnisse, asset_subdir: str) -> str:
    figure_block = _asset_figure_block(
        asset_subdir=asset_subdir,
        tex_name="",
        pdf_name="load_scheme.pdf",
        caption=r"Ansatz der Linienlasten $q_{seite,1}$, $q_{seite,2}$ und $q_{vorne}$.",
    )
    return rf"""
\section*{{5 \quad Flaechen und Linienlasten}}
\begin{{align*}}
A_{{w,Seite}} &= T \cdot h_w = {geo.e_balkon:.3f} \cdot {geo.h_abschluss:.2f} = {ergebnisse.A_w_side:.2f}~\mathrm{{m^2}} \\
A_{{w,Front}} &= B \cdot h_w = {geo.s_verankerung:.2f} \cdot {geo.h_abschluss:.2f} = {ergebnisse.A_w_front:.2f}~\mathrm{{m^2}}
\end{{align*}}

\subsection*{{5.1 \quad Lastansatz in Draufsicht}}
{figure_block}

\begin{{center}}
\begin{{tabular}}{{lccc}}
\toprule
Lastfall & $w_e$ [kN/m$^2$] & $q$ [kN/m] & Bemerkung \\
\midrule
Seite Druck (D) & {ergebnisse.we_side_pressure:.2f} & {ergebnisse.q_side_pressure:.2f} & \\
Seite Sog (E) & {ergebnisse.we_side_suction:.2f} & {ergebnisse.q_side_suction:.2f} & \\
Front Sog (A) & {ergebnisse.we_front_suction:.2f} & {ergebnisse.q_front_suction:.2f} & pruefen \\
\bottomrule
\end{{tabular}}
\end{{center}}
"""

def _section_6_decisive(geo: Geometrie, ergebnisse: Ergebnisse) -> str:
    return rf"""
\section*{{6 \quad Massgebende Schnittgroessen}}
Maßgebender Lastfall: \textbf{{{ergebnisse.lastfall_massgebend}}}
\begin{{align*}}
q_{{h,k}} &= \mathbf{{{ergebnisse.qhk:.2f}~\mathrm{{kN/m}}}} \\
H_k &= q_{{h,k}} \cdot B = {ergebnisse.qhk:.2f} \cdot {geo.s_verankerung:.2f} = \mathbf{{{ergebnisse.Hk:.2f}~\mathrm{{kN}}}} \\
M_{{k,Fusspunkt}} &= H_k \cdot \frac{{h_w}}{{2}} = {ergebnisse.Hk:.2f} \cdot {geo.h_abschluss/2:.3f} = \mathbf{{{ergebnisse.Mk:.2f}~\mathrm{{kNm}}}}
\end{{align*}}

\vspace{{8pt}}
\begin{{center}}
{{\color{{SPAccent}}\bfseries\large Zusammenfassung Ergebnisse}}\\[6pt]
\colorbox{{resultbg}}{{%
\begin{{tabular}}{{lrl}}
\toprule
\textbf{{Groesse}} & \textbf{{Wert}} & \textbf{{Einheit}} \\
\midrule
$q_p(h)$ & {ergebnisse.qp:.3f} & $\mathrm{{kN/m^2}}$ \\
$w_k$ (massg.) & {ergebnisse.wk_massgebend:.2f} & $\mathrm{{kN/m^2}}$ \\
$q_{{h,k}}$ & {ergebnisse.qhk:.2f} & $\mathrm{{kN/m}}$ \\
$H_k$ je Feld & {ergebnisse.Hk:.2f} & $\mathrm{{kN}}$ \\
$M_{{k,\mathrm{{Fusspunkt}}}}$ & {ergebnisse.Mk:.2f} & $\mathrm{{kNm}}$ \\
\bottomrule
\end{{tabular}}%
}}
\end{{center}}
"""


def _section_7_reactions(geo: Geometrie, ergebnisse: Ergebnisse, actions: ConnectionActions, asset_subdir: str) -> str:
    figure_block = _asset_figure_block(
        asset_subdir=asset_subdir,
        tex_name="",
        pdf_name="reaction_scheme.pdf",
        caption=r"Linienlasten und Reaktionen $H_x$, $H_{y,1}$, $H_{y,2}$ mit Lagerannahme.",
    )
    return rf"""
\section*{{7 \quad Vereinfachte Reaktionsabschaetzung}}
{figure_block}

\textbf{{Vereinfachte Reaktionsabschaetzung des Balkonsystems in Draufsicht}}

\subsection*{{7.1 \quad Formelansatz und Herleitung (Vorbemessung)}}
Die Winddruckbeiwerte aus Abschnitt~4 werden als Flaechenlasten $w_e$ angesetzt und ueber die wirksamen
Windflaechenhoehen in Linienlasten umgerechnet:

\begin{{align*}}
q_{{seite,1}} &= |w_{{e,seite,druck}}| \cdot h_{{w,yz}} = |{ergebnisse.we_side_pressure:.3f}| \cdot {geo.h_abschluss:.2f} = {actions.q_seite_1:.3f}~\mathrm{{kN/m}} \\
q_{{seite,2}} &= |w_{{e,seite,sog}}| \cdot h_{{w,yz}} = |{ergebnisse.we_side_suction:.3f}| \cdot {geo.h_abschluss:.2f} = {actions.q_seite_2:.3f}~\mathrm{{kN/m}} \\
q_{{vorne}} &= |w_{{e,front,sog}}| \cdot h_{{w,xz}} = |{ergebnisse.we_front_suction:.3f}| \cdot {geo.h_abschluss:.2f} = {actions.q_vorne:.3f}~\mathrm{{kN/m}}
\end{{align*}}

Mit dem Auflagerabstand $s = B - 2a$ ergibt sich aus Kraefte- und Momentengleichgewicht in Draufsicht:
\begin{{align*}}
H_{{x,k}} &= T \cdot (q_{{seite,1}}+q_{{seite,2}}) = {geo.e_balkon:.3f} \cdot ({actions.q_seite_1:.3f}+{actions.q_seite_2:.3f}) = {actions.Hx_k:.2f}~\mathrm{{kN}} \\
M_{{A,k}} &= \frac{{T^2}}{{2}}(q_{{seite,1}}+q_{{seite,2}}) + q_{{vorne}} \cdot B \cdot (B/2-a) = {actions.M_A_k:.2f}~\mathrm{{kNm}} \\
s &= B - 2a = {geo.s_verankerung:.2f} - 2\cdot{geo.b_auflager_rand:.2f} = {actions.s:.3f}~\mathrm{{m}} \\
H_{{y,2,k}} &= M_{{A,k}}/s = {actions.Hy_2_k:.2f}~\mathrm{{kN}} \\
H_{{y,1,k}} &= q_{{vorne}}\cdot B - H_{{y,2,k}} = {actions.Hy_1_k:.2f}~\mathrm{{kN}}
\end{{align*}}

\begin{{center}}
\begin{{tabular}}{{lrr}}
\toprule
\textbf{{Groesse}} & \textbf{{k-Wert}} & \textbf{{Ed-Wert}} \\
\midrule
$H_x$ & {actions.Hx_k:.2f}~kN & {actions.Hx_Ed:.2f}~kN \\
$H_{{y,1}}$ & {actions.Hy_1_k:.2f}~kN & {actions.Hy_1_Ed:.2f}~kN \\
$H_{{y,2}}$ & {actions.Hy_2_k:.2f}~kN & {actions.Hy_2_Ed:.2f}~kN \\
\bottomrule
\end{{tabular}}
\end{{center}}

\noindent\textit{{Strukturelle Hypothesen:}} ein Auflager als Festlager in x, ein Auflager als Gleitlager in x; Reaktionen in y rein aus Gleichgewicht in Draufsicht; keine Verformungskompatibilitaet und keine Torsionsumlagerung im Gesamttragwerk.\\
\noindent\textit{{Technische Einordnung:}} {latex_escape(actions.note)}
"""


def windlast_body(
    projekt: Projekt,
    standort: Standort,
    geo: Geometrie,
    ergebnisse: Ergebnisse,
    *,
    report_style: str = "standalone",
    asset_subdir: str = "assets",
) -> str:
    """Modularer Windlast-Berichtskörper.

    In ``standalone`` enthält der Body Titelblock und Projektkopf. In ``combined``
    wird nur der eigentliche Modulinhalt ohne separates Deckblatt ausgegeben.
    """
    actions = derive_connection_actions_from_wind(geo, ergebnisse)

    parts: list[str] = []
    if report_style == "standalone":
        parts.append(_title_block(projekt, standort))
    else:
        parts.append(r"\section{Windlastermittlung}")

    parts.extend(
        [
            _section_1_inputs(geo, standort, ergebnisse),
            _section_2_figures(asset_subdir),
            _section_3_qp(ergebnisse),
            _section_4_directional(geo, ergebnisse),
            _section_5_loads(geo, ergebnisse, asset_subdir),
            _section_6_decisive(geo, ergebnisse),
            _section_7_reactions(geo, ergebnisse, actions, asset_subdir),
        ]
    )
    return "\n\n".join(parts)


def render_windlast_standalone(
    projekt: Projekt,
    standort: Standort,
    geo: Geometrie,
    ergebnisse: Ergebnisse,
    asset_subdir: str = "assets",
) -> str:
    body = windlast_body(
        projekt,
        standort,
        geo,
        ergebnisse,
        report_style="standalone",
        asset_subdir=asset_subdir,
    )
    return build_document("Windlastermittlung", body, style=PreambleStyle.COLOR.value)


def render_windlast_modular_document(
    projekt: Projekt,
    standort: Standort,
    geo: Geometrie,
    ergebnisse: Ergebnisse,
) -> str:
    body = windlast_body(
        projekt,
        standort,
        geo,
        ergebnisse,
        report_style="combined",
    )
    return build_document(MODUS_STATIK, body, style=PreambleStyle.COMBINED_NEUTRAL.value)
