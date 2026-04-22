from __future__ import annotations

from .models import ProjectDocument


def validate_project_document(doc: ProjectDocument) -> None:
    if doc.schema_version < 1:
        raise ValueError("schema_version muss >= 1 sein.")
