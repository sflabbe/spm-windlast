from __future__ import annotations

from pathlib import Path

from spittelmeister_windlast import Ergebnisse, Geometrie, Projekt, Standort
from spittelmeister_windlast.report import compile_latex_to_pdf_bytes
from spittelmeister_windlast.report.latex import export_pdf


def _sample_ergebnisse() -> Ergebnisse:
    return Ergebnisse(
        qb0=0.65, qp=0.95, qp_faktor=1.46, qp_formel="x", qp_auswertung="x", qp_abschnitt="A", qp_verfahren="DIN",
        qp_normstelle="NA.B.3", gelaende_label="Binnenland", cscd=1.0, h_d=1.2, A_ref=3.0, A_w_side=2.0, A_w_front=3.0,
        cpe10_D=0.8, cpe10_E=-0.5, cpe10_A=-1.2, we_side_pressure=0.76, we_side_suction=-0.48, we_front_suction=-1.14,
        q_side_pressure=0.84, q_side_suction=-0.53, q_front_suction=-1.25, wk_sog=-1.25, wk_druck=0.84,
        wk_massgebend=-1.25, lastfall_massgebend="Frontsog", qhk=1.25, Hk=4.0, Mk=2.2, hoehenstufe=0,
        cscd_begruendung="Test", methodik="Test", cp_net_sog=-1.2, cp_net_druck=0.8, zone_massgebend="A",
        cpi_unguenstig_sog=0.0, cpi_unguenstig_druck=0.0
    )


def test_compile_latex_uses_cwd_and_basename(monkeypatch):
    calls: list[dict[str, object]] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        cwd = Path(kwargs["cwd"])
        (cwd / "main.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

        class Result:
            stdout = "ok"

        return Result()

    monkeypatch.setattr("spittelmeister_windlast.report.report_bundle.resolve_pdflatex", lambda _: "C:/PortableLatex/MiKTeX/pdflatex.exe")
    monkeypatch.setattr("spittelmeister_windlast.report.report_bundle.subprocess.run", fake_run)

    pdf = compile_latex_to_pdf_bytes(r"\documentclass{article}\begin{document}Hi\end{document}")

    assert pdf.startswith(b"%PDF")
    assert len(calls) == 2
    assert calls[0]["cmd"] == [
        "C:/PortableLatex/MiKTeX/pdflatex.exe",
        "-interaction=nonstopmode",
        "main.tex",
    ]
    assert Path(calls[0]["cwd"]).name


def test_export_pdf_uses_cwd_and_basename(monkeypatch, tmp_path):
    calls: list[dict[str, object]] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, **kwargs})
        cwd = Path(kwargs["cwd"])
        (cwd / "windlast.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

        class Result:
            stdout = "ok"

        return Result()

    monkeypatch.setattr("spittelmeister_windlast.report.latex.resolve_pdflatex", lambda _: "C:/PortableLatex/MiKTeX/pdflatex.exe")
    monkeypatch.setattr("spittelmeister_windlast.report.latex.subprocess.run", fake_run)

    out = tmp_path / "out.pdf"
    export_pdf(
        str(out),
        Projekt("Demo", "W-1", "Test"),
        Standort("Pforzheim", 2, "binnen", 280.0),
        Geometrie(h=12.0, d=10.0, b=15.0, z_balkon=8.0, e_balkon=2.0, h_abschluss=1.1, s_verankerung=3.0),
        _sample_ergebnisse(),
    )

    assert out.exists()
    assert len(calls) == 2
    assert calls[0]["cmd"] == [
        "C:/PortableLatex/MiKTeX/pdflatex.exe",
        "-interaction=nonstopmode",
        "windlast.tex",
    ]
    assert Path(calls[0]["cwd"]).name
