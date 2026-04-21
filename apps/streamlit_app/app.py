"""
Windlast-Rechner — Spittelmeister GmbH
Streamlit-Webinterface für DIN EN 1991-1-4 / NA:2010-12

Starten:
    streamlit run app.py

Voraussetzungen:
    pip install streamlit pandas geopy folium streamlit-folium requests
    pdflatex muss installiert sein (TeX Live)
"""

import streamlit as st
import base64
import tempfile
import os
import pandas as pd
from datetime import date

from spittelmeister_windlast.utils.assets import get_asset_path

from spittelmeister_windlast import WindlastBerechnung, Projekt, Standort, Geometrie
from spittelmeister_windlast.report import export_pdf

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Windlast-Rechner | Spittelmeister", layout="wide", initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stButton>button {
        background-color:#1e5080;color:white;border-radius:6px;border:none;
        padding:0.5rem 2rem;font-weight:bold;font-size:1rem;width:100%;
    }
    .stButton>button:hover{background-color:#16406a;}
    .result-box{background:#e8f0f8;border-left:5px solid #1e5080;
        border-radius:6px;padding:1.2rem 1.5rem;margin:0.5rem 0;}
    .result-value{font-size:2rem;font-weight:bold;color:#1e5080;}
    .result-label{font-size:0.85rem;color:#555;margin-bottom:0.1rem;}
    .warn-box{background:#fff3cd;border-left:5px solid #e67e22;
        border-radius:6px;padding:0.8rem 1.2rem;margin:0.5rem 0;}
    .ok-box{background:#d4edda;border-left:5px solid #27ae60;
        border-radius:6px;padding:0.8rem 1.2rem;margin:0.5rem 0;}
    .section-header{background:#1e5080;color:white;padding:0.4rem 1rem;
        border-radius:4px;font-weight:bold;margin:1rem 0 0.5rem 0;}
    h1{color:#1e5080!important;}
    footer{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ── HEADER ──
col_logo, col_title = st.columns([1, 5])
st.markdown("# Windlast-Rechner")
st.markdown("**Spittelmeister GmbH** · DIN EN 1991-1-4 / NA:2010-12 · Balkonabschlüsse")
st.markdown("---")

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("### 📋 Projektdaten")
    proj_bez   = st.text_input("Projektbezeichnung", value="Projekt XY — Balkonabschluss")
    proj_nr    = st.text_input("Projektnummer",       value="2025-WB-001")
    bearbeiter = st.text_input("Bearbeiter",           value="")
    datum      = st.date_input("Datum",                value=date.today())
    st.markdown("---")
    st.info("Gilt für **geschlossene Balkonabschlüsse** §7.2.2.\n\n"
            "cpe,1, Stirnseiten, Fassadenbekleidung → gesondert nachweisen.")
    st.markdown("---")
    st.caption("v1.2 · Statik-Abteilung Spittelmeister")

# ── TABS ──
tab_geo, tab_calc, tab_ref = st.tabs(["📍 Standortsuche", "⚡ Berechnung & PDF", "📖 Referenztabellen"])

QB0_REF = {1: 0.32, 2: 0.39, 3: 0.47, 4: 0.56}


def _render_svg_asset(filename: str, caption: str) -> None:
    """Zeigt ein SVG-Asset robust per Data-URI an."""
    try:
        svg_text = get_asset_path(filename).read_text(encoding="utf-8")
        svg_b64 = base64.b64encode(svg_text.encode("utf-8")).decode("ascii")
        st.markdown(
            f'<div style="text-align:center"><img src="data:image/svg+xml;base64,{svg_b64}" '
            f'style="max-width:100%;border:1px solid #d1d5db;border-radius:4px;"/></div>',
            unsafe_allow_html=True,
        )
        st.caption(caption)
    except FileNotFoundError:
        st.warning(f"Diagramm nicht gefunden: {filename}")

def qp_vorschau(z, windzone, gelaende):
    qb0 = QB0_REF[windzone]
    if gelaende == "binnen":
        if z <= 7:
            return 1.5 * qb0, "NA.B.1"
        if z <= 50:
            return 1.7 * qb0 * (z / 10) ** 0.37, "NA.B.2"
        return 2.1 * qb0 * (z / 10) ** 0.24, "NA.B.3"
    if gelaende == "kueste":
        if z <= 4:
            return 1.8 * qb0, "NA.B.4"
        if z <= 50:
            return 2.3 * qb0 * (z / 10) ** 0.27, "NA.B.5"
        return 2.6 * qb0 * (z / 10) ** 0.19, "NA.B.6"
    if z <= 2:
        return 1.1, "NA.B.7"
    return 1.05 * (z / 10) ** 0.19, "NA.B.8"

if "generated_pdf_bytes" not in st.session_state:
    st.session_state.generated_pdf_bytes = None
if "generated_pdf_name" not in st.session_state:
    st.session_state.generated_pdf_name = None
if "generated_result" not in st.session_state:
    st.session_state.generated_result = None
if "generated_error" not in st.session_state:
    st.session_state.generated_error = None

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — STANDORTSUCHE
# ═══════════════════════════════════════════════════════════════════════════
with tab_geo:
    st.markdown("### 📍 Standort automatisch ermitteln")
    st.markdown(
        "Adresse eingeben → **Windzone**, **Höhe ü. NN** und **Geländekategorie** "
        "werden automatisch bestimmt (OpenStreetMap Nominatim + SRTM-Höhenmodell)."
    )

    a1, a2 = st.columns([4, 1])
    with a1:
        adresse = st.text_input("Adresse", placeholder="z.B. Marktplatz 1, 97070 Würzburg",
                                label_visibility="collapsed")
    with a2:
        suchen = st.button("🔍 Suchen", use_container_width=True)

    if "geo_result" not in st.session_state:
        st.session_state.geo_result = None

    if suchen and adresse:
        with st.spinner("Standort wird ermittelt..."):
            try:
                from spittelmeister_windlast.geo import standort_ermitteln
                st.session_state.geo_result = standort_ermitteln(adresse)
            except Exception as ex:
                st.error("Standort konnte nicht automatisch ermittelt werden.")
                st.caption(f"Details: {ex}")
                st.info("Tipp: Adresse präziser eingeben, z.B. mit PLZ und Stadt.")

    if st.session_state.geo_result:
        r = st.session_state.geo_result
        wz_colors = {1:"#27ae60", 2:"#f39c12", "2*":"#e67e22", 3:"#e74c3c", 4:"#8e44ad"}
        wz_col = wz_colors.get(r.windzone, "#1e5080")

        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(
            f'<div class="result-box"><div class="result-label">Windzone</div>'
            f'<div class="result-value" style="color:{wz_col}">WZ {r.windzone}</div>'
            f'<div class="result-label">{r.windzone_quelle}</div></div>',
            unsafe_allow_html=True)
        if r.hoehe_uNN:
            k2.markdown(
                f'<div class="result-box"><div class="result-label">Höhe ü. NN</div>'
                f'<div class="result-value">{r.hoehe_uNN:.0f} m</div>'
                f'<div class="result-label">{r.hoehe_quelle}</div></div>',
                unsafe_allow_html=True)
        else:
            k2.markdown('<div class="warn-box">⚠️ Höhe nicht verfügbar<br><small>Manuell eingeben</small></div>',
                        unsafe_allow_html=True)
        gelaende_display = {"binnen":"Binnenland", "kueste":"Küste/Ostsee", "nordsee":"Nordsee"}.get(r.gelaende, r.gelaende)
        k3.markdown(
            f'<div class="result-box"><div class="result-label">Geländekategorie</div>'
            f'<div class="result-value">{gelaende_display}</div>'
            f'<div class="result-label">{r.gelaende_begruendung}</div></div>',
            unsafe_allow_html=True)
        k4.markdown(
            f'<div class="result-box"><div class="result-label">Bundesland / Kreis</div>'
            f'<div class="result-value" style="font-size:1.1rem">{r.bundesland}</div>'
            f'<div class="result-label">{r.county}</div></div>',
            unsafe_allow_html=True)

        st.caption(f"📌 {r.adresse_gefunden}")
        ns = "N" if r.lat >= 0 else "S"
        ew = "E" if r.lon >= 0 else "W"
        st.caption(f"🌐 {abs(r.lat):.5f}°{ns}, {abs(r.lon):.5f}°{ew}")

        try:
            import folium
            from streamlit_folium import st_folium
            mc = {1:"green", 2:"orange", "2*":"orange", 3:"red", 4:"purple"}
            m = folium.Map(location=[r.lat, r.lon], zoom_start=12)
            folium.Marker(
                [r.lat, r.lon],
                popup=folium.Popup(
                    f"<b>{r.adresse_gefunden[:60]}</b><br>"
                    f"WZ {r.windzone} · {f'{r.hoehe_uNN:.0f}' if r.hoehe_uNN else '?'} m ü.NN",
                    max_width=300),
                tooltip=f"WZ {r.windzone}",
                icon=folium.Icon(color=mc.get(r.windzone,"blue"), icon="home", prefix="fa"),
            ).add_to(m)
            st_folium(m, width=None, height=380, returned_objects=[])
        except ImportError:
            st.info("`pip install folium streamlit-folium` für Kartenansicht.")

        st.markdown("---")
        if st.button("➡️ Werte in Berechnung übernehmen"):
            st.session_state.auto_windzone  = r.windzone if r.windzone in [1,2,3,4] else 2
            st.session_state.auto_gelaende  = r.gelaende
            st.session_state.auto_hoehe_uNN = float(r.hoehe_uNN) if r.hoehe_uNN else 0.0
            st.session_state.auto_standort  = r.adresse_gefunden or r.county or r.bundesland
            st.session_state.switch_to_calc = True
            st.rerun()

        if st.session_state.get("switch_to_calc"):
            st.session_state.switch_to_calc = False
            st.markdown("""
            <script>
            (function() {
                const tryClick = () => {
                    const tabs = window.parent.document.querySelectorAll('button[role="tab"]');
                    if (tabs.length >= 2) { tabs[1].click(); }
                    else { setTimeout(tryClick, 100); }
                };
                setTimeout(tryClick, 150);
            })();
            </script>
            """, unsafe_allow_html=True)

    else:
        try:
            import folium
            from streamlit_folium import st_folium
            m_de = folium.Map(location=[51.2, 10.5], zoom_start=6)
            st_folium(m_de, width=None, height=420, returned_objects=[])
        except ImportError:
            st.info("Adresse eingeben und auf 🔍 Suchen klicken.")


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — BERECHNUNG & PDF
# ═══════════════════════════════════════════════════════════════════════════
with tab_calc:
    col_left, col_right = st.columns(2, gap="large")

    auto_standort = st.session_state.get("auto_standort",  "Würzburg")
    auto_hoehe    = st.session_state.get("auto_hoehe_uNN", 192.0)
    auto_wz       = st.session_state.get("auto_windzone",  1)
    auto_gel      = st.session_state.get("auto_gelaende",  "binnen")
    auto_wz_idx   = [1,2,3,4].index(auto_wz) if auto_wz in [1,2,3,4] else 0

    with col_left:
        st.markdown('<div class="section-header">📐 Geometrie</div>', unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            h_gebaeude = st.number_input("Gebäudehöhe h [m]", 1.0, 300.0, 15.13, 0.1)
            d_gebaeude = st.number_input("Gebäudetiefe d [m]", 1.0, 200.0, 12.55, 0.1)
            b_gebaeude = st.number_input("Gebäudebreite b [m]", 1.0, 300.0, 20.0, 0.1)
        with g2:
            z_balkon = st.number_input("OK Balkonabschluss ze [m]", 0.5, 300.0, 12.83, 0.1)
            e_balkon = st.number_input("Ausladung Balkon [m]", 0.1, 10.0, 1.425, 0.05)
            h_abschl = st.number_input("Höhe Abschlusselement [m]", 0.5, 10.0, 3.00, 0.05)
        s_verank = st.number_input("Achsabstand Verankerungen / Isokörbe [m]", 0.1, 20.0, 4.93, 0.01)
        b_auflager_rand = st.number_input("Abstand Ecke bis Auflage b [m]", 0.0, 10.0, 0.30, 0.01)
        A_ref = s_verank * h_abschl
        h_d_eff = max(h_gebaeude/d_gebaeude, h_gebaeude/b_gebaeude)
        st.caption(f"h/d = max(h/d, h/b) = {h_d_eff:.3f} · Aref = {A_ref:.2f} m²")
        st.caption(f"Frontfläche = {s_verank*h_abschl:.2f} m² · Seitenfläche = {e_balkon*h_abschl:.2f} m²")
                
        st.markdown('<div class="section-header">📍 Standort &amp; Windzone</div>', unsafe_allow_html=True)
        standort_bez = st.text_input("Standortbezeichnung", value=auto_standort)
        hoehe_uNN    = st.number_input("Höhe über NN [m]", 0.0, 2000.0, float(auto_hoehe), 5.0)
        wz_col2, gel_col2 = st.columns(2)
        with wz_col2:
            windzone = st.selectbox("Windzone", [1,2,3,4], index=auto_wz_idx,
                                    help="Via Tab Standortsuche automatisch befüllen")
        with gel_col2:
            gelaende_options = ["binnen", "kueste", "nordsee"]
            default_idx = gelaende_options.index(auto_gel) if auto_gel in gelaende_options else 0
            gelaende = st.selectbox(
                "Geländekategorie",
                gelaende_options,
                index=default_idx,
                format_func=lambda x: {
                    "binnen": "II / III Binnenland",
                    "kueste": "I / II Küstennähe / Ostseeinseln",
                    "nordsee": "I Nordseeinseln",
                }[x],
            )
        qb0 = QB0_REF[windzone]
        st.caption(f"qb,0 = {qb0:.2f} kN/m² · {{'binnen':'II/III Binnenland','kueste':'I/II Küstennähe / Ostseeinseln','nordsee':'I Nordseeinseln'}}[gelaende]")
        c1,c2,c3 = st.columns(3)
        v1, f1 = qp_vorschau(4, windzone, gelaende)
        v2, f2 = qp_vorschau(13.7, windzone, gelaende)
        v3, f3 = qp_vorschau(25, windzone, gelaende)
        c1.metric("h = 4 m", f"{v1:.3f} kN/m²")
        c2.metric("h = 13.7 m", f"{v2:.3f} kN/m²")
        c3.metric("h = 25 m", f"{v3:.3f} kN/m²")
        st.caption(f"Ansatz bei h = 13.7 m: {f2}")

    with col_right:
        st.markdown("#### Geometrie")
        _render_svg_asset(
            "wind_geb.svg",
            "Gebäudegeometrie"
        )
        _render_svg_asset(
            "balcony_system.svg",
            "Balkongeometrie"
        )

    st.markdown("---")
    bc, _ = st.columns([2, 5])
    with bc:
        berechnen = st.button("⚡ Berechnen & PDF erzeugen")

    if berechnen:
        st.session_state.generated_error = None
        with st.spinner("Läuft..."):
            try:
                wb = WindlastBerechnung(
                    Projekt(proj_bez, proj_nr, bearbeiter, datum.strftime("%d.%m.%Y")),
                    Standort(standort_bez, windzone, gelaende, hoehe_uNN),
                    Geometrie(h_gebaeude, d_gebaeude, b_gebaeude, z_balkon, e_balkon, h_abschl, s_verank, b_auflager_rand),
                )
                e = wb.berechnen()

                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    pdf_path = tmp.name
                wb.export_pdf(pdf_path)
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                os.unlink(pdf_path)

                st.session_state.generated_result = e
                st.session_state.generated_pdf_bytes = pdf_bytes
                st.session_state.generated_pdf_name = (
                    f"Windlast_{standort_bez.replace(' ','_')}_{datum.strftime('%Y%m%d')}.pdf"
                )
            except Exception as ex:
                st.session_state.generated_error = str(ex)
                st.session_state.generated_result = None
                st.session_state.generated_pdf_bytes = None
                st.session_state.generated_pdf_name = None

    if st.session_state.generated_error:
        st.error(f"Fehler: {st.session_state.generated_error}")

    if st.session_state.generated_result is not None:
        e = st.session_state.generated_result
        st.markdown("## ✅ Ergebnisse")
        r1,r2,r3,r4,r5 = st.columns(5)
        def rc(col, lbl, val, unit):
            col.markdown(
                f'<div class="result-box"><div class="result-label">{lbl}</div>'
                f'<div class="result-value">{val}</div>'
                f'<div class="result-label">{unit}</div></div>', unsafe_allow_html=True)
        rc(r1,"qp(h)",      f"{e.qp:.3f}",           "kN/m²")
        rc(r2,"wk (maßg.)", f"{e.wk_massgebend:.2f}","kN/m²")
        rc(r3,"qh,k",       f"{e.qhk:.2f}",          "kN/m")
        rc(r4,"Hk je Feld", f"{e.Hk:.2f}",           "kN")
        rc(r5,"Mk Fußpunkt",f"{e.Mk:.2f}",           "kNm")

        st.markdown(
            f'<div class="ok-box">📌 <b>{e.lastfall_massgebend}</b> — '
            f'Zone {e.zone_massgebend} · qp: {e.qp_verfahren} · Methodik: {e.methodik} · cscd = {e.cscd:.1f}</div>', unsafe_allow_html=True)

        with st.expander("📊 Zwischenwerte"):
            zq1, zq2, zw1, zw2 = st.columns(4)
            with zq1:
                st.table({"qp-Größe":["qb,0","Faktor","qp(h)"],
                          "Wert":[f"{e.qb0:.2f}",f"{e.qp_faktor:.3f}",f"{e.qp:.3f}"]})
            with zq2:
                st.table({"qp-Hinweis":["Gelände","Normstelle","Ansatz"],
                          "Wert":[e.gelaende_label,e.qp_normstelle,e.qp_verfahren]})
            with zw1:
                st.table({"Bereich":["D (Seite Druck)","E (Seite Sog)","A (Front Sog)"],
                          "cpe,10":[f"+{e.cpe10_D:.2f}",f"{e.cpe10_E:.2f}",f"{e.cpe10_A:.2f}"]})
            with zw2:
                st.table({"Lastfall":["Seite Druck","Seite Sog","Front Sog"],
                          "we [kN/m²]":[f"{e.we_side_pressure:.3f}",f"{e.we_side_suction:.3f}",f"{e.we_front_suction:.3f}"],
                          "q [kN/m]":[f"{e.q_side_pressure:.3f}",f"{e.q_side_suction:.3f}",f"{e.q_front_suction:.3f}"]})
            st.caption(f"Formel qp: {e.qp_formel}")
            st.caption(f"Auswertung qp: {e.qp_auswertung}")
            st.caption(f"Ansatz qp: {e.qp_abschnitt} · {e.qp_normstelle}")

        st.markdown("### Balkonsystem / vereinfachte Reaktionsabschätzung")
        rrx1, rrx2, rrx3, rrx4 = st.columns(4)
        rrx1.metric("q_seite_1 [kN/m]", f"{e.q_seite_1:.3f}")
        rrx2.metric("q_seite_2 [kN/m]", f"{e.q_seite_2:.3f}")
        rrx3.metric("q_vorne [kN/m]", f"{e.q_vorne:.3f}")
        rrx4.metric("Auflagerabstand s = B - 2b [m]", f"{e.s:.3f}")

        rry1, rry2, rry3, rry4, rry5 = st.columns(5)
        rry1.metric("Hx_k [kN]", f"{e.Hx_k:.2f}")
        rry2.metric("Hx_Ed [kN]", f"{e.Hx_Ed:.2f}")
        rry3.metric("Hy_1_k [kN]", f"{e.Hy_1_k:.2f}")
        rry4.metric("Hy_1_Ed [kN]", f"{e.Hy_1_Ed:.2f}")
        rry5.metric("M_A_k [kNm]", f"{e.M_A_k:.2f}")

        rrz1, rrz2 = st.columns(2)
        rrz1.metric("Hy_2_k [kN]", f"{e.Hy_2_k:.2f}")
        rrz2.metric("Hy_2_Ed [kN]", f"{e.Hy_2_Ed:.2f}")

        st.markdown("#### Formelansatz (Draufsicht, Vorbemessung)")
        st.latex(r"H_{x,k}=T\cdot(q_{seite,1}+q_{seite,2})")
        st.latex(
            r"M_{A,k}=\frac{T^2}{2}\cdot(q_{seite,1}+q_{seite,2})+q_{vorne}\cdot B\cdot\left(\frac{B}{2}-b\right)"
        )
        st.latex(r"H_{y,2,k}=M_{A,k}/(B-2b)")
        st.latex(r"H_{y,1,k}=q_{vorne}\cdot B-H_{y,2,k}")

        force_residual = abs((e.Hy_1_k + e.Hy_2_k) - (e.q_vorne * s_verank))
        moment_residual = abs(e.M_A_k - (e.Hy_2_k * e.s))
        if force_residual <= 1e-9 and moment_residual <= 1e-9:
            st.success(
                "Gleichgewicht in Draufsicht geschlossen: "
                f"ΔF_y={force_residual:.2e} kN, ΔM_A={moment_residual:.2e} kNm."
            )
        else:
            st.warning(
                "Gleichgewicht nur naeherungsweise geschlossen: "
                f"ΔF_y={force_residual:.2e} kN, ΔM_A={moment_residual:.2e} kNm."
            )

        st.info(
            "• ein Auflager als Festlager in x\n"
            "• ein Auflager als Gleitlager in x\n"
            "• Reaktionen in y aus Gleichgewicht in Draufsicht\n"
            "• vereinfachte Abschätzung für Vorbemessung"
        )
        st.caption(e.reaktionsmodell_hinweis)

        st.markdown("### Lasten")
        _render_svg_asset(
            "balcony_system._lasten.svg",
            "Vereinfachte Reaktionsabschätzung mit Hx, Hy_1 und Hy_2.",
        )

        st.success("PDF erfolgreich erzeugt.")
        st.download_button(
            "⬇️ PDF herunterladen",
            data=st.session_state.generated_pdf_bytes,
            file_name=st.session_state.generated_pdf_name,
            mime="application/pdf",
            use_container_width=True,
            key="download_pdf_button"
        )


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — REFERENZTABELLEN
# ═══════════════════════════════════════════════════════════════════════════
with tab_ref:
    st.markdown("### Ausführlicher qp-Ansatz nach DIN EN 1991-1-4/NA:2010-12")
    df_formeln = pd.DataFrame([
        {"Gebiet":"Binnenland II/III", "h-Bereich":"h ≤ 7 m", "Formel":"qp(h)=1.5·qb,0", "Norm":"NA.B.1"},
        {"Gebiet":"Binnenland II/III", "h-Bereich":"7 < h ≤ 50 m", "Formel":"qp(h)=1.7·qb,0·(h/10)^0.37", "Norm":"NA.B.2"},
        {"Gebiet":"Binnenland II/III", "h-Bereich":"50 < h ≤ 300 m", "Formel":"qp(h)=2.1·qb,0·(h/10)^0.24", "Norm":"NA.B.3"},
        {"Gebiet":"Küstennah / Ostsee I/II", "h-Bereich":"h ≤ 4 m", "Formel":"qp(h)=1.8·qb,0", "Norm":"NA.B.4"},
        {"Gebiet":"Küstennah / Ostsee I/II", "h-Bereich":"4 < h ≤ 50 m", "Formel":"qp(h)=2.3·qb,0·(h/10)^0.27", "Norm":"NA.B.5"},
        {"Gebiet":"Küstennah / Ostsee I/II", "h-Bereich":"50 < h ≤ 300 m", "Formel":"qp(h)=2.6·qb,0·(h/10)^0.19", "Norm":"NA.B.6"},
        {"Gebiet":"Nordseeinseln I", "h-Bereich":"h ≤ 2 m", "Formel":"qp(h)=1.1 kN/m²", "Norm":"NA.B.7"},
        {"Gebiet":"Nordseeinseln I", "h-Bereich":"2 < h ≤ 300 m", "Formel":"qp(h)=1.05·(h/10)^0.19 kN/m²", "Norm":"NA.B.8"},
    ])
    st.dataframe(df_formeln, use_container_width=True, hide_index=True)

    st.markdown("**qb,0 nach Windzone**")
    df_qb = pd.DataFrame([
        {"Windzone":"1","qb,0 [kN/m²]":"0.32"},
        {"Windzone":"2","qb,0 [kN/m²]":"0.39"},
        {"Windzone":"3","qb,0 [kN/m²]":"0.47"},
        {"Windzone":"4","qb,0 [kN/m²]":"0.56"},
    ])
    st.dataframe(df_qb, use_container_width=True, hide_index=True)

    st.caption("Regelfälle nach NA.B.3.3 für Binnenland, küstennahe Gebiete / Ostseeinseln und Nordseeinseln.")

    st.markdown("---")
    st.markdown("### Windzonen nach Bundesland (Überblick)")
    wz_bl = [
        ("Bayern",                  1,    "Vollständig WZ 1"),
        ("Baden-Württemberg",       1,    "Vollständig WZ 1"),
        ("Thüringen",               1,    "Vollständig WZ 1"),
        ("Sachsen",                 1,    "Vollständig WZ 1"),
        ("Saarland",                1,    "Vollständig WZ 1"),
        ("Rheinland-Pfalz",         "1–2","Süden WZ 1, Norden WZ 2"),
        ("Hessen",                  2,    "Überwiegend WZ 2"),
        ("Nordrhein-Westfalen",     2,    "Überwiegend WZ 2"),
        ("Brandenburg / Berlin",    2,    "WZ 2"),
        ("Sachsen-Anhalt",          "1–2","Süden WZ 1, Norden WZ 2"),
        ("Niedersachsen",           "2–3","Inland WZ 2, Küste WZ 3"),
        ("Mecklenburg-Vorpommern",  "2–3","Inland WZ 2, Küste WZ 3"),
        ("Bremen / Hamburg",        3,    "WZ 3"),
        ("Schleswig-Holstein",      "3–4","WZ 3, Nordseeinseln WZ 4"),
    ]
    df_wz = pd.DataFrame(wz_bl, columns=["Bundesland","Windzone","Hinweis"])
    df_wz["Windzone"] = df_wz["Windzone"].astype(str)
    st.dataframe(df_wz, use_container_width=True, hide_index=True)
    st.caption("Vereinfacht · Maßgebend: NA.A.1 nach Gemeinde/Kreis")
