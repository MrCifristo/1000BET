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

st.set_page_config(
    page_title="WC 2026 Predictor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("⚽ WC 2026 Predictor")
st.sidebar.caption("Modelo Poisson bivariado + Dixon-Coles")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navegación",
    ["🔮 Predecir partido", "🏆 Torneo", "📊 Fiabilidad del modelo",
     "⚙️ Estado del modelo"],
)

if page == "🔮 Predecir partido":
    from src.ui.pages.predict import show
    show()
elif page == "🏆 Torneo":
    from src.ui.pages.tournament import show
    show()
elif page == "📊 Fiabilidad del modelo":
    from src.ui.pages.dashboard import show
    show()
else:
    from src.ui.pages.model_status import show
    show()
