from __future__ import annotations

from dataclasses import asdict

from ..transfer.modelle import ConnectionActions
from ..verankerung.modelle import AnchorageAssessment, AnchorageInput


def connection_actions_to_snapshot(value: ConnectionActions) -> dict:
    return asdict(value)


def anchorage_input_to_snapshot(value: AnchorageInput) -> dict:
    return asdict(value)


def anchorage_assessment_to_snapshot(value: AnchorageAssessment) -> dict:
    return asdict(value)
