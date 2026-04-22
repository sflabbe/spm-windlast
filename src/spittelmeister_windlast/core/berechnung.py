"""Windlast-Berechnung — Orchestrator.

Verdrahtet Eingangsgroessen, Peak-Pressure und Druckbeiwerte zu
``Ergebnisse``. Enthaelt NUR Rechenlogik, keine I/O und kein LaTeX.
"""

from __future__ import annotations

from typing import Optional

from .druckbeiwerte import cpe10
from .modelle import Ergebnisse, Geometrie, Projekt, Standort
from .peak_pressure import berechne_qp
from ..transfer.vereinfachtes_balkonsystem import derive_connection_actions_simple

_METHODIK = "Detaillierter Richtungsansatz nach Excel-Vorlage 27.02.2026"
_GAMMA_Q_REAKTIONEN = 1.5
_REAKTIONSMODELL_HINWEIS = (
    "Die nachfolgenden Auflagerreaktionen stellen eine vereinfachte statische "
    "Abschätzung in Draufsicht dar. Sie dienen der Vorbemessung und ersetzen "
    "kein vollständiges Tragwerksmodell mit exakter Lagerreaktionsbestimmung."
)


def _berechne_reaktionen_vereinfacht(
    B: float,
    T: float,
    hw_yz: float,
    hw_xz: float,
    we_side_pressure: float,
    we_side_suction: float,
    we_front_suction: float,
    a: float | None = None,
    b: float | None = None,
) -> dict[str, float]:
    """Rueckwaerts-kompatibler Wrapper auf die Transfer-Layer-Logik."""
    actions = derive_connection_actions_simple(
        B=B,
        T=T,
        hw_yz=hw_yz,
        a=a,
        b=b,
        hw_xz=hw_xz,
        we_side_pressure=we_side_pressure,
        we_side_suction=we_side_suction,
        we_front_suction=we_front_suction,
        gamma_Q=_GAMMA_Q_REAKTIONEN,
    )
    return {
        "s": actions.s,
        "q_seite_1": actions.q_seite_1,
        "q_seite_2": actions.q_seite_2,
        "q_vorne": actions.q_vorne,
        "auflagerabstand": actions.auflagerabstand,
        "Hx_k": actions.Hx_k,
        "Hx_Ed": actions.Hx_Ed,
        "Hy_1_k": actions.Hy_1_k,
        "Hy_1_Ed": actions.Hy_1_Ed,
        "Hy_2_k": actions.Hy_2_k,
        "Hy_2_Ed": actions.Hy_2_Ed,
        "M_A_k": actions.M_A_k,
    }


def _cscd_begruendung(h: float, d: float) -> tuple[float, str]:
    """cscd nach NA.C.2(4) bzw. EN 1991-1-4 Tabelle 6.1.

    Returns:
        (cscd, Begruendungstext als LaTeX-Fragment)

    Raises:
        ValueError: Wenn cscd > 1.0 ergibt (dann ist ein Schwingungsnachweis
                    noetig, der hier nicht abgedeckt ist).
    """
    if h <= 25.0:
        return 1.0, (
            r"$c_{s}c_{d} = 1{,}0$ nach NA.C.2(4): "
            f"Gebaeudehoehe $h = {h:.2f}~\\mathrm{{m}} \\leq 25~\\mathrm{{m}}$, "
            "keine Schwingungsanfaelligkeit."
        )
    if h <= 100.0 and h <= 4 * d:
        return 1.0, (
            r"$c_{s}c_{d} = 1{,}0$ nach EN~1991-1-4 Tabelle~6.1: "
            f"$h = {h:.2f}~\\mathrm{{m}} \\leq 100~\\mathrm{{m}}$ und "
            f"$h = {h:.2f}~\\mathrm{{m}} \\leq 4d = {4*d:.2f}~\\mathrm{{m}}$."
        )
    raise ValueError("cscd > 1,0 — gesonderter Schwingungsnachweis erforderlich.")


