from __future__ import annotations

from ..transfer.modelle import ConnectionActions, SupportAction
from ..utils.latex_escape import latex_escape
from ..verankerung.modelle import AnchorageAssessment, AnchorageInput
from .report_figures import render_support_kinematics_figures


def _status_tex(status: str) -> str:
    if status == "ok":
        return r"\IOstatus"
    if status == "fail":
        return r"\NIOstatus"
    return r"\HINWEISstatus"


def _bullet_list(items: list[str]) -> str:
    if not items:
        return r"\begin{itemize}\item Keine zusätzlichen Angaben vorhanden.\end{itemize}"
    rows = "\n".join(rf"\item {latex_escape(item)}" for item in items)
    return "\\begin{itemize}\n" + rows + "\n\\end{itemize}"


def _kinematics_table(anchorage: AnchorageInput | None, support_action: SupportAction | None) -> str:
    if anchorage is None:
        return r"""
\subsection*{Lagerkinematik und Exzentrizität}
\HINWEISstatus\ Es wurden noch keine expliziten Lagerdaten übergeben.
"""
    if support_action is None:
        return rf"""
\subsection*{{Lagerkinematik und Exzentrizität}}
\begin{{tabularx}}{{\linewidth}}{{lX}}
\toprule
Stützstelle & {anchorage.support_index} \\
Lagerrolle & {latex_escape(anchorage.support_role)} \\
Gleitachse & {latex_escape(anchorage.slide_direction)} \\
WDVS / Spalt [mm] & {(anchorage.wdvs_mm or 0.0):.0f} / {(anchorage.spalt_mm or 0.0):.0f} \\
Lokale Exzentrizität [mm] & {anchorage.local_eccentricity_mm:.1f} \\
Plattform-Exzentrizität [mm] & {(anchorage.platform_eccentricity_mm or 0.0):.1f} \\
\bottomrule
\end{{tabularx}}
"""
    return rf"""
\subsection*{{Lagerkinematik und Exzentrizität}}
\begin{{tabularx}}{{\linewidth}}{{lX}}
\toprule
Stützstelle & {support_action.support_index} \\
Lagerrolle & {latex_escape(support_action.support_role)} \\
Gleitachse & {latex_escape(support_action.slide_direction)} \\
WDVS / Spalt [mm] & {(anchorage.wdvs_mm or 0.0):.0f} / {(anchorage.spalt_mm or 0.0):.0f} \\
Lokale Exzentrizität [mm] & {support_action.local_eccentricity_mm:.1f} \\
Plattform-Exzentrizität [mm] & {support_action.platform_eccentricity_mm:.1f} \\
Freigegebene Komponente [kN] & {support_action.released_component_Ed:.2f} \\
Zusatzmoment $M_{{add,Ed}}$ [kNm] & {support_action.additional_moment_Ed:.2f} \\
\bottomrule
\end{{tabularx}}
"""


def _support_action_table(support_action: SupportAction | None) -> str:
    if support_action is None:
        return ""
    return rf"""
\subsection*{{Abgeleitete lokale Stützstellenlasten}}
\begin{{tabular}}{{lrr}}
\toprule
Größe & Basis & Übertragen \\
\midrule
$F_{{x,Ed}}$ & {support_action.base_fx_Ed:.2f}~kN & {support_action.transferred_fx_Ed:.2f}~kN \\
$F_{{y,Ed}}$ & {support_action.base_fy_Ed:.2f}~kN & {support_action.transferred_fy_Ed:.2f}~kN \\
$R_{{h,Ed}}$ & \multicolumn{{2}}{{r}}{{{support_action.total_resultant_Ed:.2f}~kN}} \\
$M_{{add,Ed}}$ & \multicolumn{{2}}{{r}}{{{support_action.additional_moment_Ed:.2f}~kNm}} \\
\bottomrule
\end{{tabular}}

\noindent\textit{{Stützstellenmodell:}} {latex_escape(support_action.note)}
"""


