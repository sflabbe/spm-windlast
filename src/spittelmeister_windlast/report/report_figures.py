from __future__ import annotations

from pathlib import Path

from ..transfer.modelle import ConnectionActions, SupportAction
from ..utils.latex_escape import latex_escape
from ..verankerung.modelle import AnchorageInput

DEFAULT_FIGURE_MAP = {
    "wind_geb": "wind_geb.svg",
    "balcony_system": "balcony_system.svg",
    "reaction_scheme": "reaction_scheme.svg",
    "verankerung": "verankerung.svg",
}


def resolve_figure_paths(repo_root: str | Path | None = None) -> dict[str, Path]:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    assets_root = root / "assets"
    return {key: assets_root / value for key, value in DEFAULT_FIGURE_MAP.items()}


def _support_positions() -> tuple[float, float, float]:
    return 1.8, 8.2, 5.0


def render_support_plan_sketch(
    anchorage: AnchorageInput | None,
    support_action: SupportAction | None,
    actions: ConnectionActions | None = None,
) -> str:
    if anchorage is None or support_action is None:
        return r"""
\textbf{Skizze in Plandarstellung}\\
\HINWEISstatus\ Keine Plandarstellung ableitbar, da Lagerdaten fehlen.
"""

    x1, x2, xc = _support_positions()
    active_x = x1 if support_action.support_index == 1 else x2
    passive_x = x2 if support_action.support_index == 1 else x1
    platform_e = float(support_action.platform_eccentricity_mm or 0.0)
    result_y = 3.15
    if platform_e > 0.0:
        shift = min(platform_e / 120.0, 1.2)
        result_x = xc + shift if support_action.support_index == 2 else xc - shift
    else:
        result_x = xc

    fest_idx = 1 if (anchorage.support_role == "gleitlager" and support_action.support_index == 2) else 2 if (anchorage.support_role == "gleitlager" and support_action.support_index == 1) else support_action.support_index
    gleit_idx = support_action.support_index if anchorage.support_role == "gleitlager" else (2 if support_action.support_index == 1 else 1)

    released_arrow = ""
    if anchorage.support_role == "gleitlager":
        if support_action.slide_direction == "x":
            released_arrow = rf"\draw[<->, gray!70, dashed] ({active_x-0.75:.2f},0.85) -- ({active_x+0.75:.2f},0.85) node[midway, below, fill=white, inner sep=1pt] {{\scriptsize Gleitachse x}};"
        else:
            released_arrow = rf"\draw[<->, gray!70, dashed] ({active_x:.2f},0.25) -- ({active_x:.2f},1.45) node[midway, right, fill=white, inner sep=1pt] {{\scriptsize Gleitachse y}};"

    fx = support_action.transferred_fx_Ed
    fy = support_action.transferred_fy_Ed
    hx_arrow = rf"\draw[->, thick] ({result_x+1.45:.2f},{result_y:.2f}) -- ({result_x+0.20:.2f},{result_y:.2f}) node[midway, above, fill=white, inner sep=1pt] {{\scriptsize $H_x={fx:.2f}$}};" if abs(fx) > 1e-9 else rf"\node[font=\scriptsize, anchor=west] at ({result_x+0.20:.2f},{result_y+0.20:.2f}) {{$H_x=0.00$}};"
    hy_arrow = rf"\draw[->, thick] ({result_x:.2f},{result_y+1.25:.2f}) -- ({result_x:.2f},{result_y+0.15:.2f}) node[midway, right, fill=white, inner sep=1pt] {{\scriptsize $H_y={fy:.2f}$}};" if abs(fy) > 1e-9 else rf"\node[font=\scriptsize, anchor=west] at ({result_x+0.15:.2f},{result_y+0.95:.2f}) {{$H_y=0.00$}};"
    result_label = rf"\node[font=\scriptsize, fill=white, inner sep=1pt] at ({result_x:.2f},{result_y-0.45:.2f}) {{$e_{{platform}}={platform_e:.0f}\,\mathrm{{mm}}$}};" if platform_e > 0 else rf"\node[font=\scriptsize, fill=white, inner sep=1pt] at ({result_x:.2f},{result_y-0.45:.2f}) {{$e_{{platform}}=0$}};"

    return rf"""
\textbf{{Skizze in Plandarstellung}}\\[2pt]
\begin{{tikzpicture}}[x=1cm,y=1cm]
  \draw[line width=0.9pt] (0.7,1.35) -- (9.3,1.35);
  \node[font=\scriptsize, anchor=south] at (5.0,1.45) {{Linie der Stützstellen / Anschlussachsen}};
  \filldraw[fill=black!8, draw=black] ({x1:.2f},1.35) circle (0.12);
  \filldraw[fill=black!8, draw=black] ({x2:.2f},1.35) circle (0.12);
  \node[font=\scriptsize, anchor=north] at ({x1:.2f},1.05) {{Stützstelle 1}};
  \node[font=\scriptsize, anchor=north] at ({x2:.2f},1.05) {{Stützstelle 2}};
  \draw[<->] ({x1:.2f},0.45) -- ({x2:.2f},0.45) node[midway, below, fill=white, inner sep=1pt] {{\scriptsize $s \approx {actions.s if actions else 0.0:.2f}\,\mathrm{{m}}$}};

  \draw[fill=SPAccent!12, draw=SPAccent, rounded corners=1.8pt] (1.1,2.6) rectangle (8.9,3.6);
  \node[font=\scriptsize] at (5.0,3.1) {{Balkonplattform / Lastangriffsebene}};

  \draw[densely dashed, gray!70] ({result_x:.2f},1.35) -- ({result_x:.2f},3.6);
  \filldraw[fill=SPAccent!55, draw=SPAccent] ({result_x:.2f},{result_y:.2f}) circle (0.08);
  \node[font=\scriptsize, anchor=south west] at ({result_x+0.12:.2f},{result_y+0.05:.2f}) {{Resultierende Plattformlast}};
  {result_label}

  \draw[SPAccent, line width=1.0pt] ({active_x-0.28:.2f},1.65) rectangle ({active_x+0.28:.2f},2.05);
  \node[font=\scriptsize, text=SPAccent, anchor=south] at ({active_x:.2f},2.08) {{{latex_escape(support_action.support_role)}}};
  \draw[gray!70] ({passive_x-0.18:.2f},1.72) rectangle ({passive_x+0.18:.2f},1.98);

  {released_arrow}
  {hx_arrow}
  {hy_arrow}

  \node[font=\scriptsize, anchor=west] at (0.8,4.25) {{Festlager: Stützstelle {fest_idx}}};
  \node[font=\scriptsize, anchor=west] at (0.8,3.95) {{Gleitlager: Stützstelle {gleit_idx}, Gleitrichtung {latex_escape(support_action.slide_direction)}}};
  \node[font=\scriptsize, anchor=west] at (0.8,3.65) {{Lokale Stützstellenlast: $R_{{h,Ed}}={support_action.total_resultant_Ed:.2f}\,\mathrm{{kN}}$}};
\end{{tikzpicture}}
"""


