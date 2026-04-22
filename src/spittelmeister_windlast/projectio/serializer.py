from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any


def dump_json(data: Any) -> str:
    return json.dumps(asdict(data), ensure_ascii=False, indent=2)
