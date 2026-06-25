"""Página de predicción de partidos y registro de resultados reales."""
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.ui.components import render_score_forecast

ROOT = Path(__file__).resolve().parents[3]


@st.cache_data
def load_team_names() -> dict[str, str]:
    """Retorna dict openfootball_name → iso_code para los 48 equipos WC 2026."""
    ref = pd.read_csv(ROOT / "data/raw/reference/team_codes_mapping.csv")
    return dict(zip(ref["openfootball_name"], ref["iso_code"]))


@st.cache_data
def load_fixtures() -> pd.DataFrame:
    """Carga fixtures del WC 2026 filtrando solo partidos con equipos reales."""
    fix = pd.read_csv(ROOT / "data/processed/matches_2026_fixtures.csv")
    name_to_iso = load_team_names()
    return fix[fix["team1_name"].isin(name_to_iso) & fix["team2_name"].isin(name_to_iso)].copy()


def ground_to_host(ground: str) -> str:
    """Detecta el país anfitrión según la sede."""
    g = ground.lower()
    if any(c in g for c in ["mexico city", "guadalajara", "monterrey"]):
        return "MEX"
    if any(c in g for c in ["toronto", "vancouver"]):
        return "CAN"
    return "USA"


@st.cache_resource
def load_predictor():
    with open(ROOT / "outputs/match_predictor.pkl", "rb") as f:
        return pickle.load(f)


def render_score_heatmap(predictor, ia: str, ib: str, host_iso, max_g: int = 6):
    """Heatmap de P(marcador) recortado a [0, max_g] goles por equipo."""
    matrix = predictor.model_goals.predict_score_matrix(ia, ib, host_iso)
    m = matrix[: max_g + 1, : max_g + 1]
    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    im = ax.imshow(m, cmap="YlOrRd", origin="upper")
    ax.set_xticks(range(max_g + 1)); ax.set_yticks(range(max_g + 1))
    ax.set_xlabel(f"Goles {ib}"); ax.set_ylabel(f"Goles {ia}")
    bi, bj = np.unravel_index(m.argmax(), m.shape)
    for i in range(max_g + 1):
        for j in range(max_g + 1):
            ax.text(j, i, f"{m[i, j]*100:.0f}", ha="center", va="center",
                    fontsize=7, color="black")
    ax.add_patch(plt.Rectangle((bj - 0.5, bi - 0.5), 1, 1, fill=False,
                               edgecolor="#1f77b4", lw=2.5))
    ax.set_title("Probabilidad por marcador (%)", fontsize=10)
    fig.tight_layout()
    return fig


