from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any


def serialize_dataclass(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    raise TypeError("serialize_dataclass erwartet eine Dataclass-Instanz.")
