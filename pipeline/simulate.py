"""Monte-Carlo the remaining WC 2026 knockout bracket.

Reads bracket.json + elo.json. For each simulation run, replay every unfinished
knockout match by sampling from Elo-derived win probabilities and propagating
winners. Aggregate per-team probabilities of reaching each stage and of lifting
the trophy.

Writes site/public/data/odds.json.

Bracket-topology fallback: football-data.org only fills a match's team fields
when both parent games are finished. For unfilled slots we build the topology
by (a) honouring every observed parent link and (b) pairing the remaining
slots in id order. This is a heuristic for later rounds where no evidence
exists yet — flagged in odds.json so the UI can note it.
"""
from __future__ import annotations

import datetime as dt
import random
from collections import defaultdict
from typing import Any

from common import DATA_DIR, KNOCKOUT_STAGES, read_json, write_json

N_SIMS = 10_000
SEED = 26
PENALTY_FAVORITE_BIAS = 0.05

ADVANCEMENT_STAGES = ("LAST_16", "QUARTER_FINALS", "SEMI_FINALS", "FINAL", "CHAMPION")
STAGE_INDEX = {s: i for i, s in enumerate(ADVANCEMENT_STAGES)}


def expected(r_a: float, r_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((r_b - r_a) / 400.0))


def sample_winner(rng: random.Random, a: int, b: int, elo: dict[int, float]) -> int:
    p_a = expected(elo[a], elo[b])
    # Tiny tilt to the favorite when the tie is a coin flip (penalty-lottery flavour).
    if 0.45 < p_a < 0.55:
        if elo[a] >= elo[b]:
            p_a += PENALTY_FAVORITE_BIAS
        else:
            p_a -= PENALTY_FAVORITE_BIAS
    return a if rng.random() < p_a else b


def build_topology(
    bracket: dict[str, list[dict[str, Any]]]
) -> dict[str, list[tuple[int, int]]]:
    """Map every child match to its parent slot indices.

    Returns { stage: [(home_parent_slot, away_parent_slot), ...] } for each
    downstream stage. Observed parents win; remaining slots are paired in id order.
    """
    def pair_stage(child_stage: str, parent_stage: str) -> list[tuple[int, int]]:
        parents = bracket[parent_stage]
        children = bracket[child_stage]
        assigned_from_observed = set()
        pairings: list[tuple[int, int] | None] = [None] * len(children)
        for i, c in enumerate(children):
            hp = c.get("homeParent")
            ap = c.get("awayParent")
            if hp is not None and ap is not None:
                pairings[i] = (hp["slot"], ap["slot"])
                assigned_from_observed.add(hp["slot"])
                assigned_from_observed.add(ap["slot"])
        free = [i for i in range(len(parents)) if i not in assigned_from_observed]
        it = iter(free)
        for i, p in enumerate(pairings):
            if p is None:
                pairings[i] = (next(it), next(it))
        return pairings  # type: ignore[return-value]

    return {
        "LAST_16": pair_stage("LAST_16", "LAST_32"),
        "QUARTER_FINALS": pair_stage("QUARTER_FINALS", "LAST_16"),
        "SEMI_FINALS": pair_stage("SEMI_FINALS", "QUARTER_FINALS"),
        # Final and Third: single match each, pair from the two SF slots.
        "FINAL": [(0, 1)],
        "THIRD_PLACE": [(0, 1)],
    }


