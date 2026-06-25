"""Monte Carlo del Mundial 2026: probabilidades de avance por ronda y de campeón.

Sin dependencias de Streamlit. Reusa el motor de standings y la estructura del
cuadro KO; simula los partidos de grupos no jugados muestreando un marcador de la
matriz Dixon-Coles, y las eliminatorias muestreando el ganador con la win-prob del
modelo (sin empate: p = P(home)/(P(home)+P(away))).
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.tournament.standings import (
    load_groups, _elo_lookup, compute_group_table, group_qualifiers,
)
from src.tournament.bracket import parse_knockout, assign_thirds

ROOT      = Path(__file__).resolve().parents[2]
FIXTURES  = ROOT / "data/processed/matches_2026_fixtures.csv"
MAPPING   = ROOT / "data/raw/reference/team_codes_mapping.csv"

# Rondas del camino principal (excluye "Match for third place").
_ROUND_KEY = {
    "Round of 32": "p_advance",
    "Round of 16": "p_r16",
    "Quarter-final": "p_qf",
    "Semi-final": "p_sf",
    "Final": "p_final",
}
_COLS = ["ISO", "p_advance", "p_r16", "p_qf", "p_sf", "p_final", "p_champion"]


def _ground_host(ground: str) -> str:
    g = str(ground).lower()
    if any(c in g for c in ["mexico city", "guadalajara", "monterrey"]):
        return "MEX"
    if any(c in g for c in ["toronto", "vancouver"]):
        return "CAN"
    return "USA"


def _name_to_iso() -> dict:
    ref = pd.read_csv(MAPPING)
    return dict(zip(ref["openfootball_name"], ref["iso_code"]))


def _unplayed_group_fixtures(results, team_to_group):
    """Lista de (ia, ib, host) de partidos de grupos aún no jugados."""
    name_to_iso = _name_to_iso()
    played = set()
    done = results.dropna(subset=["goals_a", "goals_b"])
    for r in done.itertuples(index=False):
        played.add(frozenset((r.iso_a, r.iso_b)))
    fix = pd.read_csv(FIXTURES)
    md = fix[fix["round"].astype(str).str.startswith("Matchday")]
    out = []
    for r in md.itertuples(index=False):
        ia, ib = name_to_iso.get(r.team1_name), name_to_iso.get(r.team2_name)
        if not ia or not ib:
            continue
        if team_to_group.get(ia) is None or team_to_group.get(ia) != team_to_group.get(ib):
            continue
        if frozenset((ia, ib)) in played:
            continue
        out.append((ia, ib, _ground_host(r.ground)))
    return out


def _played_group_results(results, team_to_group):
    done = results.dropna(subset=["goals_a", "goals_b"]).copy()
    done["goals_a"] = done["goals_a"].astype(int)
    done["goals_b"] = done["goals_b"].astype(int)
    mask = done.apply(
        lambda r: team_to_group.get(r["iso_a"]) is not None
        and team_to_group.get(r["iso_a"]) == team_to_group.get(r["iso_b"]), axis=1)
    return done[mask][["iso_a", "iso_b", "goals_a", "goals_b"]] if mask.any() \
        else done.iloc[0:0][["iso_a", "iso_b", "goals_a", "goals_b"]]


def _resolve_slot(slot, match_no, quals, thirds_map, winners, losers):
    s = str(slot)
    if re.fullmatch(r"[12][A-L]", s):
        return quals.get(s)
    if re.fullmatch(r"3[A-L/]+", s):
        return thirds_map.get(match_no)
    m = re.fullmatch(r"([WL])(\d+)", s)
    if m:
        kind, num = m.group(1), int(m.group(2))
        return winners.get(num) if kind == "W" else losers.get(num)
    return None


def simulate_tournament(results, predictor, n_sims=2000, seed=0):
    rng = np.random.default_rng(seed)
    team_to_group, group_to_teams = load_groups()
    elo = _elo_lookup()
    ko = parse_knockout()

    base_group = _played_group_results(results, team_to_group)
    unplayed = _unplayed_group_fixtures(results, team_to_group)

    # Precompute flattened score-prob vectors for each unplayed group fixture.
    fixture_draws = []
    for ia, ib, host in unplayed:
        mat = predictor.model_goals.predict_score_matrix(ia, ib, host)
        ncol = mat.shape[1]
        fixture_draws.append((ia, ib, mat.ravel(), ncol))

    win_cache = {}

    def win_prob(a, b, host):
        key = (a, b, host)
        if key not in win_cache:
            r = predictor.predict_match(a, b, host_iso=host)["result"]
            ph, pa = r["p_home"], r["p_away"]
            win_cache[key] = ph / (ph + pa) if (ph + pa) > 0 else 0.5
        return win_cache[key]

    ko_rows = list(ko.itertuples(index=False))
    counts = {}  # iso -> {col: int}

    def bump(iso, col):
        counts.setdefault(iso, {c: 0 for c in _COLS[1:]})[col] += 1

    for _ in range(n_sims):
        # 1) sample unplayed group matches
        sampled = []
        for ia, ib, flat, ncol in fixture_draws:
            idx = rng.choice(len(flat), p=flat)
            ga, gb = divmod(int(idx), ncol)
            sampled.append((ia, ib, ga, gb))
        sim_results = pd.concat(
            [base_group, pd.DataFrame(sampled, columns=["iso_a", "iso_b", "goals_a", "goals_b"])],
            ignore_index=True) if sampled else base_group

        # 2) group tables -> qualifiers + thirds
        tables = {grp: compute_group_table(group_to_teams[grp],
                                           sim_results[sim_results["iso_a"].map(team_to_group) == grp],
                                           elo)
                  for grp in group_to_teams}
        quals = group_qualifiers(tables)
        thirds_map = assign_thirds(ko, tables)   # top-8 third seeding (authority)

        # 3) simulate knockout
        winners, losers = {}, {}
        champion = None
        for r in ko_rows:
            ta = _resolve_slot(r.slot_a, r.match_no, quals, thirds_map, winners, losers)
            tb = _resolve_slot(r.slot_b, r.match_no, quals, thirds_map, winners, losers)
            if ta is None or tb is None:
                continue
            col = _ROUND_KEY.get(r.round)
            if col:
                bump(ta, col); bump(tb, col)
            host = _ground_host(r.ground)
            p = win_prob(ta, tb, host)
            if rng.random() < p:
                winners[r.match_no], losers[r.match_no] = ta, tb
            else:
                winners[r.match_no], losers[r.match_no] = tb, ta
            if r.round == "Final":
                champion = winners[r.match_no]
        if champion is not None:
            bump(champion, "p_champion")

    rows = [{"ISO": iso, **{c: counts[iso][c] / n_sims for c in _COLS[1:]}}
            for iso in counts]
    df = pd.DataFrame(rows, columns=_COLS)
    return df.sort_values("p_champion", ascending=False).reset_index(drop=True)
