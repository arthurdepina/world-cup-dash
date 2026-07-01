"""Fetch WC 2026 matches from football-data.org and derive the knockout bracket.

Output: site/public/data/bracket.json
"""
from __future__ import annotations

import datetime as dt
from typing import Any

import requests

from common import (
    CACHE_DIR,
    DATA_DIR,
    KNOCKOUT_STAGES,
    PINNED_DEFAULT_ID,
    STAGE_LABEL,
    require_token,
    write_json,
)

API_BASE = "https://api.football-data.org/v4"


def fetch_matches(token: str) -> dict[str, Any]:
    resp = requests.get(
        f"{API_BASE}/competitions/WC/matches",
        headers={"X-Auth-Token": token},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def team_from(t: dict[str, Any] | None) -> dict[str, Any] | None:
    if not t or not t.get("id"):
        return None
    return {
        "id": t["id"],
        "name": t.get("name"),
        "shortName": t.get("shortName"),
        "tla": t.get("tla"),
        "crest": t.get("crest"),
    }


def match_summary(m: dict[str, Any]) -> dict[str, Any]:
    score = m.get("score") or {}
    ft = score.get("fullTime") or {}
    winner_code = score.get("winner")
    home = team_from(m.get("homeTeam"))
    away = team_from(m.get("awayTeam"))
    winner_id: int | None = None
    if winner_code == "HOME_TEAM" and home:
        winner_id = home["id"]
    elif winner_code == "AWAY_TEAM" and away:
        winner_id = away["id"]
    return {
        "id": m["id"],
        "stage": m["stage"],
        "status": m["status"],
        "played": m["status"] == "FINISHED",
        "utcDate": m.get("utcDate"),
        "home": home,
        "away": away,
        "score": {
            "home": ft.get("home"),
            "away": ft.get("away"),
            "duration": score.get("duration"),
            "winner": winner_code,
        },
        "winnerId": winner_id,
    }


def build_bracket(matches: list[dict[str, Any]]) -> dict[str, Any]:
    """Group knockout matches by stage and infer parent connections."""
    ko = [match_summary(m) for m in matches if m["stage"] in KNOCKOUT_STAGES]
    ko.sort(key=lambda m: (KNOCKOUT_STAGES.index(m["stage"]), m["id"]))

    by_stage: dict[str, list[dict[str, Any]]] = {s: [] for s in KNOCKOUT_STAGES}
    for m in ko:
        by_stage[m["stage"]].append(m)

    # Observed parent connections: for each match with a filled team, find the
    # match in the previous stage where that team appeared. Position-in-stage
    # is stable (sorted by id above), so we store parent slot indices too.
    prev_of = {
        "LAST_16": "LAST_32",
        "QUARTER_FINALS": "LAST_16",
        "SEMI_FINALS": "QUARTER_FINALS",
        "FINAL": "SEMI_FINALS",
        "THIRD_PLACE": "SEMI_FINALS",  # third-place = SF losers
    }

    def find_parent(prev_stage: str, team_id: int) -> dict[str, Any] | None:
        for i, p in enumerate(by_stage[prev_stage]):
            if (p["home"] and p["home"]["id"] == team_id) or (
                p["away"] and p["away"]["id"] == team_id
            ):
                return {"id": p["id"], "slot": i}
        return None

    for stage, items in by_stage.items():
        prev = prev_of.get(stage)
        for slot, m in enumerate(items):
            m["slot"] = slot
            m["homeParent"] = None
            m["awayParent"] = None
            if not prev:
                continue
            if m["home"]:
                m["homeParent"] = find_parent(prev, m["home"]["id"])
            if m["away"]:
                m["awayParent"] = find_parent(prev, m["away"]["id"])

    return by_stage


def trace_pinned_path(bracket: dict[str, list[dict[str, Any]]], pinned_id: int) -> list[dict[str, Any]]:
    """Walk the pinned team's actual/scheduled matches in order."""
    path: list[dict[str, Any]] = []
    for stage in KNOCKOUT_STAGES:
        if stage == "THIRD_PLACE":
            continue
        for m in bracket[stage]:
            hits_home = m["home"] and m["home"]["id"] == pinned_id
            hits_away = m["away"] and m["away"]["id"] == pinned_id
            if hits_home or hits_away:
                path.append(
                    {
                        "stage": stage,
                        "matchId": m["id"],
                        "utcDate": m["utcDate"],
                        "opponent": m["away"] if hits_home else m["home"],
                        "played": m["played"],
                        "won": m["played"] and m["winnerId"] == pinned_id,
                        "score": m["score"],
                    }
                )
                # If they lost, stop tracing.
                if m["played"] and m["winnerId"] != pinned_id:
                    return path
                break
    return path


def main() -> None:
    token = require_token()
    raw = fetch_matches(token)
    (CACHE_DIR / "wc_matches_raw.json").write_text(
        __import__("json").dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    bracket = build_bracket(raw["matches"])
    generated = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

    payload = {
        "generatedAt": generated,
        "source": "football-data.org /v4/competitions/WC/matches",
        "competition": raw.get("competition"),
        "resultSet": raw.get("resultSet"),
        "stages": [
            {
                "code": stage,
                "label": STAGE_LABEL[stage],
                "matches": bracket[stage],
            }
            for stage in KNOCKOUT_STAGES
        ],
        "pinnedDefault": PINNED_DEFAULT_ID,
        "pinnedPath": trace_pinned_path(bracket, PINNED_DEFAULT_ID),
    }

    out = DATA_DIR / "bracket.json"
    write_json(out, payload)
    played = sum(1 for s in KNOCKOUT_STAGES for m in bracket[s] if m["played"])
    total = sum(len(bracket[s]) for s in KNOCKOUT_STAGES)
    print(f"bracket.json written to {out} — {played}/{total} knockout matches played")


if __name__ == "__main__":
    main()
