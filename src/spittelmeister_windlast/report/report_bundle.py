from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile
from collections.abc import Iterable

from ..utils import resolve_pdflatex
from ..utils.assets import get_asset_root

FIGURE_FILENAMES = [
    "wind_geb.svg",
    "balcony_system.svg",
    "reaction_scheme.svg",
    "verankerung.svg",
]

LEGACY_PDF_FILENAMES = [
    "wind_geb.pdf",
    "building_geometry_cases.pdf",
    "balcony_system.pdf",
    "load_scheme.pdf",
    "reaction_scheme.pdf",
    "verankerung.pdf",
]

LATEX_ASSET_FILENAMES = [
    "building_geometry_zoning.tex",
    "building_geometry_cases.tex",
    "balcony_system.tex",
    "load_scheme.tex",
    "reaction_scheme.tex",
]


def _copy_report_assets(project_dir: Path) -> None:
    assets_root = get_asset_root()
    assets_dir = project_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    for name in sorted(set(FIGURE_FILENAMES + LEGACY_PDF_FILENAMES + LATEX_ASSET_FILENAMES)):
        src = assets_root / name
        if src.is_file():
            shutil.copy(src, assets_dir / name)


def create_report_zip_bundle(
    tex_source: str,
    *,
    extra_files: Iterable[tuple[str, str]] | None = None,
    main_tex_name: str = "main.tex",
    repo_root: str | Path | None = None,
) -> bytes:
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "report_project"
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / main_tex_name).write_text(tex_source, encoding="utf-8")
        (project_dir / "README.txt").write_text(
            "LaTeX-Projektbundle für den Windlast-/Verankerungsbericht.\n"
            "Kompilation: pdflatex main.tex (ggf. zweimal).\n"
            "Die für \\input referenzierten Skizzen liegen im Unterordner assets/.\n",
            encoding="utf-8",
        )
        _ = repo_root
        _copy_report_assets(project_dir)
        if extra_files:
            for src, rel_dest in extra_files:
                src_path = Path(src)
                if not src_path.is_file():
                    continue
                dest_path = project_dir / rel_dest
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(src_path, dest_path)
        zip_path = Path(tmpdir) / "report_project.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for file_path in project_dir.rglob("*"):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(project_dir))
        return zip_path.read_bytes()


def compile_latex_to_pdf_bytes(
    tex_source: str,
    *,
    main_tex_name: str = "main.tex",
    pdflatex_executable: str = "pdflatex",
) -> bytes:
    resolved_pdflatex = resolve_pdflatex(pdflatex_executable)
    if resolved_pdflatex is None:
        raise FileNotFoundError(
            f"pdflatex nicht gefunden: {pdflatex_executable}. Bitte TeX Live oder MiKTeX installieren."
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        tex_path = project_dir / main_tex_name
        tex_path.write_text(tex_source, encoding="utf-8")
        _copy_report_assets(project_dir)

        result = None
        compile_cmd = [
            resolved_pdflatex,
            "-interaction=nonstopmode",
            main_tex_name,
        ]
        for _ in range(2):
            result = subprocess.run(
                compile_cmd,
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                encoding="latin-1",
                errors="replace",
            )
        pdf_path = project_dir / f"{Path(main_tex_name).stem}.pdf"
        if not pdf_path.exists():
            tail = (result.stdout if result else "")[-2000:]
            raise RuntimeError("PDF-Kompilierung fehlgeschlagen.\n" + tail)
        return pdf_path.read_bytes()
