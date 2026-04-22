from __future__ import annotations

from html import escape
from typing import Any

from ..transfer.modelle import ConnectionActions, SupportAction
from ..verankerung.modelle import AnchorageAssessment, AnchorageInput


def render_plan_preview_svg(
    anchorage: AnchorageInput,
    support_action: SupportAction,
    actions: ConnectionActions | None = None,
) -> str:
    x1, x2, xc = 90, 390, 240
    active_x = x1 if support_action.support_index == 1 else x2
    passive_x = x2 if support_action.support_index == 1 else x1
    result_y = 95
    platform_e = float(support_action.platform_eccentricity_mm or 0.0)
    shift = min(platform_e / 8.0, 48.0)
    result_x = xc + shift if support_action.support_index == 2 else xc - shift
    if platform_e <= 0:
        result_x = xc

    fx = support_action.transferred_fx_Ed
    fy = support_action.transferred_fy_Ed
    arrow_x = (
        f'<line x1="{result_x+80}" y1="{result_y}" x2="{result_x+15}" y2="{result_y}" stroke="#0f766e" stroke-width="3" marker-end="url(#arrow)" />'
        f'<text x="{result_x+18}" y="{result_y-8}" font-size="12" fill="#0f172a">Hx={fx:.2f} kN</text>'
        if abs(fx) > 1e-9 else ''
    )
    arrow_y = (
        f'<line x1="{result_x}" y1="{result_y-82}" x2="{result_x}" y2="{result_y-12}" stroke="#0f766e" stroke-width="3" marker-end="url(#arrow)" />'
        f'<text x="{result_x+8}" y="{result_y-46}" font-size="12" fill="#0f172a">Hy={fy:.2f} kN</text>'
        if abs(fy) > 1e-9 else ''
    )

    if anchorage.support_role == "gleitlager":
        if support_action.slide_direction == "x":
            release = (
                f'<line x1="{active_x-55}" y1="205" x2="{active_x+55}" y2="205" stroke="#64748b" stroke-width="2" stroke-dasharray="6 4" marker-start="url(#arrowSmall)" marker-end="url(#arrowSmall)" />'
                f'<text x="{active_x-28}" y="225" font-size="12" fill="#334155">Gleitachse x</text>'
            )
        else:
            release = (
                f'<line x1="{active_x}" y1="170" x2="{active_x}" y2="240" stroke="#64748b" stroke-width="2" stroke-dasharray="6 4" marker-start="url(#arrowSmall)" marker-end="url(#arrowSmall)" />'
                f'<text x="{active_x+10}" y="208" font-size="12" fill="#334155">Gleitachse y</text>'
            )
    else:
        release = f'<text x="{active_x-36}" y="225" font-size="12" fill="#334155">Festlager</text>'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 260" width="100%" height="260" role="img" aria-label="Plandarstellung">
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#0f766e" /></marker>
    <marker id="arrowSmall" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L7,3 z" fill="#64748b" /></marker>
  </defs>
  <rect x="0" y="0" width="480" height="260" rx="14" fill="#ffffff" />
  <text x="18" y="24" font-size="16" font-weight="700" fill="#0f172a">Plandarstellung · Festlager / Gleitlager</text>
  <line x1="40" y1="180" x2="440" y2="180" stroke="#0f172a" stroke-width="2" />
  <text x="150" y="170" font-size="12" fill="#475569">Linie der Stützstellen / Anschlussachsen</text>
  <circle cx="{x1}" cy="180" r="7" fill="#e2e8f0" stroke="#0f172a" />
  <circle cx="{x2}" cy="180" r="7" fill="#e2e8f0" stroke="#0f172a" />
  <text x="{x1-34}" y="200" font-size="12" fill="#334155">Stützstelle 1</text>
  <text x="{x2-34}" y="200" font-size="12" fill="#334155">Stützstelle 2</text>
  <rect x="60" y="65" width="360" height="38" rx="8" fill="#ccfbf1" stroke="#0f766e" />
  <text x="133" y="88" font-size="13" fill="#134e4a">Balkonplattform / Lastangriffsebene</text>
  <line x1="{result_x}" y1="103" x2="{result_x}" y2="180" stroke="#94a3b8" stroke-dasharray="5 4" />
  <circle cx="{result_x}" cy="{result_y}" r="6" fill="#0f766e" />
  <text x="{result_x+10}" y="{result_y-6}" font-size="12" fill="#0f172a">Resultierende Plattformlast</text>
  <text x="{result_x-35}" y="118" font-size="12" fill="#334155">e_platform={platform_e:.0f} mm</text>
  <rect x="{active_x-18}" y="145" width="36" height="22" rx="3" fill="#99f6e4" stroke="#0f766e" stroke-width="2" />
  <rect x="{passive_x-14}" y="148" width="28" height="18" rx="3" fill="#e5e7eb" stroke="#94a3b8" />
  {release}
  {arrow_x}
  {arrow_y}
  <line x1="{x1}" y1="235" x2="{x2}" y2="235" stroke="#334155" marker-start="url(#arrowSmall)" marker-end="url(#arrowSmall)" />
  <text x="{xc-26}" y="252" font-size="12" fill="#334155">s ≈ {(actions.s if actions else 0.0):.2f} m</text>
  <text x="18" y="40" font-size="12" fill="#334155">Aktive Stützstelle: {support_action.support_index} als {escape(support_action.support_role)}</text>
  <text x="18" y="56" font-size="12" fill="#334155">Lokale Horizontallast: R_h,Ed = {support_action.total_resultant_Ed:.2f} kN</text>
