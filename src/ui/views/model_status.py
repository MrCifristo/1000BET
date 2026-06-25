"""Página de estado e información del modelo."""
import json
import pickle
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]


@st.cache_resource
def load_predictor():
    with open(ROOT / "outputs/match_predictor.pkl", "rb") as f:
        return pickle.load(f)


def show():
    st.title("⚙️ Estado del modelo")

    predictor = load_predictor()
    model     = predictor.model_goals

    # ── Hiperparámetros del modelo de goles ──────────────────────────────────
    st.subheader("Parámetros del modelo de goles")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ridge_λ",            model.ridge_lambda)
    c2.metric("decay_rate",         model.decay_rate)
    c3.metric("ρ (Dixon-Coles)",    f"{model.params_['rho']:.4f}")
    c4.metric("Selecciones",        len(model.teams_))

    # ── Best params por mercado ──────────────────────────────────────────────
    bp_path = ROOT / "outputs/best_params.json"
    if bp_path.exists():
        with open(bp_path) as f:
            best_params = json.load(f)
        st.subheader("Mejores hiperparámetros por mercado")
        bp_df = pd.DataFrame([{"mercado": k, **v} for k, v in best_params.items()])
        st.dataframe(bp_df, use_container_width=True)

    st.divider()

    # ── Dataset ──────────────────────────────────────────────────────────────
    st.subheader("Dataset de entrenamiento")
    matches     = pd.read_csv(ROOT / "data/processed/matches_intl_v3.csv")
    results_log = ROOT / "data/processed/results_log.csv"
    n_log       = len(pd.read_csv(results_log)) if results_log.exists() else 0
    ca, cb = st.columns(2)
    ca.metric("Partidos internacionales (2002+)", len(matches))
    cb.metric("Resultados reales ingresados",      n_log)

    st.divider()

    # ── Top 10 por parámetros ─────────────────────────────────────────────────
    col_att, col_def = st.columns(2)

    with col_att:
        st.subheader("Top 10 — Ataque (α)")
        alpha_df = pd.DataFrame(
            sorted(model.params_["alpha"].items(), key=lambda x: x[1], reverse=True)[:10],
            columns=["ISO", "α"],
        )
        alpha_df["α"] = alpha_df["α"].round(3)
        st.dataframe(alpha_df, use_container_width=True)

    with col_def:
        st.subheader("Top 10 — Defensa (β, mayor = peor)")
        beta_df = pd.DataFrame(
            sorted(model.params_["beta"].items(), key=lambda x: x[1], reverse=True)[:10],
            columns=["ISO", "β"],
        )
        beta_df["β"] = beta_df["β"].round(3)
        st.dataframe(beta_df, use_container_width=True)

    st.divider()

    # ── Re-entrenamiento manual ───────────────────────────────────────────────
    st.subheader("Re-entrenamiento manual")
    st.caption("Re-entrena el modelo de goles con el Elo actual + todos los resultados registrados.")
    if st.button("🔄 Re-entrenar ahora", type="secondary"):
        from src.model.updater import retrain_goals_model
        elo_df = pd.read_csv(ROOT / "data/features/elo_ratings_rolling.csv")
        with st.spinner("Re-entrenando... (~15-30s)"):
            retrain_goals_model(elo_df)
        st.success("✅ Modelo actualizado.")
        st.cache_resource.clear()
        st.rerun()
