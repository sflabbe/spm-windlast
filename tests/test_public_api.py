from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

from spittelmeister_windlast.api import (
    BalconyWindResult,
    calculate_balcony_wind,
    calculate_wind,
)


def test_calculate_balcony_wind_returns_stable_contract() -> None:
    result = calculate_balcony_wind(
        geometry={
            "B1": 3.94,
            "T": 1.94,
            "HW_Seite": 1.1,
            "HW_Front": 1.1,
        },
        qw=0.8,
        cpe_parallel=0.5,
        cpe_normal=0.7,
        gamma_w=1.5,
    )

    assert isinstance(result, BalconyWindResult)
    assert set(asdict(result)) == {
        "qw",
        "wch_S",
        "wch_F",
        "AW_yz",
        "AW_xz",
        "Hx_d_ges",
        "Hy_d_ges",
        "gamma_w",
    }
    assert result.qw == pytest.approx(0.8)
    assert result.wch_S == pytest.approx(0.4)
    assert result.wch_F == pytest.approx(0.56)
    assert result.AW_yz == pytest.approx(2.134)
    assert result.AW_xz == pytest.approx(4.334)
    assert result.Hx_d_ges == pytest.approx(1.2804)
    assert result.Hy_d_ges == pytest.approx(3.64056)
    assert result.gamma_w == pytest.approx(1.5)


def test_calculate_balcony_wind_accepts_direct_geometry_values() -> None:
    result = calculate_balcony_wind(
        B1=4.0,
        T=2.0,
        HW_Seite=1.25,
        HW_Front=1.5,
        qw=1.0,
        cpe_parallel=0.6,
        cpe_normal=0.8,
    )

    assert result.asdict() == {
        "qw": pytest.approx(1.0),
        "wch_S": pytest.approx(0.6),
        "wch_F": pytest.approx(0.8),
        "AW_yz": pytest.approx(2.5),
        "AW_xz": pytest.approx(6.0),
        "Hx_d_ges": pytest.approx(2.25),
        "Hy_d_ges": pytest.approx(7.2),
        "gamma_w": pytest.approx(1.5),
    }


def test_legacy_calculate_wind_alias_uses_same_contract() -> None:
    result = calculate_wind(
        geometry={
            "B1": 3.94,
            "T": 1.94,
            "HW_Seite": 1.1,
            "HW_Front": 1.1,
        },
        qw=0.8,
        cpe_parallel=0.5,
        cpe_normal=0.7,
    )

    assert isinstance(result, BalconyWindResult)
    assert result.Hx_d_ges == pytest.approx(1.2804)


def test_public_api_import_does_not_pull_ui_or_cli_modules() -> None:
    src_path = Path(__file__).resolve().parents[1] / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_path)
    if os.environ.get("PYTHONPATH"):
        env["PYTHONPATH"] += os.pathsep + os.environ["PYTHONPATH"]

    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import spittelmeister_windlast.api; "
                "assert 'streamlit' not in sys.modules; "
                "assert 'spittelmeister_windlast.cli' not in sys.modules"
            ),
        ],
        check=True,
        env=env,
    )
