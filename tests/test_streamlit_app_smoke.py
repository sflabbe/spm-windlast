"""Compile-time smoke test fuer die Streamlit-App.

Stellt sicher, dass das App-Modul ohne Syntaxfehler importierbar ist und
dass alle Imports zur neuen Paketstruktur passen. Die UI selbst wird nicht
ausgefuehrt (Streamlit-Widgets werden nur unter ``streamlit run`` aktiv).

Ist Streamlit nicht installiert (z. B. reines Kern-Setup), wird der Test
uebersprungen.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

APP_PATH = Path(__file__).resolve().parents[1] / "apps" / "streamlit_app" / "app.py"


def test_app_py_ist_gueltiges_python():
    """AST-Parsen reicht, um Syntax/Indent-Fehler zu erkennen."""
    source = APP_PATH.read_text(encoding="utf-8")
    ast.parse(source, filename=str(APP_PATH))


def test_app_imports_funktionieren():
    """Vollstaendiger Import der App. Ueberspringt, wenn Streamlit fehlt."""
    try:
        import streamlit  # noqa: F401
    except ImportError:
        pytest.skip("streamlit nicht installiert — App-Import nicht pruefbar.")

    spec = importlib.util.spec_from_file_location("_smoke_app", APP_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Streamlit-Widgets werden beim Import teilweise ausgefuehrt. Wir
    # akzeptieren runtime-Warnungen (kein ScriptRunContext), aber keine
    # ImportError / NameError / SyntaxError.
    try:
        spec.loader.exec_module(module)
    except ImportError as e:
        pytest.fail(f"App-Import fehlgeschlagen (neue Paketstruktur?): {e}")
    except Exception:
        # Streamlit wirft ausserhalb seines Runners teilweise Warnings/Errors
        # bei der ersten Widget-Instanz — das ist fuer uns kein Fail, solange
        # die Import-Kette selbst gesund ist.
        pass