class WindlastBerechnung:
    """Orchestrator: Eingangsgroessen -> Ergebnisse.

    Example:
        >>> from spittelmeister_windlast import (
        ...     WindlastBerechnung, Projekt, Standort, Geometrie
        ... )
        >>> wb = WindlastBerechnung(
        ...     Projekt("Demo", "2026-001", "S. Montero"),
        ...     Standort("Pforzheim", windzone=1, gelaende="binnen", hoehe_uNN=280.0),
        ...     Geometrie(h=15.0, d=12.0, b=20.0, z_balkon=13.0,
        ...               e_balkon=1.4, h_abschluss=3.0, s_verankerung=5.0),
        ... )
        >>> erg = wb.berechnen()
        >>> round(erg.qhk, 2) > 0
        True
    """

    def __init__(self, projekt: Projekt, standort: Standort, geo: Geometrie):
        self.projekt = projekt
        self.standort = standort
        self.geo = geo
        self.erg: Optional[Ergebnisse] = None

    def berechnen(self) -> Ergebnisse:
        """Fuehrt die Berechnung durch und speichert/retourniert ``Ergebnisse``."""
        geo = self.geo
        st = self.standort

        # 1. qp(z)
        qp_info = berechne_qp(geo.h, st.windzone, st.gelaende)  # type: ignore[arg-type]
        qp = qp_info.qp

        # 2. cscd
        cscd, cscd_begruendung = _cscd_begruendung(geo.h, geo.d)

        # 3. cpe,10 je Bereich
        h_d = geo.h_d
        cpe10_D = cpe10("D", h_d)
        cpe10_E = cpe10("E", h_d)
        cpe10_A = cpe10("A", h_d)

        # 4. we (Vorzeichen wie in Excel-Vorlage beibehalten)
        we_side_pressure = qp * cscd * cpe10_D
        we_side_suction = qp * cscd * cpe10_E
        we_front_suction = qp * cscd * cpe10_A

        # 5. Linienlasten pro Meter Hoehe (eigentlich: q_h = we * h_w)
        q_side_pressure = we_side_pressure * geo.h_abschluss
        q_side_suction = we_side_suction * geo.h_abschluss
        q_front_suction = we_front_suction * geo.h_abschluss

        # 6. Massgebender Lastfall = groesste |q|
        candidates = [
            ("Seite Druck (Bereich D)", q_side_pressure, "D"),
            ("Seite Sog (Bereich E)", q_side_suction, "E"),
            ("Front Sog (Bereich A)", q_front_suction, "A"),
        ]
        lastfall_massgebend, qhk_signed, zone_massgebend = max(
            candidates, key=lambda x: abs(x[1])
        )
        qhk = abs(qhk_signed)
        wk_massgebend = abs(qhk_signed / geo.h_abschluss)
        Hk = qhk * geo.s_verankerung
        Mk = Hk * (geo.h_abschluss / 2.0)

        # 7. Vereinfachte statische Reaktionsabschaetzung in Draufsicht
        connection_actions = derive_connection_actions_simple(
            B=geo.s_verankerung,
            T=geo.e_balkon,
            hw_yz=geo.h_abschluss,
            a=geo.b_auflager_rand,
            hw_xz=geo.h_abschluss,
            we_side_pressure=we_side_pressure,
            we_side_suction=we_side_suction,
            we_front_suction=we_front_suction,
            gamma_Q=_GAMMA_Q_REAKTIONEN,
        )

        self.erg = Ergebnisse(
            # Peak-Pressure
            qb0=qp_info.qb0,
            qp=qp,
            qp_faktor=qp_info.faktor,
            qp_formel=qp_info.formel,
            qp_auswertung=qp_info.auswertung,
            qp_abschnitt=qp_info.abschnitt,
            qp_verfahren=qp_info.verfahren,
            qp_normstelle=qp_info.normstelle,
            gelaende_label=qp_info.gelaende_label,
            # Geometrie + cpe
            cscd=cscd,
            h_d=h_d,
            A_ref=geo.A_ref,
            A_w_side=geo.A_w_side,
            A_w_front=geo.A_w_front,
            cpe10_D=cpe10_D,
            cpe10_E=cpe10_E,
            cpe10_A=cpe10_A,
            # Richtungsansatz
            we_side_pressure=we_side_pressure,
            we_side_suction=we_side_suction,
            we_front_suction=we_front_suction,
            q_side_pressure=q_side_pressure,
            q_side_suction=q_side_suction,
            q_front_suction=q_front_suction,
            # Massgebend
            wk_sog=we_front_suction,
            wk_druck=we_side_pressure,
            wk_massgebend=wk_massgebend,
            lastfall_massgebend=lastfall_massgebend,
            qhk=qhk,
            Hk=Hk,
            Mk=Mk,
            hoehenstufe=0,
            cscd_begruendung=cscd_begruendung,
            methodik=_METHODIK,
            cp_net_sog=cpe10_A,
            cp_net_druck=cpe10_D,
            zone_massgebend=zone_massgebend,
            cpi_unguenstig_sog=0.0,
            cpi_unguenstig_druck=0.0,
            q_seite_1=connection_actions.q_seite_1,
            q_seite_2=connection_actions.q_seite_2,
            q_vorne=connection_actions.q_vorne,
            s=connection_actions.s,
            auflagerabstand=connection_actions.auflagerabstand,
            Hx_k=connection_actions.Hx_k,
            Hx_Ed=connection_actions.Hx_Ed,
            Hy_1_k=connection_actions.Hy_1_k,
            Hy_1_Ed=connection_actions.Hy_1_Ed,
            Hy_2_k=connection_actions.Hy_2_k,
            Hy_2_Ed=connection_actions.Hy_2_Ed,
            M_A_k=connection_actions.M_A_k,
            gamma_Q_reaktionen=_GAMMA_Q_REAKTIONEN,
            reaktionsmodell_hinweis=_REAKTIONSMODELL_HINWEIS,
        )
        return self.erg

    def export_pdf(self, output_path: str) -> str:
        """Bequemlichkeits-Wrapper um ``report.export_pdf``.

        Ermoeglicht ``wb.export_pdf(...)`` fuer Rueckwaerts-Kompatibilitaet
        mit dem v1.x-API. Fuer neue Projekte wird der direkte Aufruf der
        freien Funktion aus ``spittelmeister_windlast.report`` empfohlen,
        da er die PDF-Erzeugung klarer vom Rechenkern trennt.

        Raises:
            RuntimeError: Wenn ``berechnen()`` noch nicht aufgerufen wurde.
        """
        if self.erg is None:
            self.berechnen()
        # Lazy import: report -> pdflatex wird nur geladen, wenn tatsaechlich
        # ein PDF gewuenscht ist. Haelt den Kern frei von LaTeX-Abhaengigkeit.
        from ..report import export_pdf as _export_pdf
        assert self.erg is not None
        return _export_pdf(output_path, self.projekt, self.standort, self.geo, self.erg)

    def print_summary(self) -> None:
        """Kurze Textausgabe der Schnittgroessen (fuer CLI / Tests)."""
        if self.erg is None:
            self.berechnen()
        e = self.erg
        assert e is not None
        print("\n" + "=" * 55)
        print("  WINDLAST — ERGEBNISSE")
        print("=" * 55)
        print(f"  Methodik      = {e.methodik}")
        print(f"  qp            = {e.qp:.2f} kN/m^2")
        print(f"  qh,k          = {e.qhk:.2f} kN/m")
        print(f"  Hk je Feld    = {e.Hk:.2f} kN")
        print(f"  Mk Fusspunkt  = {e.Mk:.2f} kNm")
        print(f"  massgebend    = {e.lastfall_massgebend}")
        print("=" * 55 + "\n")


__all__ = ["WindlastBerechnung"]
