from __future__ import annotations

from math import hypot

from ..transfer.modelle import ConnectionActions, SupportAction
from .modelle import AnchorageAssessment, AnchorageInput, CheckItem


MANUAL_SCOPE_DEFAULT = [
    "Vollständiger Tragfähigkeitsnachweis der Verankerung nach projektspezifischer Grundlage.",
    "Bemessung von Randabständen, Achsabständen und Betonausbruch / Stahlversagen.",
    "Plausibilisierung der Anschlusssteifigkeit, Exzentrizitäten und Lastverteilung im Gesamtsystem.",
    "Beim Gleitlager: Reibung, Schlitzende, Montagevorspannung und Anschlagwirkung separat bewerten.",
]


def _has_complete_edges(anchorage: AnchorageInput) -> bool:
    return all(key in anchorage.edge_distances_mm for key in ("left", "right", "top", "bottom"))


def _has_plausible_spacing(anchorage: AnchorageInput) -> bool:
    if anchorage.anchor_count <= 1:
        return True
    return "x" in anchorage.spacing_mm or "y" in anchorage.spacing_mm


def _strategy_detail(anchorage: AnchorageInput) -> tuple[str, str]:
    if anchorage.manufacturer_mode == "hilti_doc":
        return (
            "open",
            "Es ist eine dokumentierte Hersteller-/PROFIS-Grundlage vorgesehen; die hier ausgewiesenen Größen dienen als Lastübergabe.",
        )
    if anchorage.manufacturer_mode == "precheck":
        return (
            "open",
            "Vorprüfung vorgesehen; vollständige Bemessung bleibt projektspezifisch offen.",
        )
    return (
        "manual",
        "Nur manuelle / dokumentierende Bearbeitung vorgesehen; vollständiger Nachweis ist nicht Teil dieses Moduls.",
    )


