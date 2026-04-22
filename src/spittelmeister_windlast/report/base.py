from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from ..utils.latex_escape import latex_escape

MODUS_STATIK = "Statische Berechnung"
MODUS_GUTACHTEN = "Gutachtliche Stellungnahme"


@dataclass
class ProtokolHeader:
    projekt_nr: str = "2026-WB-001"
    projekt_bez: str = "Windnachweis Balkonanschluss"
    strasse: str = ""
    ort: str = ""
    bauherr: str = ""
    bearbeiter: str = ""
    geprueft: str = ""
    datum: str = ""
    bauteil: str = "Balkonanschluss"
    norm: str = "DIN EN 1991-1-4 / NA"
    revision: str = "0"
    modus: str = MODUS_STATIK

    def __post_init__(self) -> None:
        if not self.datum:
            self.datum = date.today().strftime("%d.%m.%Y")


class PreambleStyle(str, Enum):
    COLOR = "color"
    COMBINED_NEUTRAL = "combined_neutral"


def _sym_legend(symbols: list[tuple[str, str, str]]) -> str:
    if not symbols:
        return ""
    rows = []
    for sym, desc, unit in symbols:
        rows.append(rf"${sym}$ & {latex_escape(desc)} & [{latex_escape(unit)}] \\")
    body = "\n".join(rows)
    return rf"""
\begin{{center}}
\small
\begin{{tabular}}{{lll}}
{body}
\end{{tabular}}
\end{{center}}
"""


def build_preamble(*, style: str = PreambleStyle.COLOR.value, title: str = MODUS_STATIK) -> str:
    is_neutral = style == PreambleStyle.COMBINED_NEUTRAL.value
    ok_macro = (
        r"\newcommand{\okbox}[1]{\colorbox{gray!12}{\parbox{\dimexpr\linewidth-2\fboxsep}{\textbf{#1}}}}"
        if is_neutral
        else r"\newcommand{\okbox}[1]{\colorbox{green!10}{\parbox{\dimexpr\linewidth-2\fboxsep}{\textbf{#1}}}}"
    )
    fail_macro = (
        r"\newcommand{\failbox}[1]{\colorbox{gray!12}{\parbox{\dimexpr\linewidth-2\fboxsep}{\textbf{#1}}}}"
        if is_neutral
        else r"\newcommand{\failbox}[1]{\colorbox{red!12}{\parbox{\dimexpr\linewidth-2\fboxsep}{\color{red!70!black}\textbf{#1}}}}"
    )
    result_color = "gray" if is_neutral else "SPAccent"
    return rf"""\documentclass[a4paper,10pt]{{article}}
\usepackage[a4paper,left=22mm,right=22mm,top=28mm,bottom=22mm]{{geometry}}
\usepackage[T1]{{fontenc}}
\usepackage[utf8]{{inputenc}}
\usepackage[ngerman]{{babel}}
\usepackage{{lmodern}}
\renewcommand{{\familydefault}}{{\sfdefault}}
\usepackage{{amsmath}}
\usepackage{{booktabs}}
\usepackage{{tabularx}}
\usepackage{{xcolor}}
\usepackage{{graphicx}}
\usepackage{{float}}
\usepackage{{tikz}}
\usepackage{{fancyhdr}}
\usepackage{{lastpage}}
\usepackage{{parskip}}
\usepackage{{needspace}}
\usepackage[hidelinks]{{hyperref}}
\definecolor{{SPAccent}}{{RGB}}{{30,80,140}}
\definecolor{{SPLineGray}}{{HTML}}{{C9C9C9}}
\definecolor{{resultbg}}{{RGB}}{{230,240,255}}
\newcommand{{\OK}}{{\textbf{{OK}}}}
\newcommand{{\IO}}{{\OK}}
\newcommand{{\NIO}}{{\textbf{{NICHT ERFÜLLT}}}}
\newcommand{{\IOstatus}}{{\textbf{{erfüllt}}}}
\newcommand{{\NIOstatus}}{{\textbf{{nicht erfüllt}}}}
\newcommand{{\HINWEISstatus}}{{\textbf{{Hinweis / offen}}}}
{ok_macro}
{fail_macro}
\newcommand{{\resultbox}}[1]{{\fcolorbox{{{result_color}}}{{gray!8}}{{\parbox{{0.97\linewidth}}{{#1}}}}}}
\newenvironment{{mandateblock}}{{\paragraph{{Aufgabenstellung}}}}{{}}
\newenvironment{{scopeblock}}{{\paragraph{{Untersuchungsumfang}}}}{{}}
\newenvironment{{verificationmodule}}[1]{{\section{{#1}}}}{{}}
\newenvironment{{conclusionblock}}{{\paragraph{{Zusammenfassung}}}}{{}}
\pagestyle{{fancy}}
\fancyhf{{}}
\lhead{{\footnotesize Spittelmeister GmbH}}
\rhead{{\footnotesize {latex_escape(title)}}}
\rfoot{{\footnotesize Seite \thepage\ von \pageref{{LastPage}}}}
"""


def build_document(title: str, body: str, *, style: str = PreambleStyle.COLOR.value) -> str:
    return build_preamble(style=style, title=title) + "\n\\begin{document}\n" + body + "\n\\end{document}\n"
