from __future__ import annotations

import streamlit as st

from spittelmeister_windlast.ui.windlast_page import render_windlast_module_page

st.set_page_config(page_title="01 Windlast", layout="wide", initial_sidebar_state="expanded")
render_windlast_module_page()
