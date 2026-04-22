from __future__ import annotations

from pathlib import Path

from spittelmeister_windlast.utils.pdflatex import resolve_pdflatex


def test_resolve_pdflatex_prefers_explicit_existing_path(tmp_path, monkeypatch):
    fake = tmp_path / "pdflatex.exe"
    fake.write_text("", encoding="utf-8")
    monkeypatch.delenv("SPM_WINDLAST_PDFLATEX", raising=False)
    monkeypatch.setattr("spittelmeister_windlast.utils.pdflatex.shutil.which", lambda _: None)

    assert resolve_pdflatex(str(fake)) == str(fake)


def test_resolve_pdflatex_accepts_env_var(monkeypatch, tmp_path):
    fake = tmp_path / "pdflatex.exe"
    fake.write_text("", encoding="utf-8")
    monkeypatch.setenv("SPM_WINDLAST_PDFLATEX", str(fake))
    monkeypatch.setattr("spittelmeister_windlast.utils.pdflatex.shutil.which", lambda _: None)

    assert resolve_pdflatex(None) == str(fake)


def test_resolve_pdflatex_falls_back_to_portable_location(monkeypatch, tmp_path):
    target = tmp_path / "PortableLatex" / "MiKTeX" / "texmfs" / "install" / "miktex" / "bin" / "x64" / "pdflatex.exe"
    target.parent.mkdir(parents=True)
    target.write_text("", encoding="utf-8")

    monkeypatch.delenv("SPM_WINDLAST_PDFLATEX", raising=False)
    monkeypatch.delenv("BALKONSYSTEM_PDFLATEX", raising=False)
    monkeypatch.delenv("PDFLATEX_PATH", raising=False)
    monkeypatch.setattr("spittelmeister_windlast.utils.pdflatex.shutil.which", lambda _: None)
    monkeypatch.setattr(
        "spittelmeister_windlast.utils.pdflatex._portable_candidates",
        lambda: [target],
    )

    assert resolve_pdflatex(None) == str(target)
