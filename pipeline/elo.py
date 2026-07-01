"""Apply Elo updates for every completed WC 2026 match, on top of the committed seed.

Reads:
  pipeline/data/elo_seed.json    (bootstrap ratings)
  pipeline/cache/wc_matches_raw.json (must be fresh; run build_live.py first)
  site/public/data/elo.json      (previous state, optional)

Writes:
  site/public/data/elo.json      (current Elo + list of match ids already applied)
"""
from __future__ import annotations

import datetime as dt
import json
from typing import Any

from common import CACHE_DIR, DATA_DIR, SEED_DIR, read_json, write_json

K_BASE = 50  # spec: "K ~= 50 for the World Cup"


def gd_multiplier(gd: int) -> float:
    gd = abs(gd)
    if gd <= 1:
        return 1.0
    if gd == 2:
        return 1.5
    return (11 + gd) / 8.0  # eloratings.net formula


def expected(r_a: float, r_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((r_b - r_a) / 400.0))


def apply_match(
    ratings: dict[int, float],
    home_id: int,
    away_id: int,
    home_goals: int,
    away_goals: int,
    duration: str,
) -> tuple[float, float]:
    """Return (home_delta, away_delta) and mutate ratings in place."""
    ra = ratings[home_id]
    rb = ratings[away_id]

    if duration == "PENALTY_SHOOTOUT":
        # Elo treats shootouts as a draw regardless of who advanced.
        s_home = 0.5
        gd = 0
    else:
        if home_goals > away_goals:
            s_home = 1.0
        elif home_goals < away_goals:
            s_home = 0.0
        else:
            s_home = 0.5
        gd = home_goals - away_goals

    k = K_BASE * gd_multiplier(gd)
    e_home = expected(ra, rb)
    delta_home = k * (s_home - e_home)
    delta_away = -delta_home

    ratings[home_id] = ra + delta_home
    ratings[away_id] = rb + delta_away
    return delta_home, delta_away


def main() -> None:
    seed = read_json(SEED_DIR / "elo_seed.json")
    if not seed:
        raise SystemExit("Missing pipeline/data/elo_seed.json — run build_elo_seed.py once")
    raw = read_json(CACHE_DIR / "wc_matches_raw.json")
    if not raw:
        raise SystemExit("Missing cache — run build_live.py first")

    prev = read_json(DATA_DIR / "elo.json", default={}) or {}
    applied_ids = set(prev.get("appliedMatches", []))
    prev_ratings = prev.get("ratings", {})

    # Start from previous ratings if we have them, else from seed.
    ratings: dict[int, float] = {}
    teams_meta: dict[int, dict[str, Any]] = {}
    for sid, t in seed["teams"].items():
        tid = int(sid)
        teams_meta[tid] = t
        if str(tid) in prev_ratings:
            ratings[tid] = float(prev_ratings[str(tid)])
        else:
            ratings[tid] = float(t["elo"])

    # Sort finished matches chronologically so updates compound in real order.
    finished = [
        m for m in raw["matches"]
        if m["status"] == "FINISHED" and m["id"] not in applied_ids
    ]
    finished.sort(key=lambda m: m["utcDate"])

    log = []
    for m in finished:
        home = m.get("homeTeam") or {}
        away = m.get("awayTeam") or {}
        hid, aid = home.get("id"), away.get("id")
        ft = (m.get("score") or {}).get("fullTime") or {}
        hg, ag = ft.get("home"), ft.get("away")
        if hid is None or aid is None or hg is None or ag is None:
            continue
        if hid not in ratings or aid not in ratings:
            # Team not in seed (shouldn't happen for WC teams).
            continue
        duration = (m.get("score") or {}).get("duration") or "REGULAR"
        before_h, before_a = ratings[hid], ratings[aid]
        dh, da = apply_match(ratings, hid, aid, hg, ag, duration)
        log.append({
            "matchId": m["id"],
            "utcDate": m["utcDate"],
            "stage": m["stage"],
            "home": {"id": hid, "tla": home.get("tla"), "before": round(before_h, 1), "delta": round(dh, 1)},
            "away": {"id": aid, "tla": away.get("tla"), "before": round(before_a, 1), "delta": round(da, 1)},
            "score": f"{hg}-{ag}",
            "duration": duration,
        })
        applied_ids.add(m["id"])

    payload = {
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "kBase": K_BASE,
        "teams": [
            {**teams_meta[tid], "elo": round(r, 1)}
            for tid, r in sorted(ratings.items(), key=lambda kv: -kv[1])
        ],
        "ratings": {str(tid): round(r, 1) for tid, r in ratings.items()},
        "appliedMatches": sorted(applied_ids),
        "recentUpdates": log[-20:],  # keep the last 20 for the UI
    }
    write_json(DATA_DIR / "elo.json", payload)
    print(f"elo.json updated: applied {len(log)} new match(es), total {len(applied_ids)} matches accounted for")


if __name__ == "__main__":
    main()