def render_support_side_sketch(
    anchorage: AnchorageInput | None,
    support_action: SupportAction | None,
) -> str:
    if anchorage is None or support_action is None:
        return r"""
\textbf{Skizze in Seitenansicht}\\
\HINWEISstatus\ Keine Seitenansicht ableitbar, da Exzentrizitätsdaten fehlen.
"""

    wdvs = float(anchorage.wdvs_mm or 0.0)
    spalt = float(anchorage.spalt_mm or 0.0)
    bracket = float(anchorage.bracket_offset_mm or 0.0)
    anchor_plane = float(anchorage.anchor_plane_offset_mm or 0.0)
    e_local = float(support_action.local_eccentricity_mm or 0.0)
    e_platform = float(support_action.platform_eccentricity_mm or 0.0)
    x0 = 0.0
    x1 = x0 + 1.2
    scale = 0.011
    x2 = x1 + wdvs * scale
    x3 = x2 + spalt * scale
    x4 = x3 + bracket * scale
    x5 = x4 + anchor_plane * scale
    x_platform = x5 + 1.2
    result_y = 2.55

    wdvs_dim = rf"\draw[<->] ({x1:.2f},0.55) -- ({x2:.2f},0.55) node[midway, below, fill=white, inner sep=1pt] {{\scriptsize WDVS {wdvs:.0f}}};" if wdvs > 0 else ""
    spalt_dim = rf"\draw[<->] ({x2:.2f},0.95) -- ({x3:.2f},0.95) node[midway, below, fill=white, inner sep=1pt] {{\scriptsize Spalt {spalt:.0f}}};" if spalt > 0 else ""
    bracket_dim = rf"\draw[<->] ({x3:.2f},1.35) -- ({x4:.2f},1.35) node[midway, below, fill=white, inner sep=1pt] {{\scriptsize Konsole {bracket:.0f}}};" if bracket > 0 else ""
    plane_dim = rf"\draw[<->] ({x4:.2f},1.75) -- ({x5:.2f},1.75) node[midway, below, fill=white, inner sep=1pt] {{\scriptsize Ankerachse {anchor_plane:.0f}}};" if anchor_plane > 0 else ""

    return rf"""
\textbf{{Skizze in Seitenansicht}}\\[2pt]
\begin{{tikzpicture}}[x=1cm,y=1cm]
  \fill[gray!18] ({x0:.2f},0.4) rectangle ({x1:.2f},4.1);
  \draw[gray!70] ({x0:.2f},0.4) rectangle ({x1:.2f},4.1);
  \node[font=\scriptsize, rotate=90] at ({(x0+x1)/2:.2f},2.25) {{Untergrund}};
  \fill[gray!8] ({x1:.2f},0.4) rectangle ({x2:.2f},4.1);
  \draw[gray!55] ({x1:.2f},0.4) rectangle ({x2:.2f},4.1);
  \node[font=\scriptsize, rotate=90] at ({(x1+x2)/2:.2f},2.25) {{WDVS}};
  \draw[dashed] ({x2:.2f},0.4) -- ({x2:.2f},4.1);
  \draw[dashed] ({x3:.2f},0.4) -- ({x3:.2f},4.1);
  \draw[SPAccent, line width=0.8pt] ({x3:.2f},2.0) -- ({x4:.2f},2.0) -- ({x_platform:.2f},2.0);
  \draw[SPAccent, line width=1.0pt] ({x5:.2f},1.2) -- ({x5:.2f},2.8);
  \filldraw[fill=white, draw=SPAccent, line width=0.5pt] ({x5:.2f},1.55) circle (0.10);
  \filldraw[fill=white, draw=SPAccent, line width=0.5pt] ({x5:.2f},2.45) circle (0.10);
  \node[font=\scriptsize, anchor=west] at ({x_platform+0.1:.2f},2.1) {{Plattform / Profil}};
  \node[font=\scriptsize, anchor=west] at ({x5+0.1:.2f},2.75) {{Ankerachse}};

  {wdvs_dim}
  {spalt_dim}
  {bracket_dim}
  {plane_dim}
  \draw[<->] ({x1:.2f},3.55) -- ({x5:.2f},3.55) node[midway, above, fill=white, inner sep=1pt] {{\scriptsize $e_{{local}}={e_local:.0f}\,\mathrm{{mm}}$}};
  \draw[<->] ({x5:.2f},4.05) -- ({x_platform:.2f},4.05) node[midway, above, fill=white, inner sep=1pt] {{\scriptsize $e_{{platform}}={e_platform:.0f}\,\mathrm{{mm}}$}};

  \draw[->, thick] ({x_platform+0.8:.2f},{result_y:.2f}) -- ({x_platform+0.1:.2f},{result_y:.2f}) node[midway, above, fill=white, inner sep=1pt] {{\scriptsize $R_{{h,Ed}}={support_action.total_resultant_Ed:.2f}$}};
  \draw[->, thick] ({x_platform-0.1:.2f},3.15) arc[start angle=45, end angle=-245, radius=0.45] node[pos=0.1, right] {{\scriptsize $M_{{add,Ed}}={support_action.additional_moment_Ed:.2f}$}};
  \node[font=\scriptsize, anchor=west] at (0.1,4.45) {{Stützstelle {support_action.support_index} als {latex_escape(support_action.support_role)}}};
\end{{tikzpicture}}
"""


def render_support_kinematics_figures(
    anchorage: AnchorageInput | None,
    support_action: SupportAction | None,
    actions: ConnectionActions | None = None,
) -> str:
    return (
        r"""
\subsection*{Skizzen Festlager / Gleitlager und Exzentrizität}
\begin{figure}[H]
\centering
"""
        + render_support_plan_sketch(anchorage, support_action, actions)
        + r"""
\end{figure}

\begin{figure}[H]
\centering
"""
        + render_support_side_sketch(anchorage, support_action)
        + r"""
\end{figure}
\noindent\textit{Skizzenhinweis:} Schematische Darstellung des kinematischen Modells. Sie dient der Lastabtragung und Nachvollziehbarkeit, nicht der Werk- oder Montageplanung.
"""
    )
