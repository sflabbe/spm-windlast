from __future__ import annotations

from pathlib import Path
import os
import shutil

_ENV_VAR_NAMES = (
    "SPM_WINDLAST_PDFLATEX",
    "BALKONSYSTEM_PDFLATEX",
    "PDFLATEX_PATH",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _portable_candidates() -> list[Path]:
    repo_root = _repo_root()
    return [
        Path(r"C:\PortableLatex\MiKTeX\texmfs\install\miktex\bin\x64\pdflatex.exe"),
        Path(r"C:\miktex-portable\texmfs\install\miktex\bin\x64\pdflatex.exe"),
        Path(r"D:\PortableLatex\MiKTeX\texmfs\install\miktex\bin\x64\pdflatex.exe"),
        repo_root / "PortableLaTeX" / "MiKTeX" / "texmfs" / "install" / "miktex" / "bin" / "x64" / "pdflatex.exe",
        repo_root / "MiKTeX" / "texmfs" / "install" / "miktex" / "bin" / "x64" / "pdflatex.exe",
        repo_root / "tools" / "MiKTeX" / "texmfs" / "install" / "miktex" / "bin" / "x64" / "pdflatex.exe",
    ]


def _normalize_candidate(path_value: str | os.PathLike[str] | None) -> str | None:
    if path_value is None:
        return None
    candidate = str(path_value).strip().strip('"')
    if not candidate:
        return None
    if Path(candidate).exists():
        return candidate
    which_hit = shutil.which(candidate)
    if which_hit:
        return which_hit
    return None


def resolve_pdflatex(explicit_path: str | os.PathLike[str] | None = None) -> str | None:
    """Resolve a working ``pdflatex`` executable.

    Resolution order:
    1. explicitly provided path/name
    2. supported environment variables
    3. PATH lookup
    4. known portable MiKTeX locations
    """
    direct_hit = _normalize_candidate(explicit_path)
    if direct_hit:
        return direct_hit

    for env_name in _ENV_VAR_NAMES:
        env_hit = _normalize_candidate(os.environ.get(env_name))
        if env_hit:
            return env_hit

    path_hit = shutil.which("pdflatex")
    if path_hit:
        return path_hit

    for candidate in _portable_candidates():
        candidate_hit = _normalize_candidate(candidate)
        if candidate_hit:
            return candidate_hit
    return None


__all__ = ["resolve_pdflatex"]