def simulate_once(
    rng: random.Random,
    bracket: dict[str, list[dict[str, Any]]],
    topology: dict[str, list[tuple[int, int]]],
    elo: dict[int, float],
) -> dict[int, int]:
    reached: dict[int, int] = {}

    def bump(tid: int, stage_key: str) -> None:
        idx = STAGE_INDEX[stage_key]
        if reached.get(tid, -1) < idx:
            reached[tid] = idx

    # winner_of_slot[stage][slot] = team_id
    winner_of_slot: dict[str, list[int | None]] = {
        s: [None] * len(bracket[s]) for s in KNOCKOUT_STAGES
    }

    # LAST_32.
    for slot, m in enumerate(bracket["LAST_32"]):
        if m["played"]:
            w = m["winnerId"]
        else:
            w = sample_winner(rng, m["home"]["id"], m["away"]["id"], elo)
        winner_of_slot["LAST_32"][slot] = w

    def play(child_stage: str, parent_stage: str) -> None:
        for slot, m in enumerate(bracket[child_stage]):
            hp_slot, ap_slot = topology[child_stage][slot]
            home = (
                m["home"]["id"] if m["home"] else winner_of_slot[parent_stage][hp_slot]
            )
            away = (
                m["away"]["id"] if m["away"] else winner_of_slot[parent_stage][ap_slot]
            )
            bump(home, child_stage if child_stage != "THIRD_PLACE" else "SEMI_FINALS")
            bump(away, child_stage if child_stage != "THIRD_PLACE" else "SEMI_FINALS")
            if m["played"]:
                w = m["winnerId"]
            else:
                w = sample_winner(rng, home, away, elo)
            winner_of_slot[child_stage][slot] = w

    play("LAST_16", "LAST_32")
    play("QUARTER_FINALS", "LAST_16")
    play("SEMI_FINALS", "QUARTER_FINALS")
    play("FINAL", "SEMI_FINALS")

    champ = winner_of_slot["FINAL"][0]
    bump(champ, "CHAMPION")
    return reached


def build_odds_table(
    reached_counts: dict[int, list[int]],
    n_sims: int,
    teams_meta: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for tid, counts in reached_counts.items():
        rows.append({
            **teams_meta[tid],
            "probR16": counts[STAGE_INDEX["LAST_16"]] / n_sims,
            "probQF": counts[STAGE_INDEX["QUARTER_FINALS"]] / n_sims,
            "probSF": counts[STAGE_INDEX["SEMI_FINALS"]] / n_sims,
            "probFinal": counts[STAGE_INDEX["FINAL"]] / n_sims,
            "probChampion": counts[STAGE_INDEX["CHAMPION"]] / n_sims,
        })
    rows.sort(key=lambda r: -r["probChampion"])
    return rows


def main() -> None:
    bracket_doc = read_json(DATA_DIR / "bracket.json")
    elo_doc = read_json(DATA_DIR / "elo.json")
    if not bracket_doc or not elo_doc:
        raise SystemExit("Missing bracket.json or elo.json — run build_live.py and elo.py first")

    bracket = {s["code"]: s["matches"] for s in bracket_doc["stages"]}
    elo = {int(k): float(v) for k, v in elo_doc["ratings"].items()}
    teams_meta = {t["id"]: t for t in elo_doc["teams"]}

    topology = build_topology(bracket)

    all_team_ids = set()
    for stage in KNOCKOUT_STAGES:
        for m in bracket[stage]:
            for side in ("home", "away"):
                t = m.get(side)
                if t and t.get("id"):
                    all_team_ids.add(t["id"])

    rng = random.Random(SEED)
    counts: dict[int, list[int]] = defaultdict(lambda: [0] * len(ADVANCEMENT_STAGES))
    for _ in range(N_SIMS):
        reached = simulate_once(rng, bracket, topology, elo)
        for tid, idx in reached.items():
            for j in range(idx + 1):
                counts[tid][j] += 1

    for tid in all_team_ids:
        counts.setdefault(tid, [0] * len(ADVANCEMENT_STAGES))

    table = build_odds_table(counts, N_SIMS, teams_meta)

    # Report how much of the bracket topology is observed vs inferred.
    observed = {"LAST_16": 0, "QUARTER_FINALS": 0, "SEMI_FINALS": 0, "FINAL": 0}
    for stage in observed:
        for m in bracket[stage]:
            if m.get("homeParent") and m.get("awayParent"):
                observed[stage] += 1

    payload = {
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "nSims": N_SIMS,
        "seed": SEED,
        "kBase": elo_doc.get("kBase"),
        "stages": list(ADVANCEMENT_STAGES),
        "topologyObserved": observed,  # e.g., {"LAST_16": 3, "QUARTER_FINALS": 0, ...}
        "teams": table,
    }
    write_json(DATA_DIR / "odds.json", payload)

    print(f"odds.json written ({N_SIMS} sims). Top 8:")
    for r in table[:8]:
        print(
            f"  {r['tla']:<4} {r['name']:<20}"
            f"  R16={r['probR16']*100:5.1f}%  QF={r['probQF']*100:5.1f}%"
            f"  SF={r['probSF']*100:5.1f}%  F={r['probFinal']*100:5.1f}%"
            f"  Cup={r['probChampion']*100:5.1f}%"
        )


if __name__ == "__main__":
    main()
