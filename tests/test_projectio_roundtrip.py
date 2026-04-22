from __future__ import annotations

from spittelmeister_windlast.projectio import ProjectDocument, load_project_document, dump_project_document


def test_project_document_roundtrip_preserves_core_fields():
    doc = ProjectDocument()
    doc.project.title = "Windlast Testprojekt"
    doc.modules["windlast"].input = {"windzone": 2, "gelaende": "binnen"}
    text = dump_project_document(doc)
    loaded = load_project_document(text)
    assert loaded.project.title == "Windlast Testprojekt"
    assert loaded.modules["windlast"].input["windzone"] == 2
    assert "verankerung" in loaded.modules


def test_project_document_loader_merges_missing_defaults():
    loaded = load_project_document(
        """
        schema_version: 1
        project:
          title: Teilprojekt
        modules:
          windlast:
            enabled: true
            input:
              windzone: 3
        """
    )
    assert loaded.project.title == "Teilprojekt"
    assert loaded.modules["windlast"].input["windzone"] == 3
    assert "verankerung" in loaded.modules
    assert loaded.report["selection"]["windlast"]["include"] is True
