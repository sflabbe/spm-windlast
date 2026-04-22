from spittelmeister_windlast.projectio import ProjectDocument, dump_project_document, load_project_document
from spittelmeister_windlast.report.report_selection import ReportSelection
from spittelmeister_windlast.transfer import ConnectionActions, derive_connection_actions_simple
from spittelmeister_windlast.verankerung import AnchorageInput, assess_anchorage


def test_transfer_and_verankerung_scaffold_roundtrip():
    actions = derive_connection_actions_simple(
        B=4.93,
        T=1.425,
        b=0.15,
        hw_yz=3.0,
        hw_xz=3.0,
        we_side_pressure=0.76,
        we_side_suction=-1.10,
        we_front_suction=-1.30,
    )
    assert isinstance(actions, ConnectionActions)
    assessment = assess_anchorage(actions, AnchorageInput(anchor_count=2, manufacturer_mode="precheck"))
    assert assessment.overall_status in {"ok", "open", "manual"}


def test_projectio_scaffold_dump_and_load():
    doc = ProjectDocument()
    text = dump_project_document(doc)
    loaded = load_project_document(text)
    assert loaded.project.project_id == doc.project.project_id


def test_report_selection_labels():
    selection = ReportSelection()
    labels = selection.selected_module_labels()
    assert "Windlast" in labels
