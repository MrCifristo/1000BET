"""Página de fiabilidad acumulada del modelo."""
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT    = Path(__file__).resolve().parents[3]
LOG_CSV = ROOT / "data/processed/results_log.csv"


def show():
    st.title("📊 Fiabilidad del modelo")

    if not LOG_CSV.exists():
        st.info("Aún no hay resultados registrados. Predice un partido e ingresa el resultado real.")
        return

    df = pd.read_csv(LOG_CSV)
    if len(df) == 0:
        st.info("El log de resultados está vacío.")
        return

    df["match_date"] = pd.to_datetime(df["match_date"])

    # ── Filtros ──────────────────────────────────────────────────────────────
    sources    = ["Todos"] + sorted(df["source"].unique().tolist())
    src_filter = st.selectbox("Fuente", sources)
    if src_filter != "Todos":
        df = df[df["source"] == src_filter]

    if len(df) == 0:
        st.warning("Sin resultados para este filtro.")
        return

    # ── Métricas clave ───────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Partidos registrados", len(df))
    m2.metric("BS acumulado",         f"{df['brier_score'].mean():.4f}")
    m3.metric("Referencia naive",      "0.6667")
    mejora = (0.6667 - df["brier_score"].mean()) / 0.6667 * 100
    m4.metric("Mejora vs naive",       f"{mejora:.1f}%", delta=f"{mejora:.1f}%")

    st.divider()

    # ── Gráfica BS partido a partido ─────────────────────────────────────────
    st.subheader("Evolución Brier Score")
    df_sorted = df.sort_values("match_date").reset_index(drop=True)
    df_sorted["bs_rolling5"]   = df_sorted["brier_score"].rolling(5, min_periods=1).mean()
    df_sorted["bs_acumulado"]  = df_sorted["brier_score"].expanding().mean()
    df_sorted["resultado"]     = df_sorted["goals_a"].astype(str) + "-" + df_sorted["goals_b"].astype(str)
    df_sorted["match_label"]   = df_sorted["iso_a"] + " vs " + df_sorted["iso_b"]

    chart_data = df_sorted[["match_label","brier_score","bs_rolling5","bs_acumulado"]].set_index("match_label")
    st.line_chart(chart_data, use_container_width=True)

    st.divider()

    # ── Tabla de partidos ────────────────────────────────────────────────────
    st.subheader("Detalle de partidos")
    display_df = df_sorted[[
        "match_date","iso_a","iso_b","resultado",
        "p_home_pred","p_draw_pred","p_away_pred",
        "brier_score","source"
    ]].copy()
    display_df["match_date"] = display_df["match_date"].dt.strftime("%Y-%m-%d")
    st.dataframe(display_df, use_container_width=True)

    st.divider()

    # ── Top/Bottom 5 ────────────────────────────────────────────────────────
    col_t, col_b = st.columns(2)
    show_cols = ["match_date","iso_a","iso_b","resultado","brier_score"]
    with col_t:
        st.subheader("✅ Mejores predicciones")
        best = df_sorted.nsmallest(5, "brier_score")[show_cols].copy()
        best["match_date"] = best["match_date"].dt.strftime("%Y-%m-%d")
        st.dataframe(best, use_container_width=True)
    with col_b:
        st.subheader("❌ Peores predicciones")
        worst = df_sorted.nlargest(5, "brier_score")[show_cols].copy()
        worst["match_date"] = worst["match_date"].dt.strftime("%Y-%m-%d")
        st.dataframe(worst, use_container_width=True)
