"""Command-Line-Interface fuer Headless-Nutzung.

Beispiel:

    spittelmeister-windlast calc \\
        --projekt "Demo" --nummer 2026-001 --bearbeiter "S. Montero" \\
        --standort Wuerzburg --windzone 1 --gelaende binnen --hoehe-unn 192 \\
        --h 15.13 --d 12.55 --b 20.0 --z-balkon 12.83 \\
        --e-balkon 1.425 --h-abschluss 3.00 --s-verankerung 4.93 \\
        --pdf /tmp/windlast.pdf
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from .core import Geometrie, Projekt, Standort, WindlastBerechnung


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="spittelmeister-windlast",
        description="Windlastermittlung nach DIN EN 1991-1-4 / NA:2010-12",
    )
    sub = ap.add_subparsers(dest="command", required=True)

    calc = sub.add_parser("calc", help="Einmalige Berechnung.")
    # Projekt
    calc.add_argument("--projekt", required=True)
    calc.add_argument("--nummer", required=True)
    calc.add_argument("--bearbeiter", required=True)
    calc.add_argument("--datum", default=None)
    # Standort
    calc.add_argument("--standort", required=True)
    calc.add_argument("--windzone", type=int, required=True, choices=[1, 2, 3, 4])
    calc.add_argument("--gelaende", required=True, choices=["binnen", "kueste", "nordsee"])
    calc.add_argument("--hoehe-unn", type=float, required=True)
    # Geometrie
    for name in ("h", "d", "b", "z-balkon", "e-balkon", "h-abschluss", "s-verankerung"):
        calc.add_argument(f"--{name}", type=float, required=True)
    # Ausgabe
    calc.add_argument("--pdf", default=None, help="Optional: Pfad fuer PDF-Report.")
    calc.add_argument("--json", action="store_true", help="Ergebnisse als JSON ausgeben.")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command != "calc":
        return 2

    projekt_kwargs = dict(
        bezeichnung=args.projekt,
        nummer=args.nummer,
        bearbeiter=args.bearbeiter,
    )
    if args.datum:
        projekt_kwargs["datum"] = args.datum

    wb = WindlastBerechnung(
        Projekt(**projekt_kwargs),
        Standort(
            bezeichnung=args.standort,
            windzone=args.windzone,
            gelaende=args.gelaende,
            hoehe_uNN=args.hoehe_unn,
        ),
        Geometrie(
            h=args.h, d=args.d, b=args.b,
            z_balkon=args.z_balkon, e_balkon=args.e_balkon,
            h_abschluss=args.h_abschluss, s_verankerung=args.s_verankerung,
        ),
    )
    erg = wb.berechnen()

    if args.json:
        # Nur numerische Felder — LaTeX-Fragmente rausfiltern
        d = asdict(erg)
        clean = {
            k: v for k, v in d.items()
            if not isinstance(v, str) or k in ("lastfall_massgebend", "zone_massgebend")
        }
        print(json.dumps(clean, indent=2, ensure_ascii=False))
    else:
        wb.print_summary()

    if args.pdf:
        from .report import export_pdf
        export_pdf(args.pdf, wb.projekt, wb.standort, wb.geo, erg)
        print(f"PDF geschrieben: {args.pdf}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
