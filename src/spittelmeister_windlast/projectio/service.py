from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .models import ModuleEntry, ProjectDocument, ProjectMetadata
from .validation import validate_project_document

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def _coerce_project_document(payload: dict[str, Any]) -> ProjectDocument:
    default_doc = ProjectDocument()

    project_payload = payload.get("project", {})
    project = ProjectMetadata(**project_payload)

    modules: dict[str, ModuleEntry] = {
        key: ModuleEntry(
            enabled=value.enabled,
            input=dict(value.input),
            results_snapshot=dict(value.results_snapshot),
        )
        for key, value in default_doc.modules.items()
    }
    for key, value in payload.get("modules", {}).items():
        modules[key] = ModuleEntry(
            enabled=bool(value.get("enabled", False)),
            input=dict(value.get("input", {})),
            results_snapshot=dict(value.get("results_snapshot", {})),
        )

    report = dict(default_doc.report)
    report.update(dict(payload.get("report", {})))

    doc = ProjectDocument(
        schema_version=int(payload.get("schema_version", 1)),
        project=project,
        modules=modules,
        report=report,
    )
    validate_project_document(doc)
    return doc


def dump_project_document(doc: ProjectDocument, path: str | Path | None = None) -> str:
    validate_project_document(doc)
    data = asdict(doc)
    if yaml is not None:
        text = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    else:
        text = json.dumps(data, ensure_ascii=False, indent=2)
    if path is not None:
        Path(path).write_text(text, encoding="utf-8")
    return text


def load_project_document(text_or_path: str | Path) -> ProjectDocument:
    raw = str(text_or_path)
    text: str
    if "\n" not in raw and "\r" not in raw:
        try:
            path = Path(raw)
            if path.exists():
                text = path.read_text(encoding="utf-8")
            else:
                text = raw
        except OSError:
            text = raw
    else:
        text = raw

    if yaml is not None:
        payload = yaml.safe_load(text)
    else:
        payload = json.loads(text)
    if not isinstance(payload, dict):
        raise TypeError("Projektdatei muss ein Mapping / dict enthalten.")
    return _coerce_project_document(payload)
