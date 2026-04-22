from __future__ import annotations

from typing import Any

try:  # pragma: no cover
    import streamlit as st
except Exception:  # pragma: no cover
    st = None

_KEY_PROJECT = "project_meta"
_KEY_WIND = "wind_inp"
_KEY_VERANKERUNG = "verankerung_inp"
_KEY_REPORT = "report_selection"
_KEY_LATEX = "latex_cfg"


def _state() -> dict[str, Any]:
    if st is None:
        raise RuntimeError("Streamlit ist für session helpers nicht verfügbar.")
    return st.session_state


def save_project_meta_state(**kwargs: Any) -> None:
    _state()[_KEY_PROJECT] = dict(kwargs)


def load_project_meta_state() -> dict[str, Any]:
    return dict(_state().get(_KEY_PROJECT, {}))


def save_wind_state(**kwargs: Any) -> None:
    _state()[_KEY_WIND] = dict(kwargs)


def load_wind_state() -> dict[str, Any]:
    return dict(_state().get(_KEY_WIND, {}))


def save_verankerung_state(**kwargs: Any) -> None:
    _state()[_KEY_VERANKERUNG] = dict(kwargs)


def load_verankerung_state() -> dict[str, Any]:
    return dict(_state().get(_KEY_VERANKERUNG, {}))


def save_report_selection_state(**kwargs: Any) -> None:
    _state()[_KEY_REPORT] = dict(kwargs)


def load_report_selection_state() -> dict[str, Any]:
    return dict(_state().get(_KEY_REPORT, {}))


def save_latex_config_state(**kwargs: Any) -> None:
    _state()[_KEY_LATEX] = dict(kwargs)


def load_latex_config_state() -> dict[str, Any]:
    return dict(_state().get(_KEY_LATEX, {}))
