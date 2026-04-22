from __future__ import annotations

from math import hypot

from .modelle import ConnectionActions, SlideDirection, SupportAction, SupportRole


def derive_support_action(
    actions: ConnectionActions,
    *,
    support_index: int,
    support_role: SupportRole = "festlager",
    slide_direction: SlideDirection = "x",
    local_eccentricity_mm: float = 0.0,
    platform_eccentricity_mm: float = 0.0,
) -> SupportAction:
    """Leitet lokale Lagergrößen für Festlager/Gleitlager aus dem Wind-Snapshot ab.

    Modellannahmen:
    - Hx wird gleichmäßig auf beide Stützstellen verteilt.
    - Hy_1 / Hy_2 werden als jeweilige Stützreaktionen in der zweiten Horizontalrichtung interpretiert.
    - Das Gleitlager setzt die freigegebene Richtung ideal auf null; Reibung, Anschläge und Schlitzenden
      werden bewusst nicht mitmodelliert.
    - Exzentrizität wird als lokaler Hebel `e = e_platform + e_local` angesetzt und erzeugt
      ein Zusatzmoment `M_add,Ed = |F_transferred| * e`.
    """

    if support_index not in (1, 2):
        raise ValueError("support_index muss 1 oder 2 sein.")

    base_fx = actions.Hx_Ed / 2.0
    base_fy = actions.Hy_1_Ed if support_index == 1 else actions.Hy_2_Ed

    transferred_fx = base_fx
    transferred_fy = base_fy
    released_component = 0.0

    if support_role == "gleitlager":
        if slide_direction == "x":
            released_component = abs(base_fx)
            transferred_fx = 0.0
        else:
            released_component = abs(base_fy)
            transferred_fy = 0.0

    total_resultant = hypot(transferred_fx, transferred_fy)
    e_total_m = max(local_eccentricity_mm, 0.0) / 1000.0 + max(platform_eccentricity_mm, 0.0) / 1000.0
    additional_moment = total_resultant * e_total_m

    trace = [
        f"Basisreaktion Stützstelle {support_index}: Fx,Ed = Hx,Ed/2 = {base_fx:.3f} kN, Fy,Ed = {base_fy:.3f} kN.",
        f"Lagerrolle: {support_role}, Gleitrichtung: {slide_direction}.",
    ]
    if support_role == "gleitlager":
        trace.append(
            f"Freigegebene Komponente in {slide_direction}-Richtung idealisiert zu null gesetzt: {released_component:.3f} kN."
        )
    trace.append(
        f"Lokaler Hebel e_local = {local_eccentricity_mm:.1f} mm, Plattform-Exzentrizität e_platform = {platform_eccentricity_mm:.1f} mm."
    )
    trace.append(
        f"Zusatzmoment aus Exzentrizität: M_add,Ed = {additional_moment:.3f} kNm."
    )

    note = (
        "Kinematisches Stützstellenmodell mit idealisiertem Festlager/Gleitlager. "
        "Reibung, Schlitzende, Montagevorspannung und dreidimensionale Steifigkeiten sind nicht berücksichtigt."
    )
    return SupportAction(
        support_index=support_index,
        support_role=support_role,
        slide_direction=slide_direction,
        source_model="support_distribution_v1",
        base_fx_Ed=base_fx,
        base_fy_Ed=base_fy,
        transferred_fx_Ed=transferred_fx,
        transferred_fy_Ed=transferred_fy,
        released_component_Ed=released_component,
        local_eccentricity_mm=float(local_eccentricity_mm),
        platform_eccentricity_mm=float(platform_eccentricity_mm),
        additional_moment_Ed=additional_moment,
        total_resultant_Ed=total_resultant,
        note=note,
        trace=trace,
    )
