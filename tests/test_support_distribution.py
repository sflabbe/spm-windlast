from __future__ import annotations

import pytest

from spittelmeister_windlast.transfer import ConnectionActions, derive_support_action


def _actions() -> ConnectionActions:
    return ConnectionActions(Hx_Ed=1.2, Hy_1_Ed=1.6, Hy_2_Ed=4.4, M_A_k=7.5)


def test_festlager_receives_base_components_and_additional_moment() -> None:
    support = derive_support_action(
        _actions(),
        support_index=2,
        support_role="festlager",
        slide_direction="x",
        local_eccentricity_mm=140.0,
        platform_eccentricity_mm=60.0,
    )
    assert support.base_fx_Ed == pytest.approx(0.6)
    assert support.base_fy_Ed == pytest.approx(4.4)
    assert support.transferred_fx_Ed == pytest.approx(0.6)
    assert support.transferred_fy_Ed == pytest.approx(4.4)
    assert support.additional_moment_Ed > 0.0


def test_gleitlager_releases_x_component_ideally() -> None:
    support = derive_support_action(
        _actions(),
        support_index=1,
        support_role="gleitlager",
        slide_direction="x",
        local_eccentricity_mm=120.0,
        platform_eccentricity_mm=0.0,
    )
    assert support.transferred_fx_Ed == pytest.approx(0.0)
    assert support.transferred_fy_Ed == pytest.approx(1.6)
    assert support.released_component_Ed == pytest.approx(0.6)
