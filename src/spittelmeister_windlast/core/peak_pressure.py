"""Boeengeschwindigkeitsdruck q_p(z) nach DIN EN 1991-1-4/NA:2010-12, NA.B.3.

Ausfuehrlicher Formelansatz fuer Binnenland, Kuesten und Nordseeinseln.
Logisch 1:1 aus `windlast_generator.berechne_qp_ausfuehrlich` uebernommen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..daten import qb0_table

Gelaende = Literal["binnen", "kueste", "nordsee"]


@dataclass
class PeakPressureResult:
    """Ergebnis der qp(z)-Berechnung inkl. LaTeX-Fragmente fuer den Report."""
    qb0: float
    qp: float
    faktor: float
    formel: str
    auswertung: str
    abschnitt: str
    verfahren: str
    gelaende_label: str
    normstelle: str


def get_hoehenstufe(h: float) -> int | None:
    """Vereinfachter Hoehenstufen-Index (Tabellenansatz, historisch)."""
    if h <= 10.0:
        return 0
    if h <= 18.0:
        return 1
    if h <= 25.0:
        return 2
    return None


_VERFAHREN = "Ausfuehrlicher Formelansatz nach DIN EN 1991-1-4/NA:2010-12"


def _binnen(z: float, qb0: float) -> PeakPressureResult:
    if z <= 7.0:
        qp = 1.5 * qb0
        faktor = 1.5
        formel = r"q_p(h) &= 1{,}5 \cdot q_{b,0}"
        auswertung = rf"q_p(h) &= 1{{,}}5 \cdot {qb0:.2f} = \mathbf{{{qp:.3f}~\mathrm{{kN/m^2}}}}"
        abschnitt = r"fuer Gelaendekategorie II / III und $h \leq 7~\mathrm{m}$"
        normstelle = "NA.B.1"
    elif z <= 50.0:
        faktor = 1.7 * (z / 10.0) ** 0.37
        qp = faktor * qb0
        formel = r"q_p(h) &= 1{,}7 \cdot q_{b,0} \cdot \left(\frac{h}{10}\right)^{0{,}37}"
        auswertung = rf"       &= {faktor:.3f} \cdot q_{{b,0}} = \mathbf{{{qp:.3f}~\mathrm{{kN/m^2}}}}"
        abschnitt = r"fuer Gelaendekategorie II / III und $7 < h \leq 50~\mathrm{m}$"
        normstelle = "NA.B.2"
    else:
        faktor = 2.1 * (z / 10.0) ** 0.24
        qp = faktor * qb0
        formel = r"q_p(h) &= 2{,}1 \cdot q_{b,0} \cdot \left(\frac{h}{10}\right)^{0{,}24}"
        auswertung = rf"       &= {faktor:.3f} \cdot q_{{b,0}} = \mathbf{{{qp:.3f}~\mathrm{{kN/m^2}}}}"
        abschnitt = r"fuer Gelaendekategorie II / III und $50 < h \leq 300~\mathrm{m}$"
        normstelle = "NA.B.3"
    return PeakPressureResult(
        qb0=qb0, qp=qp, faktor=faktor, formel=formel, auswertung=auswertung,
        abschnitt=abschnitt, verfahren=_VERFAHREN,
        gelaende_label="II und III (Binnenland)", normstelle=normstelle,
    )


def _kueste(z: float, qb0: float) -> PeakPressureResult:
    if z <= 4.0:
        qp = 1.8 * qb0
        faktor = 1.8
        formel = r"q_p(h) &= 1{,}8 \cdot q_{b,0}"
        auswertung = rf"q_p(h) &= 1{{,}}8 \cdot {qb0:.2f} = \mathbf{{{qp:.3f}~\mathrm{{kN/m^2}}}}"
        abschnitt = r"fuer kuestennahe Gebiete / Ostseeinseln und $h \leq 4~\mathrm{m}$"
        normstelle = "NA.B.4"
    elif z <= 50.0:
        faktor = 2.3 * (z / 10.0) ** 0.27
        qp = faktor * qb0
        formel = r"q_p(h) &= 2{,}3 \cdot q_{b,0} \cdot \left(\frac{h}{10}\right)^{0{,}27}"
        auswertung = rf"       &= {faktor:.3f} \cdot q_{{b,0}} = \mathbf{{{qp:.3f}~\mathrm{{kN/m^2}}}}"
        abschnitt = r"fuer kuestennahe Gebiete / Ostseeinseln und $4 < h \leq 50~\mathrm{m}$"
        normstelle = "NA.B.5"
    else:
        faktor = 2.6 * (z / 10.0) ** 0.19
        qp = faktor * qb0
        formel = r"q_p(h) &= 2{,}6 \cdot q_{b,0} \cdot \left(\frac{h}{10}\right)^{0{,}19}"
        auswertung = rf"       &= {faktor:.3f} \cdot q_{{b,0}} = \mathbf{{{qp:.3f}~\mathrm{{kN/m^2}}}}"
        abschnitt = r"fuer kuestennahe Gebiete / Ostseeinseln und $50 < h \leq 300~\mathrm{m}$"
        normstelle = "NA.B.6"
    return PeakPressureResult(
        qb0=qb0, qp=qp, faktor=faktor, formel=formel, auswertung=auswertung,
        abschnitt=abschnitt, verfahren=_VERFAHREN,
        gelaende_label="I und II (kuestennah / Ostseeinseln)", normstelle=normstelle,
    )


def _nordsee(z: float, qb0: float) -> PeakPressureResult:
    if z <= 2.0:
        qp = 1.1
        faktor = qp / qb0
        formel = r"q_p(h) &= 1{,}1~\mathrm{kN/m^2}"
        auswertung = rf"q_p(h) &= \mathbf{{{qp:.3f}~\mathrm{{kN/m^2}}}}"
        abschnitt = r"fuer Nordseeinseln und $h \leq 2~\mathrm{m}$"
        normstelle = "NA.B.7"
    else:
        qp = 1.05 * (z / 10.0) ** 0.19
        faktor = qp / qb0
        formel = r"q_p(h) &= 1{,}05 \cdot \left(\frac{h}{10}\right)^{0{,}19}~\mathrm{kN/m^2}"
        auswertung = rf"       &= \mathbf{{{qp:.3f}~\mathrm{{kN/m^2}}}}"
        abschnitt = r"fuer Nordseeinseln und $2 < h \leq 300~\mathrm{m}$"
        normstelle = "NA.B.8"
    return PeakPressureResult(
        qb0=qb0, qp=qp, faktor=faktor, formel=formel, auswertung=auswertung,
        abschnitt=abschnitt, verfahren=_VERFAHREN,
        gelaende_label="I (Nordseeinseln)", normstelle=normstelle,
    )


def berechne_qp(z: float, windzone: int, gelaende: Gelaende) -> PeakPressureResult:
    """Ausfuehrlicher Formelansatz nach DIN EN 1991-1-4/NA:2010-12, NA.B.3.3.

    Args:
        z:         Hoehe ueber Gelaende [m], z <= 300 m
        windzone:  1..4
        gelaende:  "binnen" | "kueste" | "nordsee"

    Returns:
        PeakPressureResult mit qp, qb0 und LaTeX-Fragmenten.

    Raises:
        ValueError: Bei ungueltiger Hoehe, Windzone oder Gelaendekategorie.
    """
    if z > 300.0:
        raise ValueError(f"Hoehe z={z} m > 300 m: qp-Ansatz nach NA.B.3.3 nicht anwendbar.")

    table = qb0_table()
    if windzone not in table:
        raise ValueError(f"Unbekannte Windzone: {windzone} (erlaubt: {sorted(table)})")
    qb0 = table[windzone]

    if gelaende == "binnen":
        return _binnen(z, qb0)
    if gelaende == "kueste":
        return _kueste(z, qb0)
    if gelaende == "nordsee":
        return _nordsee(z, qb0)
    raise ValueError(f"Unbekannte Gelaendekategorie: {gelaende}")


# Legacy-Alias fuer Kompatibilitaet mit dem flachen Vorgaenger-Modul.
# Gibt ein dict zurueck wie die alte Funktion, statt eines dataclass.
def berechne_qp_ausfuehrlich(z: float, windzone: int, gelaende: str) -> dict:
    """Legacy-API: gibt ein dict wie die urspruengliche Implementation."""
    r = berechne_qp(z, windzone, gelaende)  # type: ignore[arg-type]
    return {
        "qb0": r.qb0, "qp": r.qp, "faktor": r.faktor, "formel": r.formel,
        "auswertung": r.auswertung, "abschnitt": r.abschnitt, "verfahren": r.verfahren,
        "gelaende_label": r.gelaende_label, "normstelle": r.normstelle,
    }


__all__ = ["berechne_qp", "PeakPressureResult", "get_hoehenstufe", "berechne_qp_ausfuehrlich"]
