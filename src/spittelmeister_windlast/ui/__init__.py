"""UI-Helfer für Streamlit."""

from .project_ui import render_project_sidebar
from .session import (
    load_latex_config_state,
    load_project_meta_state,
    load_report_selection_state,
    load_verankerung_state,
    load_wind_state,
    save_latex_config_state,
    save_project_meta_state,
    save_report_selection_state,
    save_verankerung_state,
    save_wind_state,
)

__all__ = [
    "render_project_sidebar",
    "load_latex_config_state",
    "load_project_meta_state",
    "load_report_selection_state",
    "load_verankerung_state",
    "load_wind_state",
    "save_latex_config_state",
    "save_project_meta_state",
    "save_report_selection_state",
    "save_verankerung_state",
    "save_wind_state",
    "apply_macro_to_state_input",
    "suggest_anchorage_macro",
    "build_verankerung_feedback",
    "render_assessment_badges",
    "render_plan_preview_svg",
    "render_side_preview_svg",
    "analyze_verankerung_consistency",
    "apply_consistency_quick_fixes",
]

from .verankerung_optimizer import apply_macro_to_state_input, suggest_anchorage_macro
from .verankerung_preview import (
    build_verankerung_feedback,
    render_assessment_badges,
    render_plan_preview_svg,
    render_side_preview_svg,
)

from .verankerung_consistency import (
    analyze_verankerung_consistency,
    apply_consistency_quick_fixes,
)
