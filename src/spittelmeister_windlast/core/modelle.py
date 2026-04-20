"""Dataclasses des Berechnungskerns.

Reine Datenstrukturen - keine Logik, keine I/O, keine Seiteneffekte.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Projekt:
    """Projektmetadaten fuer Deckblatt und Kopfzeile."""
    bezeichnung: str
    nummer: str
    bearbeiter: str
    datum: str = field(default_factory=lambda: date.today().strftime("%d.%m.%Y"))


@dataclass
class Standort:
    """Standort-Eingangsgroessen fuer die Windlastermittlung.

    Attributes:
        bezeichnung: Anzeigename (z. B. "Pforzheim")
        windzone:   1..4 nach DIN EN 1991-1-4/NA Anhang NA.A
        gelaende:   "binnen" | "kueste" | "nordsee"
        hoehe_uNN:  Gelaendehoehe ueber NN in Metern
    """
    bezeichnung: str
    windzone: int
    gelaende: str
    hoehe_uNN: float


@dataclass
class Geometrie:
    """Geometrische Eingangsgroessen des Gebaeudes und Balkonabschlusses.

    Attributes:
        h:            Gebaeudehoehe [m]
        d:            Gebaeudetiefe [m] (Windrichtung 1)
        b:            Gebaeudebreite [m] (Windrichtung 2)
        z_balkon:     Hoehe OK Balkonabschluss ueber Gelaende [m]
        e_balkon:     Balkonausladung / Seitenflaechenlaenge [m]
        h_abschluss:  Hoehe des Abschlusselements [m]
        s_verankerung: Achsabstand Verankerungen [m]
        b_auflager_rand: Abstand Ecke bis Auflage b [m] fuer vereinfachte Reaktionsabschaetzung
    """
    h: float
    d: float
    b: float
    z_balkon: float
    e_balkon: float
    h_abschluss: float
    s_verankerung: float
    b_auflager_rand: float = 0.0

    @property
    def h_d(self) -> float:
        """h/d-Verhaeltnis (max aus d und b) zur Interpolation der cpe,10."""
        return max(self.h / self.d, self.h / self.b)

    @property
    def A_ref(self) -> float:
        """Bezugsflaeche je Verankerungsfeld [m^2]."""
        return self.s_verankerung * self.h_abschluss

    @property
    def A_w_side(self) -> float:
        """Seitenflaeche (Ausladung x Hoehe) [m^2]."""
        return self.e_balkon * self.h_abschluss

    @property
    def A_w_front(self) -> float:
        """Frontflaeche (Verankerungsabstand x Hoehe) [m^2]."""
        return self.s_verankerung * self.h_abschluss


@dataclass
class Ergebnisse:
    """Vollstaendiges Ergebnispaket der Windlastberechnung.

    Enthaelt die numerischen Ergebnisse sowie LaTeX-Fragmente, damit
    Report-Layer den Berechnungsweg nachvollziehbar darstellen koennen.
    """
    # Peak-Pressure
    qb0: float
    qp: float
    qp_faktor: float
    qp_formel: str
    qp_auswertung: str
    qp_abschnitt: str
    qp_verfahren: str
    qp_normstelle: str
    gelaende_label: str

    # Druckbeiwerte + Geometrie
    cscd: float
    h_d: float
    A_ref: float
    A_w_side: float
    A_w_front: float
    cpe10_D: float
    cpe10_E: float
    cpe10_A: float

    # Richtungsansatz (Excel-Vorlage 27.02.2026)
    we_side_pressure: float
    we_side_suction: float
    we_front_suction: float
    q_side_pressure: float
    q_side_suction: float
    q_front_suction: float

    # Massgebende Groessen
    wk_sog: float
    wk_druck: float
    wk_massgebend: float
    lastfall_massgebend: str
    qhk: float
    Hk: float
    Mk: float

    # Kontext
    hoehenstufe: int
    cscd_begruendung: str
    methodik: str
    cp_net_sog: float
    cp_net_druck: float
    zone_massgebend: str
    cpi_unguenstig_sog: float
    cpi_unguenstig_druck: float


    # Vereinfachte statische Reaktionsabschaetzung in Draufsicht
    q_seite_1: float = 0.0
    q_seite_2: float = 0.0
    q_vorne: float = 0.0
    auflagerabstand: float = 0.0
    Hx_k: float = 0.0
    Hx_Ed: float = 0.0
    Hy_1_k: float = 0.0
    Hy_1_Ed: float = 0.0
    Hy_2_k: float = 0.0
    Hy_2_Ed: float = 0.0
    M_A_k: float = 0.0
    gamma_Q_reaktionen: float = 1.5
    reaktionsmodell_hinweis: str = (
        "Vereinfachte statische Reaktionsabschaetzung in Draufsicht; "
        "keine exakte Lagerreaktionsberechnung eines vollstaendigen Tragmodells."
    )


__all__ = ["Projekt", "Standort", "Geometrie", "Ergebnisse"]