def verankerung_body(
    actions: ConnectionActions,
    assessment: AnchorageAssessment | None,
    anchorage: AnchorageInput | None = None,
    support_action: SupportAction | None = None,
    *,
    report_style: str = "standalone",
) -> str:
    heading = (
        r"\section{Verankerung / Anschluss}"
        if report_style == "combined"
        else r"\begin{verificationmodule}{Verankerung / Anschluss}"
    )
    closing = "" if report_style == "combined" else r"\end{verificationmodule}"

    if assessment is not None:
        rows = [
            rf"{latex_escape(item.title)} & {_status_tex(item.status)} & {latex_escape(item.detail)} \\\\"
            for item in assessment.checks
        ]
        basis_items = assessment.basis_summary
        geometry_items = assessment.geometry_summary
        decisive_items = assessment.decisive_notes
        manual_scope = assessment.manual_scope
        overall_status = assessment.overall_status
    else:
        rows = [r"Scaffold-Stand & \HINWEISstatus & Noch kein Assessment übergeben. \\\\" ]
        basis_items = []
        geometry_items = []
        decisive_items = []
        manual_scope = []
        overall_status = "open"

    table_body = "\n".join(rows)

    if anchorage is not None:
        edge_text = ", ".join(
            f"{key}={value:.0f}"
            for key, value in sorted(anchorage.edge_distances_mm.items())
        ) or "nicht erfasst"
        spacing_text = ", ".join(
            f"{key}={value:.0f}"
            for key, value in sorted(anchorage.spacing_mm.items())
        ) or "nicht erfasst"
        plate_width = "-" if anchorage.plate_width_mm is None else f"{anchorage.plate_width_mm:.0f}"
        plate_height = "-" if anchorage.plate_height_mm is None else f"{anchorage.plate_height_mm:.0f}"
        plate_thickness = "-" if anchorage.plate_thickness_mm is None else f"{anchorage.plate_thickness_mm:.0f}"
        geometry_table = rf"""
\subsection*{{Anschlussgeometrie und Grundlagen}}
\begin{{tabularx}}{{\linewidth}}{{lX}}
\toprule
Bezeichnung & {latex_escape(anchorage.connection_label)} \\
Ankergruppe & {latex_escape(anchorage.anchor_group_shape)} / {latex_escape(anchorage.anchor_designation)} \\
Untergrund / Bauteil & {latex_escape(anchorage.support_type)} \\
Materialgrundlage & {latex_escape(anchorage.substrate_strength_class)} \\
Platte [mm] & {plate_width} x {plate_height} x {plate_thickness} \\
Randabstände [mm] & {latex_escape(edge_text)} \\
Achsabstände [mm] & {latex_escape(spacing_text)} \\
Nachweisstrategie & {latex_escape(anchorage.manufacturer_mode)} \\
\bottomrule
\end{{tabularx}}
"""
    else:
        geometry_table = r"""
\subsection*{Anschlussgeometrie und Grundlagen}
\HINWEISstatus\ Es wurden noch keine expliziten Anschluss-Eingabedaten übergeben.
"""

    return rf"""
{heading}
Die Anschlussgrößen werden aus dem Windmodul übernommen und als Grundlage einer
projektspezifischen Verankerungsbewertung dokumentiert. Für Festlager/Gleitlager
wird zusätzlich ein idealisiertes Stützstellenmodell mit lokaler Exzentrizität
angesetzt. Ein vollständiger Verankerungsnachweis wird nicht vorgetäuscht.

\resultbox{{
Gesamtstatus: {_status_tex(overall_status)}\\
$H_{{x,Ed}} = {actions.Hx_Ed:.2f}\,\mathrm{{kN}}$,
$H_{{y,1,Ed}} = {actions.Hy_1_Ed:.2f}\,\mathrm{{kN}}$,
$H_{{y,2,Ed}} = {actions.Hy_2_Ed:.2f}\,\mathrm{{kN}}$,
$M_{{A,k}} = {actions.M_A_k:.2f}\,\mathrm{{kNm}}$
}}

\subsection*{{Übernommene Lastbasis}}
\begin{{tabular}}{{lrr}}
\toprule
Größe & k-Wert & Ed-Wert \\
\midrule
$H_x$ & {actions.Hx_k:.2f}~kN & {actions.Hx_Ed:.2f}~kN \\
$H_{{y,1}}$ & {actions.Hy_1_k:.2f}~kN & {actions.Hy_1_Ed:.2f}~kN \\
$H_{{y,2}}$ & {actions.Hy_2_k:.2f}~kN & {actions.Hy_2_Ed:.2f}~kN \\
\bottomrule
\end{{tabular}}

\noindent\textit{{Transfermodell:}} {latex_escape(actions.model_name)}\\
\noindent\textit{{Hinweis:}} {latex_escape(actions.note)}

{geometry_table}

{_kinematics_table(anchorage, support_action)}

{render_support_kinematics_figures(anchorage, support_action, actions)}

{_support_action_table(support_action)}

\subsection*{{Bewertungsmatrix}}
\begin{{tabularx}}{{\linewidth}}{{l l X}}
\toprule
Prüfpunkt & Status & Bemerkung \\
\midrule
{table_body}
\bottomrule
\end{{tabularx}}

\subsection*{{Einordnung und offene Punkte}}
\paragraph{{Basis der Vorprüfung}}
{_bullet_list(basis_items)}

\paragraph{{Geometrisch dokumentierte Angaben}}
{_bullet_list(geometry_items)}

\paragraph{{Entscheidende Hinweise}}
{_bullet_list(decisive_items)}

\paragraph{{Nicht abgedeckter Restumfang}}
{_bullet_list(manual_scope)}

{closing}
"""