</svg>'''


def render_side_preview_svg(
    anchorage: AnchorageInput,
    support_action: SupportAction,
) -> str:
    wdvs = float(anchorage.wdvs_mm or 0.0)
    spalt = float(anchorage.spalt_mm or 0.0)
    bracket = float(anchorage.bracket_offset_mm or 0.0)
    anchor_plane = float(anchorage.anchor_plane_offset_mm or 0.0)
    e_local = float(support_action.local_eccentricity_mm or 0.0)
    e_platform = float(support_action.platform_eccentricity_mm or 0.0)
    x0, x1 = 30, 90
    scale = 0.7
    x2 = x1 + wdvs * scale
    x3 = x2 + spalt * scale
    x4 = x3 + bracket * scale
    x5 = x4 + anchor_plane * scale
    x_platform = min(x5 + 95, 430)
    dims: list[str] = []

    def dim_line(a: float, b: float, y: float, label: str) -> str:
        if b - a <= 2:
            return ''
        return f'<line x1="{a}" y1="{y}" x2="{b}" y2="{y}" stroke="#64748b" marker-start="url(#arrowSmall)" marker-end="url(#arrowSmall)" /><text x="{(a+b)/2-28}" y="{y-6}" font-size="12" fill="#334155">{escape(label)}</text>'

    dims.extend([
        dim_line(x1, x2, 200, f'WDVS {wdvs:.0f}'),
        dim_line(x2, x3, 220, f'Spalt {spalt:.0f}'),
        dim_line(x3, x4, 240, f'Konsole {bracket:.0f}'),
        dim_line(x4, x5, 260, f'Ankerachse {anchor_plane:.0f}'),
    ])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 310" width="100%" height="310" role="img" aria-label="Seitenansicht">
  <defs>
    <marker id="arrowSmall" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L7,3 z" fill="#64748b" /></marker>
    <marker id="arrowMain" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#0f766e" /></marker>
  </defs>
  <rect x="0" y="0" width="480" height="310" rx="14" fill="#ffffff" />
  <text x="18" y="24" font-size="16" font-weight="700" fill="#0f172a">Seitenansicht · Exzentrizität und Anschluss</text>
  <rect x="{x0}" y="50" width="{x1-x0}" height="130" fill="#cbd5e1" stroke="#64748b" />
  <text x="{x0+18}" y="118" font-size="12" fill="#0f172a" transform="rotate(-90 {x0+18} 118)">Untergrund</text>
  <rect x="{x1}" y="50" width="{max(x2-x1,2)}" height="130" fill="#f1f5f9" stroke="#94a3b8" />
  <text x="{x1+8}" y="118" font-size="12" fill="#334155" transform="rotate(-90 {x1+8} 118)">WDVS</text>
  <line x1="{x2}" y1="50" x2="{x2}" y2="180" stroke="#94a3b8" stroke-dasharray="5 4" />
  <line x1="{x3}" y1="50" x2="{x3}" y2="180" stroke="#94a3b8" stroke-dasharray="5 4" />
  <line x1="{x3}" y1="120" x2="{x_platform}" y2="120" stroke="#0f766e" stroke-width="4" />
  <line x1="{x5}" y1="86" x2="{x5}" y2="154" stroke="#0f766e" stroke-width="3" />
  <circle cx="{x5}" cy="98" r="7" fill="#ffffff" stroke="#0f766e" stroke-width="2" />
  <circle cx="{x5}" cy="142" r="7" fill="#ffffff" stroke="#0f766e" stroke-width="2" />
  <text x="{x_platform+8}" y="114" font-size="12" fill="#0f172a">Plattform / Profil</text>
  <text x="{x5+8}" y="88" font-size="12" fill="#334155">Ankerachse</text>
  {''.join(dims)}
  <line x1="{x1}" y1="62" x2="{x5}" y2="62" stroke="#334155" marker-start="url(#arrowSmall)" marker-end="url(#arrowSmall)" />
  <text x="{(x1+x5)/2-40}" y="54" font-size="12" fill="#334155">e_local={e_local:.0f} mm</text>
  <line x1="{x5}" y1="36" x2="{x_platform}" y2="36" stroke="#334155" marker-start="url(#arrowSmall)" marker-end="url(#arrowSmall)" />
  <text x="{(x5+x_platform)/2-46}" y="28" font-size="12" fill="#334155">e_platform={e_platform:.0f} mm</text>
  <line x1="{x_platform+55}" y1="120" x2="{x_platform+8}" y2="120" stroke="#0f766e" stroke-width="3" marker-end="url(#arrowMain)" />
  <text x="{x_platform+2}" y="104" font-size="12" fill="#0f172a">R_h,Ed={support_action.total_resultant_Ed:.2f} kN</text>
  <path d="M {x_platform-10} 88 A 22 22 0 1 1 {x_platform-11} 152" fill="none" stroke="#0f766e" stroke-width="2.5" marker-end="url(#arrowMain)" />
  <text x="{x_platform+10}" y="162" font-size="12" fill="#0f172a">M_add,Ed={support_action.additional_moment_Ed:.2f} kNm</text>
  <text x="18" y="292" font-size="12" fill="#334155">Stützstelle {support_action.support_index} als {escape(support_action.support_role)} · Gleitachse {escape(support_action.slide_direction)}</text>
</svg>'''


