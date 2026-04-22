from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class ProjectMetadata:
    project_id: str = "2026-WB-001"
    title: str = "Windnachweis Balkonanschluss"
    client: str = ""
    street: str = ""
    city: str = ""
    revision: str = "0"
    bearbeiter: str = ""
    datum: str = field(default_factory=lambda: date.today().strftime("%d.%m.%Y"))


@dataclass
class ModuleEntry:
    enabled: bool = False
    input: dict[str, Any] = field(default_factory=dict)
    results_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectDocument:
    schema_version: int = 1
    project: ProjectMetadata = field(default_factory=ProjectMetadata)
    modules: dict[str, ModuleEntry] = field(default_factory=lambda: {
        "windlast": ModuleEntry(enabled=True),
        "verankerung": ModuleEntry(enabled=False),
        "herstellernachweis": ModuleEntry(enabled=False),
    })
    report: dict[str, Any] = field(default_factory=lambda: {
        "selection": {
            "windlast": {"include": True},
            "verankerung": {"include": False},
            "herstellernachweis": {"include": False},
        }
    })
