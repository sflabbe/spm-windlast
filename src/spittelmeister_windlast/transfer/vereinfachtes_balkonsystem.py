from __future__ import annotations

from .modelle import ConnectionActions


DEFAULT_GAMMA_Q = 1.5
DEFAULT_NOTE = (
    "Festlager/Gleitlager-Modell in Draufsicht; y-Reaktionen nur aus statischem "
    "Gleichgewicht ohne Verformungskompatibilität."
)


def derive_connection_actions_simple(
    *,
    B: float,
    T: float,
    b: float,
    hw_yz: float,
    hw_xz: float,
    we_side_pressure: float,
    we_side_suction: float,
    we_front_suction: float,
    gamma_Q: float = DEFAULT_GAMMA_Q,
) -> ConnectionActions:
    """Extrahierte Vorbemessungslogik für das vereinfachte Balkonsystem."""
    if B <= 0:
        raise ValueError("Breite B muss > 0 sein.")
    if T <= 0:
        raise ValueError("Tiefe T muss > 0 sein.")
    if hw_yz <= 0 or hw_xz <= 0:
        raise ValueError("Windflächenhöhen müssen > 0 sein.")
    if b < 0:
        raise ValueError("Randabstand b muss >= 0 sein.")

    s = B - 2.0 * b
    if s <= 0:
        raise ValueError("Ungültige Geometrie: B - 2*b muss > 0 sein.")

    q_seite_1 = abs(we_side_pressure) * hw_yz
    q_seite_2 = abs(we_side_suction) * hw_yz
    q_vorne = abs(we_front_suction) * hw_xz

    Hx_k = T * (q_seite_1 + q_seite_2)
    M_A_k = (T**2 / 2.0) * (q_seite_1 + q_seite_2) + q_vorne * B * (B / 2.0 - b)
    Hy_2_k = M_A_k / s
    Hy_1_k = q_vorne * B - Hy_2_k

    return ConnectionActions(
        q_seite_1=q_seite_1,
        q_seite_2=q_seite_2,
        q_vorne=q_vorne,
        s=s,
        auflagerabstand=s,
        Hx_k=Hx_k,
        Hx_Ed=gamma_Q * Hx_k,
        Hy_1_k=Hy_1_k,
        Hy_1_Ed=gamma_Q * Hy_1_k,
        Hy_2_k=Hy_2_k,
        Hy_2_Ed=gamma_Q * Hy_2_k,
        M_A_k=M_A_k,
        gamma_Q=gamma_Q,
        note=DEFAULT_NOTE,
        trace=[
            f"q_seite_1 = |we_side_pressure| * hw_yz = {q_seite_1:.3f} kN/m",
            f"q_seite_2 = |we_side_suction| * hw_yz = {q_seite_2:.3f} kN/m",
            f"q_vorne = |we_front_suction| * hw_xz = {q_vorne:.3f} kN/m",
            f"Hx_k = T * (q_seite_1 + q_seite_2) = {Hx_k:.3f} kN",
            f"M_A_k = {M_A_k:.3f} kNm",
            f"Hy_2_k = M_A_k / s = {Hy_2_k:.3f} kN",
            f"Hy_1_k = q_vorne * B - Hy_2_k = {Hy_1_k:.3f} kN",
        ],
    )
