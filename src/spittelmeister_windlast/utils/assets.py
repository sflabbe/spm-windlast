"""Hilfsfunktionen fuer robuste Asset-Pfade."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
import shutil


PACKAGE_NAME = "spittelmeister_windlast"


def _package_asset_root() -> Path | None:
    """Gibt den Asset-Ordner aus Paketdaten zurueck (falls vorhanden)."""
    try:
        candidate = resources.files(PACKAGE_NAME) / "assets"
    except Exception:
        return None

    candidate_path = Path(str(candidate))
    if candidate_path.exists():
        return candidate_path
    return None


def _repo_asset_root() -> Path:
    """Fuer Entwicklungsbetrieb: ``<repo>/assets``."""
    return Path(__file__).resolve().parents[3] / "assets"


def get_asset_root() -> Path:
    """Liefert den bevorzugten Asset-Ordner (Paketdaten, sonst Repo)."""
    package_root = _package_asset_root()
    if package_root is not None:
        return package_root

    repo_root = _repo_asset_root()
    if repo_root.exists():
        return repo_root

    raise FileNotFoundError("Asset-Ordner nicht gefunden (weder Paketdaten noch Repo).")


def get_asset_path(filename: str) -> Path:
    """Liefert den absoluten Pfad zu einem Asset und validiert die Existenz."""
    path = get_asset_root() / filename
    if not path.exists():
        raise FileNotFoundError(f"Asset nicht gefunden: {filename}")
    return path


def copy_assets(target_dir: str | Path, filenames: list[str]) -> Path:
    """Kopiert angeforderte Assets in ``target_dir/assets`` und gibt den Ordner zurueck."""
    dst_root = Path(target_dir) / "assets"
    dst_root.mkdir(parents=True, exist_ok=True)

    for name in filenames:
        src = get_asset_path(name)
        shutil.copy(src, dst_root / name)

    return dst_root