def build_verankerung_feedback(
    anchorage: AnchorageInput,
    assessment: AnchorageAssessment,
    support_action: SupportAction | None,
    action_error: str | None = None,
) -> dict[str, Any]:
    missing: list[str] = []
    hints: list[str] = []
    strengths: list[str] = []

    if action_error:
        missing.append("Wind-Snapshot / Anschlussgrößen aus Modul 01 sind noch nicht konsistent verfügbar.")
    else:
        strengths.append("Anschlussgrößen aus dem Windmodul konnten rekonstruiert werden.")

    if not anchorage.support_type.strip():
        missing.append("Untergrund / Bauteil ist noch nicht spezifiziert.")
    else:
        strengths.append(f"Untergrund ist als '{anchorage.support_type}' dokumentiert.")

    if anchorage.substrate_strength_class.strip() and anchorage.substrate_strength_class != "unbekannt":
        strengths.append(f"Materialgrundlage '{anchorage.substrate_strength_class}' ist erfasst.")
    else:
        missing.append("Materialgrundlage / Festigkeitsklasse ist noch offen.")

    if anchorage.anchor_count > 1 and not anchorage.spacing_mm:
        missing.append("Achsabstände x/y fehlen für die Mehrfachverankerung.")
    elif anchorage.spacing_mm:
        strengths.append("Achsabstände der Ankergruppe sind hinterlegt.")

    if len(anchorage.edge_distances_mm) < 4:
        missing.append("Randabstände sind noch nicht vollständig (links/rechts/oben/unten).")
    else:
        strengths.append("Randabstände sind vollständig erfasst.")

    plate_complete = all(v is not None and v > 0.0 for v in [anchorage.plate_width_mm, anchorage.plate_height_mm, anchorage.plate_thickness_mm])
    if not plate_complete:
        missing.append("Plattengeometrie ist unvollständig.")
    else:
        strengths.append("Plattengeometrie ist vollständig dokumentiert.")

    if anchorage.local_eccentricity_mm <= 0.0:
        missing.append("Lokale Exzentrizität ist noch 0 mm; WDVS/Spalt/Konsole/Ankerachse prüfen.")
    else:
        strengths.append(f"Lokale Exzentrizität e_local = {anchorage.local_eccentricity_mm:.0f} mm erfasst.")

    if anchorage.support_role == "gleitlager":
        hints.append(
            f"Gleitlager ist in {anchorage.slide_direction}-Richtung freigegeben; Reibung und Anschlagwirkung bleiben im Modell offen."
        )
        if support_action is not None and support_action.released_component_Ed > 0.0:
            hints.append(
                f"Freigegebene Komponente = {support_action.released_component_Ed:.2f} kN; prüfen, ob dies konstruktiv zur Schlitzrichtung passt."
            )
    else:
        hints.append("Festlager übernimmt im Modell beide horizontalen Komponenten der betrachteten Stützstelle.")

    hints.extend(assessment.manual_scope[:2])

    present = len(strengths)
    total = present + len(missing)
    completeness = present / total if total > 0 else 1.0
    if completeness >= 0.85 and assessment.overall_status == "ok":
        level = "success"
        summary = "Gute Datengrundlage für die Vorprüfung."
    elif completeness >= 0.6:
        level = "warning"
        summary = "Vorprüfung sinnvoll nutzbar, aber einzelne projektspezifische Angaben fehlen noch."
    else:
        level = "error"
        summary = "Datengrundlage ist noch lückenhaft; die Vorprüfung bleibt deutlich vorläufig."

    return {
        "level": level,
        "summary": summary,
        "completeness": completeness,
        "missing": missing,
        "hints": hints,
        "strengths": strengths,
    }


def _status_color(status: str) -> str:
    return {
        "ok": "#166534",
        "open": "#92400e",
        "manual": "#9a3412",
        "fail": "#991b1b",
    }.get(status, "#334155")


def render_assessment_badges(assessment: AnchorageAssessment) -> str:
    chips = []
    for item in assessment.checks:
        chips.append(
            f'<span style="display:inline-block;margin:4px 6px 0 0;padding:4px 8px;border-radius:999px;background:#f8fafc;border:1px solid #e2e8f0;color:{_status_color(item.status)};font-size:12px;">{escape(item.title)} · {escape(item.status)}</span>'
        )
    return "".join(chips)
