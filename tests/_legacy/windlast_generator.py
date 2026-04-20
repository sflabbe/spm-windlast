#!/usr/bin/env python3
"""
Windlast-Generator — DIN EN 1991-1-4 / NA:2010-12
Spittelmeister GmbH, Statik-Abteilung

Überarbeitet nach Excel-Vorlage 27.02.2026:
- detaillierter Richtungsansatz für Balkonabschlüsse
- getrennte Betrachtung von Front- und Seitenflächen
- Interpolation der Außendruckbeiwerte A / D / E wie in der Vorlage
- maßgebend ist die größte resultierende Linienlast
"""

import subprocess
import os
import re
import tempfile
from dataclasses import dataclass, field
from typing import Optional
from datetime import date

QB0_TABLE = {
    1: 0.32,
    2: 0.39,
    3: 0.47,
    4: 0.56,
}



def interpolate_linear(x: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """Lineare Interpolation / Extrapolation exakt wie in der Excel-Vorlage."""
    if abs(x2 - x1) < 1e-12:
        raise ValueError("Interpolation nicht möglich: identische x-Stützstellen.")
    return ((y2 - y1) / (x2 - x1)) * (x - x1) + y1


def interpolate_cpe_excel(zone: str, h_d: float) -> float:
    """Interpolation exakt nach den Excel-Formeln der Vorlage 27.02.2026 / Tafel 3.35.

    Wichtig: Die Vorlage klemmt nicht überall ab, sondern extrapoliert in einzelnen Bereichen.
    Genau dieses Verhalten wird hier nachgebildet.
    """
    if zone == "D":
        # Excel: IF(h_d > 1; 0.8; lineare Funktion zwischen (0.25, 0.7) und (1.0, 0.8))
        return 0.8 if h_d > 1.0 else interpolate_linear(h_d, 0.25, 0.7, 1.0, 0.8)

    if zone == "E":
        # Excel: IF(h_d > 1; -0.5; lineare Funktion zwischen (0.25, -0.3) und (1.0, -0.5))
        return -0.5 if h_d > 1.0 else interpolate_linear(h_d, 0.25, -0.3, 1.0, -0.5)

    if zone == "A":
        # Excel: IF(h_d > 5; -1.4; lineare Funktion zwischen (1.0, -1.2) und (5.0, -1.4))
        return -1.4 if h_d > 5.0 else interpolate_linear(h_d, 1.0, -1.2, 5.0, -1.4)

    raise ValueError(f"Unbekannte Zone: {zone}")


def get_hoehenstufe(h: float) -> int:
    if h <= 10.0:
        return 0
    elif h <= 18.0:
        return 1
    elif h <= 25.0:
        return 2
    else:
        return None


def berechne_qp_ausfuehrlich(z: float, windzone: int, gelaende: str):
    """Ausführlicher Ansatz nach DIN EN 1991-1-4/NA:2010-12, NA.B.3.3."""
    if z > 300.0:
        raise ValueError(f"Höhe z={z} m > 300 m: qp-Ansatz nach NA.B.3.3 nicht anwendbar.")

    qb0 = QB0_TABLE[windzone]

    if gelaende == "binnen":
        if z <= 7.0:
            qp = 1.5 * qb0
            faktor = 1.5
            formel = r"q_p(h) &= 1{,}5 \cdot q_{b,0}"
            auswertung = rf"q_p(h) &= 1{{,}}5 \cdot {qb0:.2f} = \mathbf{{{qp:.3f}~\mathrm{{kN/m^2}}}}"
            abschnitt = r"für Geländekategorie II / III und $h \leq 7~\mathrm{m}$"
            normstelle = "NA.B.1"
        elif z <= 50.0:
            faktor = 1.7 * (z / 10.0) ** 0.37
            qp = faktor * qb0
            formel = r"q_p(h) &= 1{,}7 \cdot q_{b,0} \cdot \left(\frac{h}{10}\right)^{0{,}37}"
            auswertung = rf"       &= {faktor:.3f} \cdot q_{{b,0}} = \mathbf{{{qp:.3f}~\mathrm{{kN/m^2}}}}"
            abschnitt = r"für Geländekategorie II / III und $7 < h \leq 50~\mathrm{m}$"
            normstelle = "NA.B.2"
        else:
            faktor = 2.1 * (z / 10.0) ** 0.24
            qp = faktor * qb0
            formel = r"q_p(h) &= 2{,}1 \cdot q_{b,0} \cdot \left(\frac{h}{10}\right)^{0{,}24}"
            auswertung = rf"       &= {faktor:.3f} \cdot q_{{b,0}} = \mathbf{{{qp:.3f}~\mathrm{{kN/m^2}}}}"
            abschnitt = r"für Geländekategorie II / III und $50 < h \leq 300~\mathrm{m}$"
            normstelle = "NA.B.3"
        return {
            "qb0": qb0, "qp": qp, "faktor": faktor, "formel": formel,
            "auswertung": auswertung, "abschnitt": abschnitt, "verfahren": "Ausführlicher Formelansatz nach DIN EN 1991-1-4/NA:2010-12",
            "gelaende_label": "II und III (Binnenland)", "normstelle": normstelle,
        }

    if gelaende == "kueste":
        if z <= 4.0:
            qp = 1.8 * qb0
            faktor = 1.8
            formel = r"q_p(h) &= 1{,}8 \cdot q_{b,0}"
            auswertung = rf"q_p(h) &= 1{{,}}8 \cdot {qb0:.2f} = \mathbf{{{qp:.3f}~\mathrm{{kN/m^2}}}}"
            abschnitt = r"für küstennahe Gebiete / Ostseeinseln und $h \leq 4~\mathrm{m}$"
            normstelle = "NA.B.4"
        elif z <= 50.0:
            faktor = 2.3 * (z / 10.0) ** 0.27
            qp = faktor * qb0
            formel = r"q_p(h) &= 2{,}3 \cdot q_{b,0} \cdot \left(\frac{h}{10}\right)^{0{,}27}"
            auswertung = rf"       &= {faktor:.3f} \cdot q_{{b,0}} = \mathbf{{{qp:.3f}~\mathrm{{kN/m^2}}}}"
            abschnitt = r"für küstennahe Gebiete / Ostseeinseln und $4 < h \leq 50~\mathrm{m}$"
            normstelle = "NA.B.5"
        else:
            faktor = 2.6 * (z / 10.0) ** 0.19
            qp = faktor * qb0
            formel = r"q_p(h) &= 2{,}6 \cdot q_{b,0} \cdot \left(\frac{h}{10}\right)^{0{,}19}"
            auswertung = rf"       &= {faktor:.3f} \cdot q_{{b,0}} = \mathbf{{{qp:.3f}~\mathrm{{kN/m^2}}}}"
            abschnitt = r"für küstennahe Gebiete / Ostseeinseln und $50 < h \leq 300~\mathrm{m}$"
            normstelle = "NA.B.6"
        return {
            "qb0": qb0, "qp": qp, "faktor": faktor, "formel": formel,
            "auswertung": auswertung, "abschnitt": abschnitt, "verfahren": "Ausführlicher Formelansatz nach DIN EN 1991-1-4/NA:2010-12",
            "gelaende_label": "I und II (küstennah / Ostseeinseln)", "normstelle": normstelle,
        }

    if gelaende == "nordsee":
        if z <= 2.0:
            qp = 1.1
            faktor = qp / qb0
            formel = r"q_p(h) &= 1{,}1~\mathrm{kN/m^2}"
            auswertung = rf"q_p(h) &= \mathbf{{{qp:.3f}~\mathrm{{kN/m^2}}}}"
            abschnitt = r"für Nordseeinseln und $h \leq 2~\mathrm{m}$"
            normstelle = "NA.B.7"
        else:
            qp = 1.05 * (z / 10.0) ** 0.19
            faktor = qp / qb0
            formel = r"q_p(h) &= 1{,}05 \cdot \left(\frac{h}{10}\right)^{0{,}19}~\mathrm{kN/m^2}"
            auswertung = rf"       &= \mathbf{{{qp:.3f}~\mathrm{{kN/m^2}}}}"
            abschnitt = r"für Nordseeinseln und $2 < h \leq 300~\mathrm{m}$"
            normstelle = "NA.B.8"
        return {
            "qb0": qb0, "qp": qp, "faktor": faktor, "formel": formel,
            "auswertung": auswertung, "abschnitt": abschnitt, "verfahren": "Ausführlicher Formelansatz nach DIN EN 1991-1-4/NA:2010-12",
            "gelaende_label": "I (Nordseeinseln)", "normstelle": normstelle,
        }

    raise ValueError(f"Unbekannte Geländekategorie: {gelaende}")


def latex_escape(text: str) -> str:
    if text is None:
        return ""
    text = str(text)
    _map = {
        '\\': r'\textbackslash{}',
        '&':  r'\&',
        '%':  r'\%',
        '$':  r'\$',
        '#':  r'\#',
        '_':  r'\_',
        '{':  r'\{',
        '}':  r'\}',
        '~':  r'\textasciitilde{}',
        '^':  r'\textasciicircum{}',
    }
    return re.sub(r'[\\&%$#_{}\~\^]', lambda m: _map[m.group()], text)


@dataclass
class Geometrie:
    h: float
    d: float
    b: float
    z_balkon: float
    e_balkon: float
    h_abschluss: float
    s_verankerung: float

    @property
    def h_d(self) -> float:
        return max(self.h / self.d, self.h / self.b)

    @property
    def A_ref(self) -> float:
        return self.s_verankerung * self.h_abschluss

    @property
    def A_w_side(self) -> float:
        return self.e_balkon * self.h_abschluss

    @property
    def A_w_front(self) -> float:
        return self.s_verankerung * self.h_abschluss


@dataclass
class Standort:
    bezeichnung: str
    windzone: int
    gelaende: str
    hoehe_uNN: float


@dataclass
class Projekt:
    bezeichnung: str
    nummer: str
    bearbeiter: str
    datum: str = field(default_factory=lambda: date.today().strftime("%d.%m.%Y"))


@dataclass
class Ergebnisse:
    qb0: float
    qp: float
    qp_faktor: float
    qp_formel: str
    qp_auswertung: str
    qp_abschnitt: str
    qp_verfahren: str
    qp_normstelle: str
    gelaende_label: str
    cscd: float
    h_d: float
    A_ref: float
    A_w_side: float
    A_w_front: float
    cpe10_D: float
    cpe10_E: float
    cpe10_A: float
    we_side_pressure: float
    we_side_suction: float
    we_front_suction: float
    q_side_pressure: float
    q_side_suction: float
    q_front_suction: float
    wk_sog: float
    wk_druck: float
    wk_massgebend: float
    lastfall_massgebend: str
    qhk: float
    Hk: float
    Mk: float
    hoehenstufe: int
    cscd_begruendung: str
    methodik: str
    cp_net_sog: float
    cp_net_druck: float
    zone_massgebend: str
    cpi_unguenstig_sog: float
    cpi_unguenstig_druck: float


class WindlastBerechnung:
    def __init__(self, projekt: Projekt, standort: Standort, geo: Geometrie):
        self.projekt = projekt
        self.standort = standort
        self.geo = geo
        self.erg: Optional[Ergebnisse] = None

    def berechnen(self) -> Ergebnisse:
        geo = self.geo
        st = self.standort

        qp_info = berechne_qp_ausfuehrlich(geo.h, st.windzone, st.gelaende)
        qp = qp_info["qp"]
        cscd = 1.0
        if geo.h <= 25.0:
            cscd_begruendung = (
                r"$c_{s}c_{d} = 1{,}0$ nach NA.C.2(4): "
                f"Gebäudehöhe $h = {geo.h:.2f}~\\mathrm{{m}} \\leq 25~\\mathrm{{m}}$, "
                "keine Schwingungsanfälligkeit."
            )
        elif geo.h <= 100.0 and geo.h <= 4 * geo.d:
            cscd_begruendung = (
                r"$c_{s}c_{d} = 1{,}0$ nach EN~1991-1-4 Tabelle~6.1: "
                f"$h = {geo.h:.2f}~\\mathrm{{m}} \\leq 100~\\mathrm{{m}}$ und "
                f"$h = {geo.h:.2f}~\\mathrm{{m}} \\leq 4d = {4*geo.d:.2f}~\\mathrm{{m}}$."
            )
        else:
            raise ValueError("cscd > 1,0 — gesonderter Nachweis erforderlich.")

        h_d = geo.h_d
        cpe10_D = interpolate_cpe_excel("D", h_d)
        cpe10_E = interpolate_cpe_excel("E", h_d)
        cpe10_A = interpolate_cpe_excel("A", h_d)

        # Vorzeichen wie in der Excel-Vorlage beibehalten
        we_side_pressure = qp * cscd * cpe10_D
        we_side_suction = qp * cscd * cpe10_E
        we_front_suction = qp * cscd * cpe10_A

        q_side_pressure = we_side_pressure * geo.h_abschluss
        q_side_suction = we_side_suction * geo.h_abschluss
        q_front_suction = we_front_suction * geo.h_abschluss

        candidates = [
            ("Seite Druck (Bereich D)", q_side_pressure, "D"),
            ("Seite Sog (Bereich E)", q_side_suction, "E"),
            ("Front Sog (Bereich A)", q_front_suction, "A"),
        ]
        lastfall_massgebend, qhk_signed, zone_massgebend = max(candidates, key=lambda x: abs(x[1]))
        qhk = abs(qhk_signed)
        wk_massgebend = abs(qhk_signed / geo.h_abschluss)
        Hk = qhk * geo.s_verankerung
        Mk = Hk * (geo.h_abschluss / 2.0)

        self.erg = Ergebnisse(
            qb0=qp_info["qb0"],
            qp=qp,
            qp_faktor=qp_info["faktor"],
            qp_formel=qp_info["formel"],
            qp_auswertung=qp_info["auswertung"],
            qp_abschnitt=qp_info["abschnitt"],
            qp_verfahren=qp_info["verfahren"],
            qp_normstelle=qp_info["normstelle"],
            gelaende_label=qp_info["gelaende_label"],
            cscd=cscd,
            h_d=h_d,
            A_ref=geo.A_ref,
            A_w_side=geo.A_w_side,
            A_w_front=geo.A_w_front,
            cpe10_D=cpe10_D,
            cpe10_E=cpe10_E,
            cpe10_A=cpe10_A,
            we_side_pressure=we_side_pressure,
            we_side_suction=we_side_suction,
            we_front_suction=we_front_suction,
            q_side_pressure=q_side_pressure,
            q_side_suction=q_side_suction,
            q_front_suction=q_front_suction,
            wk_sog=we_front_suction,
            wk_druck=we_side_pressure,
            wk_massgebend=wk_massgebend,
            lastfall_massgebend=lastfall_massgebend,
            qhk=qhk,
            Hk=Hk,
            Mk=Mk,
            hoehenstufe=0,
            cscd_begruendung=cscd_begruendung,
            methodik="Detaillierter Richtungsansatz nach Excel-Vorlage 27.02.2026",
            cp_net_sog=cpe10_A,
            cp_net_druck=cpe10_D,
            zone_massgebend=zone_massgebend,
            cpi_unguenstig_sog=0.0,
            cpi_unguenstig_druck=0.0,
        )
        return self.erg

    def _latex(self) -> str:
        e = self.erg
        p = self.projekt
        st = self.standort
        geo = self.geo

        hoehen_labels = ["$h \\leq 10~\\mathrm{m}$", "$10 < h \\leq 18~\\mathrm{m}$", "$18 < h \\leq 25~\\mathrm{m}$"]
        hs_label = hoehen_labels[e.hoehenstufe]
        gelaende_label = "Binnenland" if st.gelaende == "binnen" else "Küste"

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
\textbf{{Standort:}} & {latex_escape(st.bezeichnung)} & \textbf{{Höhe ü.\ NN:}} & {st.hoehe_uNN:.0f}~m \\
\end{{tabularx}}
\vspace{{6pt}}
{{\color{{spittel}}\rule{{\linewidth}}{{0.6pt}}}}

\section*{{1 \quad Eingangsgrößen}}
\begin{{tabular}}{{@{{}}lll@{{}}}}
\toprule
\textbf{{Größe}} & \textbf{{Wert}} & \textbf{{Bemerkung}} \\
\midrule
Windzone & WZ~{st.windzone} & DIN EN 1991-1-4/NA, Anhang NA.A \\
Geländekategorie & {gelaende_label} & Excel 27.02.2026 / NA.B.3 \\
Gebäudehöhe & $h = {geo.h:.2f}~\mathrm{{m}}$ & maßgebend für $q_p$ \\\
Gebäudetiefe & $d = {geo.d:.2f}~\mathrm{{m}}$ & Windrichtung 1 \\
Gebäudebreite & $b = {geo.b:.2f}~\mathrm{{m}}$ & Windrichtung 2 \\
Höhe OK Balkonabschluss & $z_e = {geo.z_balkon:.2f}~\mathrm{{m}}$ & Geometrie Balkon \\
Balkonausladung & $T = {geo.e_balkon:.3f}~\mathrm{{m}}$ & Seitenfläche \\
Höhe Abschlusselement & $h_w = {geo.h_abschluss:.2f}~\mathrm{{m}}$ & \\
Achsabstand Verankerungen & $B = {geo.s_verankerung:.2f}~\mathrm{{m}}$ & Frontfläche \\
\bottomrule
\end{{tabular}}

\section*{{2 \quad Böengeschwindigkeitsdruck $q_p$}}
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

Angesetzt werden die Außendruckbeiwerte analog Excel-Vorlage 27.02.2026 / Tafel 3.35:
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

\section*{{4 \quad Flächen und Linienlasten}}
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
Front Sog (A) & {e.we_front_suction:.2f} & {e.q_front_suction:.2f} & prüfen \\
\bottomrule
\end{{tabular}}
\end{{center}}

\section*{{5 \quad Maßgebende Schnittgrößen}}
Maßgebender Lastfall: \textbf{{{e.lastfall_massgebend}}}
\begin{{align*}}
q_{{h,k}} &= \mathbf{{{e.qhk:.2f}~\mathrm{{kN/m}}}} \\
H_k &= q_{{h,k}} \cdot B = {e.qhk:.2f} \cdot {geo.s_verankerung:.2f} = \mathbf{{{e.Hk:.2f}~\mathrm{{kN}}}} \\
M_{{k,Fußpunkt}} &= H_k \cdot \frac{{h_w}}{{2}} = {e.Hk:.2f} \cdot {geo.h_abschluss/2:.3f} = \mathbf{{{e.Mk:.2f}~\mathrm{{kNm}}}}
\end{{align*}}

\vspace{{8pt}}
\begin{{center}}
{{\color{{spittel}}\bfseries\large Zusammenfassung Ergebnisse}}\\[6pt]
\colorbox{{resultbg}}{{%
\begin{{tabular}}{{lrl}}
\toprule
\textbf{{Größe}} & \textbf{{Wert}} & \textbf{{Einheit}} \\
\midrule
$q_p(h)$ & {e.qp:.3f} & $\mathrm{{kN/m^2}}$ \\
$w_k$ (maßg.) & {e.wk_massgebend:.2f} & $\mathrm{{kN/m^2}}$ \\
$q_{{h,k}}$ & {e.qhk:.2f} & $\mathrm{{kN/m}}$ \\
$H_k$ je Feld & {e.Hk:.2f} & $\mathrm{{kN}}$ \\
$M_{{k,\mathrm{{Fußpunkt}}}}$ & {e.Mk:.2f} & $\mathrm{{kNm}}$ \\
\bottomrule
\end{{tabular}}%
}}
\end{{center}}

\end{{document}}
"""

    def export_pdf(self, output_path: str) -> str:
        if self.erg is None:
            self.berechnen()
        latex_src = self._latex()
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_file = os.path.join(tmpdir, "windlast.tex")
            pdf_tmp = os.path.join(tmpdir, "windlast.pdf")
            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(latex_src)
            for _ in range(2):
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, tex_file],
                    capture_output=True, text=True, encoding="latin-1", errors="replace"
                )
            if not os.path.exists(pdf_tmp):
                raise RuntimeError("PDF-Kompilierung fehlgeschlagen.\n" + result.stdout[-2000:])
            import shutil
            shutil.copy(pdf_tmp, output_path)
        return output_path

    def print_summary(self):
        e = self.erg
        print("\n" + "=" * 55)
        print("  WINDLAST — ERGEBNISSE")
        print("=" * 55)
        print(f"  Methodik      = {e.methodik}")
        print(f"  qp            = {e.qp:.2f} kN/m²")
        print(f"  qh,k          = {e.qhk:.2f} kN/m")
        print(f"  Hk je Feld    = {e.Hk:.2f} kN")
        print(f"  Mk Fußpunkt   = {e.Mk:.2f} kNm")
        print(f"  maßgebend     = {e.lastfall_massgebend}")
        print("=" * 55 + "\n")


if __name__ == "__main__":
    projekt = Projekt(bezeichnung="Demo", nummer="2026-WB-001", bearbeiter="OpenAI")
    standort = Standort(bezeichnung="Würzburg", windzone=1, gelaende="binnen", hoehe_uNN=192.0)
    geo = Geometrie(h=13.7, d=42.5, b=42.5, z_balkon=13.7, e_balkon=1.425, h_abschluss=2.11, s_verankerung=4.63)
    wb = WindlastBerechnung(projekt, standort, geo)
    wb.berechnen()
    wb.print_summary()
