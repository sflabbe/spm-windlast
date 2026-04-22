"""Compile-time smoke tests fuer die Streamlit-App.

Stellt sicher, dass das Shell-Modul und die produktive Windlast-Seite ohne
Syntaxfehler importierbar sind und dass alle Imports zur neuen Paketstruktur
passen. Die UI selbst wird nicht ausgefuehrt (Streamlit-Widgets werden nur
unter ``streamlit run`` aktiv).

Ist Streamlit nicht installiert (z. B. reines Kern-Setup), werden die Import-
Tests uebersprungen.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

APP_PATH = Path(__file__).resolve().parents[1] / "apps" / "streamlit_app" / "app.py"
PAGE_WINDLAST_PATH = Path(__file__).resolve().parents[1] / "apps" / "streamlit_app" / "pages" / "01_Windlast.py"
PAGE_VERANKERUNG_PATH = Path(__file__).resolve().parents[1] / "apps" / "streamlit_app" / "pages" / "02_Verankerung.py"
PAGE_PROTOKOLL_PATH = Path(__file__).resolve().parents[1] / "apps" / "streamlit_app" / "pages" / "04_Protokoll.py"


def _assert_python_file_parses(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    ast.parse(source, filename=str(path))


def _assert_import_works(path: Path, module_name: str) -> None:
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ImportError as e:
        pytest.fail(f"Modul-Import fehlgeschlagen ({path.name}): {e}")
    except Exception:
        # Streamlit wirft ausserhalb seines Runners teilweise Warnings/Errors
        # bei der ersten Widget-Instanz — das ist fuer uns kein Fail, solange
        # die Import-Kette selbst gesund ist.
        pass


def test_app_shell_ist_gueltiges_python():
    _assert_python_file_parses(APP_PATH)


def test_windlast_page_ist_gueltiges_python():
    _assert_python_file_parses(PAGE_WINDLAST_PATH)


def test_verankerung_page_ist_gueltiges_python():
    _assert_python_file_parses(PAGE_VERANKERUNG_PATH)


def test_protokoll_page_ist_gueltiges_python():
    _assert_python_file_parses(PAGE_PROTOKOLL_PATH)


def test_streamlit_module_imports_funktionieren():
    try:
        import streamlit  # noqa: F401
    except ImportError:
        pytest.skip("streamlit nicht installiert — App-Import nicht pruefbar.")

    _assert_import_works(APP_PATH, "_smoke_app_shell")
    _assert_import_works(PAGE_WINDLAST_PATH, "_smoke_page_windlast")
    _assert_import_works(PAGE_VERANKERUNG_PATH, "_smoke_page_verankerung")
    _assert_import_works(PAGE_PROTOKOLL_PATH, "_smoke_page_protokoll")