def show():
    st.title("🔮 Predecir partido")

    name_to_iso = load_team_names()
    teams       = sorted(name_to_iso.keys())

    mode = st.radio(
        "Tipo de partido",
        ["Mundial 2026 — fixture oficial", "Partido libre / Amistoso"],
        horizontal=True,
    )

    iso_a = iso_b = host_iso = match_date = None
    source = "wc2026" if mode.startswith("Mundial") else "friendly"

    if mode == "Mundial 2026 — fixture oficial":
        fixtures = load_fixtures()
        options  = [
            f"{r['match_date']} | {r['team1_name']} vs {r['team2_name']}  ({r['round']})"
            for _, r in fixtures.iterrows()
        ]
        sel = st.selectbox("Seleccionar partido", options)
        idx = options.index(sel)
        row = fixtures.iloc[idx]
        iso_a      = name_to_iso[row["team1_name"]]
        iso_b      = name_to_iso[row["team2_name"]]
        host_iso   = ground_to_host(row["ground"])
        match_date = row["match_date"]
        st.caption(f"📍 Sede: {row['ground']} | Anfitrión detectado: **{host_iso}**")

    else:
        c1, c2 = st.columns(2)
        a_name  = c1.selectbox("Equipo A", teams, index=teams.index("Argentina") if "Argentina" in teams else 0)
        b_name  = c2.selectbox("Equipo B", teams, index=teams.index("France") if "France" in teams else 1)
        iso_a   = name_to_iso[a_name]
        iso_b   = name_to_iso[b_name]
        h_sel   = st.selectbox("Anfitrión", ["Ninguno", "USA", "MEX", "CAN"])
        host_iso  = None if h_sel == "Ninguno" else h_sel
        match_date = str(st.date_input("Fecha del partido"))

    st.divider()

    if st.button("⚡ Predecir", type="primary", use_container_width=True):
        with st.spinner("Calculando predicciones..."):
            predictor = load_predictor()
            result    = predictor.predict_match(iso_a, iso_b, host_iso=host_iso)
        st.session_state["last_prediction"] = {
            "result":     result,
            "iso_a":      iso_a,
            "iso_b":      iso_b,
            "host_iso":   host_iso,
            "match_date": match_date,
            "source":     source,
        }

    if "last_prediction" not in st.session_state:
        return

    pred = st.session_state["last_prediction"]
    r    = pred["result"]
    ia   = pred["iso_a"]
    ib   = pred["iso_b"]

    # ── Resultado 1X2 ──────────────────────────────────────────────────────
    st.subheader(f"📊 {ia} vs {ib}")
    c1, c2, c3 = st.columns(3)
    c1.metric(f"🏆 {ia} gana", f"{r['result']['p_home']:.1%}")
    c2.metric("🤝 Empate",     f"{r['result']['p_draw']:.1%}")
    c3.metric(f"🏆 {ib} gana", f"{r['result']['p_away']:.1%}")
    render_score_forecast(r["result"])

    with st.expander("🔥 Mapa de calor de marcadores", expanded=False):
        predictor = load_predictor()
        st.pyplot(render_score_heatmap(predictor, ia, ib, pred["host_iso"]))

    # ── Mercados Over/Under ─────────────────────────────────────────────────
    st.subheader("📈 Mercados Over / Under")
    markets = {
        "⚽ Goles":    r["goals"],
        "🚩 Corners":  r["corners"],
        "🟨 Tarjetas": r["cards"],
        "👟 Disparos": r["shots"],
        "⚠️ Faltas":  r["fouls"],
    }
    cols = st.columns(len(markets))
    for col, (name, mkt) in zip(cols, markets.items()):
        col.markdown(f"**{name}**")
        col.metric("Expected total", mkt["expected_total"])
        lines = sorted(k for k in mkt if k.startswith("over_"))
        for key in lines:
            line      = key.replace("over_", "").replace("_", ".")
            under_key = key.replace("over_", "under_")
            over_val  = mkt[key]
            under_val = mkt.get(under_key, 1 - over_val)
            col.write(f"O{line}: **{over_val:.0%}** | U{line}: **{under_val:.0%}**")

    # ── Ingresar resultado real ─────────────────────────────────────────────
    st.divider()
    with st.expander("📝 Ingresar resultado real (actualiza el modelo)"):
        cg1, cg2 = st.columns(2)
        goals_a = cg1.number_input(f"Goles {ia}", min_value=0, max_value=20, value=0, key="ga")
        goals_b = cg2.number_input(f"Goles {ib}", min_value=0, max_value=20, value=0, key="gb")

        # Mercados de props opcionales: cada checkbox despliega 2 campos (A / B)
        st.caption("Opcional: registra estadísticas reales para reentrenar esos mercados.")
        PROP_UI = [
            ("corners", "🚩 Corners",  50),
            ("shots",   "👟 Disparos", 60),
            ("cards",   "🟨 Tarjetas", 15),
            ("fouls",   "⚠️ Faltas",   60),
        ]
        props_real: dict = {}
        for market, label, vmax in PROP_UI:
            if st.checkbox(f"Registrar {label}", key=f"chk_{market}"):
                pc1, pc2 = st.columns(2)
                va = pc1.number_input(f"{label} {ia}", min_value=0, max_value=vmax,
                                      value=0, key=f"{market}_a")
                vb = pc2.number_input(f"{label} {ib}", min_value=0, max_value=vmax,
                                      value=0, key=f"{market}_b")
                props_real[market] = (int(va), int(vb))

        if st.button("💾 Guardar resultado y actualizar modelo", type="secondary"):
            from src.model.updater import (
                log_result, update_elo, retrain_goals_model,
                retrain_props_models, k_for_source,
            )

            elo_path = ROOT / "data/features/elo_ratings_rolling.csv"
            elo_df   = pd.read_csv(elo_path)

            # Elo pre-partido (point-in-time) para registrar y re-entrenar sin leakage
            elo_lookup = elo_df.set_index("iso_code")["elo_rating"].astype(float)
            elo_a_pre  = float(elo_lookup.get(ia, elo_lookup.median()))
            elo_b_pre  = float(elo_lookup.get(ib, elo_lookup.median()))

            bs = log_result(
                match_date=pred["match_date"],
                iso_a=ia, iso_b=ib, host_iso=pred["host_iso"],
                goals_a=goals_a, goals_b=goals_b,
                p_home=r["result"]["p_home"],
                p_draw=r["result"]["p_draw"],
                p_away=r["result"]["p_away"],
                source=pred["source"],
                elo_a_pre=elo_a_pre, elo_b_pre=elo_b_pre,
                props_real=props_real,
            )

            elo_updated = update_elo(
                elo_df, ia, ib, goals_a, goals_b,
                k=k_for_source(pred["source"]), host_iso=pred["host_iso"],
            )
            elo_updated.to_csv(elo_path, index=False)

            with st.spinner("Re-entrenando modelo... (~15-30s)"):
                retrain_goals_model(elo_updated)
                if props_real:
                    retrain_props_models(markets=list(props_real.keys()))

            extra = f" + props: {', '.join(props_real)}" if props_real else ""
            st.success(f"✅ Resultado guardado{extra}. Brier Score 1X2: **{bs:.3f}**")
            st.cache_resource.clear()
            del st.session_state["last_prediction"]
            st.rerun()