def assess_anchorage(
    actions: ConnectionActions,
    anchorage: AnchorageInput,
    support_action: SupportAction | None = None,
) -> AnchorageAssessment:
    """Einfache, ehrliche Vorprüfung ohne vorgetäuschten Vollnachweis."""
    checks: list[CheckItem] = []
    geometry_summary: list[str] = []
    basis_summary: list[str] = []
    decisive_notes: list[str] = []

    horizontal_resultant = hypot(actions.Hx_Ed, actions.Hy_1_Ed + actions.Hy_2_Ed)
    basis_summary.append(f"Transfermodell: {actions.model_name}")
    basis_summary.append(f"Quellmodul: {actions.source}")
    basis_summary.append(f"Resultierende Horizontallast R_h,Ed ≈ {horizontal_resultant:.2f} kN")
    decisive_notes.append(actions.note)

    if support_action is not None:
        basis_summary.append(
            f"Stützstelle {support_action.support_index}: Fx,Ed = {support_action.base_fx_Ed:.2f} kN, Fy,Ed = {support_action.base_fy_Ed:.2f} kN"
        )
        basis_summary.append(
            f"Zusatzmoment aus Exzentrizität M_add,Ed = {support_action.additional_moment_Ed:.2f} kNm"
        )
        decisive_notes.append(support_action.note)

    if anchorage.anchor_count <= 0:
        checks.append(CheckItem(
            title="Ankeranzahl",
            status="fail",
            detail="Es wurde keine gültige Anzahl an Verankerungen angegeben.",
        ))
    else:
        checks.append(CheckItem(
            title="Ankeranzahl",
            status="ok",
            detail=f"{anchorage.anchor_count} Verankerungen als Eingangsgröße gesetzt ({anchorage.anchor_group_shape}).",
        ))
        geometry_summary.append(f"Ankergruppe: {anchorage.anchor_group_shape} / {anchorage.anchor_designation}")

    if abs(actions.Hx_Ed) + abs(actions.Hy_1_Ed) + abs(actions.Hy_2_Ed) <= 0.0:
        checks.append(CheckItem(
            title="Lastübergabe aus Windmodul",
            status="fail",
            detail="Keine auswertbaren Anschlusslasten vorhanden.",
        ))
    else:
        checks.append(CheckItem(
            title="Lastübergabe aus Windmodul",
            status="ok",
            detail=(
                f"Hx,Ed = {actions.Hx_Ed:.2f} kN, Hy1,Ed = {actions.Hy_1_Ed:.2f} kN, "
                f"Hy2,Ed = {actions.Hy_2_Ed:.2f} kN, M_A,k = {actions.M_A_k:.2f} kNm."
            ),
        ))

    if actions.s <= 0.0:
        checks.append(CheckItem(
            title="Transfermodell / Auflagerabstand",
            status="fail",
            detail="Der Auflagerabstand s ist nicht positiv; die Lastumlagerung ist damit nicht plausibel rekonstruierbar.",
        ))
    else:
        checks.append(CheckItem(
            title="Transfermodell / Auflagerabstand",
            status="ok",
            detail=f"Auflagerabstand s = {actions.s:.3f} m wurde aus dem Windmodul übernommen.",
        ))
        basis_summary.append(f"Auflagerabstand s = {actions.s:.3f} m")

    checks.append(CheckItem(
        title="Lagerrolle / Stützstelle",
        status="open",
        detail=(
            f"Stützstelle {anchorage.support_index} als {anchorage.support_role} modelliert"
            + (f" mit freier {anchorage.slide_direction}-Richtung." if anchorage.support_role == "gleitlager" else ".")
        ),
    ))
    geometry_summary.append(
        f"Lagerkinematik: Stützstelle {anchorage.support_index} / {anchorage.support_role} / Gleitachse {anchorage.slide_direction}"
    )

    local_ecc = anchorage.local_eccentricity_mm
    if local_ecc > 0.0 or (anchorage.platform_eccentricity_mm or 0.0) > 0.0:
        checks.append(CheckItem(
            title="Exzentrizität Anschluss / Plattform",
            status="open",
            detail=(
                f"e_local = {local_ecc:.1f} mm, e_platform = {(anchorage.platform_eccentricity_mm or 0.0):.1f} mm; "
                "Zusatzmoment wird im vereinfachten Stützstellenmodell berücksichtigt."
            ),
        ))
        geometry_summary.append(
            f"Hebelarme [mm]: WDVS={(anchorage.wdvs_mm or 0.0):.0f}, Spalt={(anchorage.spalt_mm or 0.0):.0f}, Konsole={(anchorage.bracket_offset_mm or 0.0):.0f}, Ankerachse={(anchorage.anchor_plane_offset_mm or 0.0):.0f}, e_platform={(anchorage.platform_eccentricity_mm or 0.0):.0f}"
        )
    else:
        checks.append(CheckItem(
            title="Exzentrizität Anschluss / Plattform",
            status="manual",
            detail="Es wurden noch keine lokalen Hebelarme bzw. keine Plattform-Exzentrizität erfasst.",
        ))

    if support_action is not None:
        if support_action.support_role == "gleitlager":
            status = "open" if support_action.released_component_Ed > 0.0 else "ok"
            checks.append(CheckItem(
                title="Gleitrichtung / freigegebene Komponente",
                status=status,
                detail=(
                    f"In {support_action.slide_direction}-Richtung werden idealisiert {support_action.released_component_Ed:.2f} kN freigegeben; "
                    "Reibung und Anschlagwirkung bleiben offen."
                ),
            ))
        else:
            checks.append(CheckItem(
                title="Festlagerwirkung",
                status="open",
                detail=(
                    f"Festlager übernimmt Fx,Ed = {support_action.transferred_fx_Ed:.2f} kN und "
                    f"Fy,Ed = {support_action.transferred_fy_Ed:.2f} kN im vereinfachten Stützstellenmodell."
                ),
            ))
        checks.append(CheckItem(
            title="Lokale Stützstellenlasten",
            status="open",
            detail=(
                f"Übertragene lokale Größen: Fx,Ed = {support_action.transferred_fx_Ed:.2f} kN, "
                f"Fy,Ed = {support_action.transferred_fy_Ed:.2f} kN, M_add,Ed = {support_action.additional_moment_Ed:.2f} kNm."
            ),
        ))

    if not anchorage.edge_distances_mm:
        checks.append(CheckItem(
            title="Randabstände",
            status="manual",
            detail="Randabstände fehlen oder wurden noch nicht projektspezifisch erfasst.",
        ))
    elif _has_complete_edges(anchorage):
        checks.append(CheckItem(
            title="Randabstände",
            status="open",
            detail="Randabstände links/rechts/oben/unten wurden erfasst; normative Prüfung bleibt offen.",
        ))
        geometry_summary.append(
            "Randabstände [mm]: "
            + ", ".join(f"{key}={value:.0f}" for key, value in sorted(anchorage.edge_distances_mm.items()))
        )
    else:
        checks.append(CheckItem(
            title="Randabstände",
            status="manual",
            detail="Randabstände wurden nur teilweise erfasst; vollständige Normprüfung ist noch nicht möglich.",
        ))
        geometry_summary.append(
            "Teilweise Randabstände [mm]: "
            + ", ".join(f"{key}={value:.0f}" for key, value in sorted(anchorage.edge_distances_mm.items()))
        )

    if _has_plausible_spacing(anchorage):
        status = "open" if anchorage.anchor_count > 1 else "ok"
        detail = (
            "Achsabstände wurden erfasst und müssen für die Bemessung normativ geprüft werden."
            if anchorage.anchor_count > 1
            else "Einzelanker: kein zusätzlicher Achsabstand erforderlich."
        )
        if anchorage.spacing_mm:
            geometry_summary.append(
                "Achsabstände [mm]: "
                + ", ".join(f"{key}={value:.0f}" for key, value in sorted(anchorage.spacing_mm.items()))
            )
        checks.append(CheckItem(title="Achsabstände", status=status, detail=detail))
    else:
        checks.append(CheckItem(
            title="Achsabstände",
            status="manual",
            detail="Für Mehrfachverankerungen fehlen Achsabstände x/y; Gruppenwirkung kann noch nicht beurteilt werden.",
        ))

    plate_complete = all(
        value is not None and value > 0.0
        for value in (anchorage.plate_width_mm, anchorage.plate_height_mm, anchorage.plate_thickness_mm)
    )
    if plate_complete:
        checks.append(CheckItem(
            title="Anschlussplatte / Lasche",
            status="open",
            detail=(
                f"Plattengeometrie {anchorage.plate_width_mm:.0f} x {anchorage.plate_height_mm:.0f} x "
                f"{anchorage.plate_thickness_mm:.0f} mm ist dokumentiert; lokaler Stahlbau-/Pressungsnachweis bleibt offen."
            ),
        ))
        geometry_summary.append(
            f"Platte [mm]: {anchorage.plate_width_mm:.0f} x {anchorage.plate_height_mm:.0f} x {anchorage.plate_thickness_mm:.0f}"
        )
    else:
        checks.append(CheckItem(
            title="Anschlussplatte / Lasche",
            status="manual",
            detail="Plattenabmessungen und/oder Plattendicke sind unvollständig; lokaler Anschlussnachweis ist noch nicht möglich.",
        ))

    if anchorage.support_type.strip():
        checks.append(CheckItem(
            title="Untergrund / Bauteil",
            status="open",
            detail=f"Untergrund wurde als '{anchorage.support_type}' angegeben; Materialkennwerte und Aufbau sind projektspezifisch zu verifizieren.",
        ))
        geometry_summary.append(f"Untergrund: {anchorage.support_type}")
    else:
        checks.append(CheckItem(
            title="Untergrund / Bauteil",
            status="manual",
            detail="Untergrund / Bauteil ist noch nicht spezifiziert.",
        ))

    if anchorage.substrate_strength_class and anchorage.substrate_strength_class != "unbekannt":
        checks.append(CheckItem(
            title="Materialgrundlage Untergrund",
            status="open",
            detail=f"Material-/Festigkeitsangabe '{anchorage.substrate_strength_class}' wurde erfasst; Plausibilisierung im Nachweis erforderlich.",
        ))
        geometry_summary.append(f"Materialgrundlage: {anchorage.substrate_strength_class}")
    else:
        checks.append(CheckItem(
            title="Materialgrundlage Untergrund",
            status="manual",
            detail="Material- bzw. Festigkeitsklasse des Untergrunds fehlt noch.",
        ))

    strategy_status, strategy_detail = _strategy_detail(anchorage)
    checks.append(CheckItem(title="Nachweisstrategie", status=strategy_status, detail=strategy_detail))

    if anchorage.note.strip():
        decisive_notes.append(anchorage.note.strip())

    overall = "ok"
    if any(item.status == "fail" for item in checks):
        overall = "fail"
    elif any(item.status == "manual" for item in checks):
        overall = "manual"
    elif any(item.status == "open" for item in checks):
        overall = "open"

    return AnchorageAssessment(
        overall_status=overall,
        checks=checks,
        manual_scope=list(MANUAL_SCOPE_DEFAULT),
        basis_summary=basis_summary,
        geometry_summary=geometry_summary,
        decisive_notes=decisive_notes,
    )
