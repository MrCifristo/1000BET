"""
WC 2026 Predictor — UI Streamlit.
Lanzar con: streamlit run src/ui/app.py
"""
import sys
from pathlib import Path

# Ensure project root is on sys.path so `src.*` imports resolve
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import streamlit as st

from src.ui.views import predict, tournament, dashboard, model_status

st.set_page_config(
    page_title="WC 2026 Predictor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = [
    st.Page(predict.show,      title="Predecir partido",      icon="🔮",
            url_path="predict", default=True),
    st.Page(tournament.show,   title="Torneo",                icon="🏆",
            url_path="tournament"),
    st.Page(dashboard.show,    title="Fiabilidad del modelo", icon="📊",
            url_path="reliability"),
    st.Page(model_status.show, title="Estado del modelo",     icon="⚙️",
            url_path="status"),
]

st.sidebar.title("⚽ WC 2026 Predictor")
st.sidebar.caption("Modelo Poisson bivariado + Dixon-Coles")
st.sidebar.divider()

st.navigation(pages).run()
