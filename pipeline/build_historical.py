"""Render Brazil-2022 shot maps and per-match xG summary. RUN ONCE — do not
schedule on cron; StatsBomb open data doesn't change.

Outputs:
  site/public/img/br_2022_<match_id>.png  (one shot map per match)
  site/public/data/historical.json         (per-match xG summary + image paths)
"""
from __future__ import annotations

import datetime as dt
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mplsoccer import Pitch
from statsbombpy import sb

from common import DATA_DIR, IMG_DIR, write_json

WC_COMPETITION_ID = 43
WC_2022_SEASON_ID = 106
BRAZIL = "Brazil"

# Theme (matches the frontend dark palette).
BG = "#0a0a0a"
LINE = "#5a5a5a"
GOAL = "#00d68f"       # brand green (Brazil pinned color)
MISS = "#ff5c5c"       # red for no-goal
TEXT = "#e5e5e5"


def render_match(match: dict[str, Any]) -> dict[str, Any]:
    match_id = int(match["match_id"])
    events = sb.events(match_id=match_id)
    # Exclude period 5 (penalty shootout) — those are not open-play shots.
    shots = events[
        (events["type"] == "Shot")
        & (events["team"] == BRAZIL)
        & (events["period"] != 5)
    ].copy()
    # Coerce location columns.
    shots["x"] = shots["location"].apply(lambda p: p[0] if isinstance(p, list) else None)
    shots["y"] = shots["location"].apply(lambda p: p[1] if isinstance(p, list) else None)
    shots = shots.dropna(subset=["x", "y", "shot_statsbomb_xg"])
    shots["is_goal"] = shots["shot_outcome"] == "Goal"

    fig, ax = plt.subplots(figsize=(9, 6), facecolor=BG)
    pitch = Pitch(
        pitch_type="statsbomb",
        pitch_color=BG,
        line_color=LINE,
        linewidth=1,
        goal_type="line",
    )
    pitch.draw(ax=ax)

    if not shots.empty:
        sizes = shots["shot_statsbomb_xg"] * 900 + 40
        colors = shots["is_goal"].map({True: GOAL, False: MISS})
        edge = shots["is_goal"].map({True: "#ffcb0e", False: "#222"})
        pitch.scatter(
            shots["x"], shots["y"],
            s=sizes,
            c=colors,
            edgecolors=edge,
            linewidths=1.2,
            alpha=0.85,
            ax=ax,
            zorder=3,
        )

    opp = match["away_team"] if match["home_team"] == BRAZIL else match["home_team"]
    br_score = match["home_score"] if match["home_team"] == BRAZIL else match["away_score"]
    opp_score = match["away_score"] if match["home_team"] == BRAZIL else match["home_score"]
    total_xg = float(shots["shot_statsbomb_xg"].sum()) if not shots.empty else 0.0
    goals = int(shots["is_goal"].sum()) if not shots.empty else 0

    ax.set_title(
        f"Brazil {br_score} – {opp_score} {opp}  ·  {match['competition_stage']}  ·  {match['match_date']}",
        color=TEXT, fontsize=12, pad=12,
        fontname="monospace",
    )
    ax.text(
        60, 82,
        f"shots {len(shots)}   xG {total_xg:.2f}   goals {goals}",
        color=TEXT, fontsize=10, ha="center", fontname="monospace",
    )

    img_path = IMG_DIR / f"br_2022_{match_id}.png"
    fig.savefig(img_path, dpi=140, bbox_inches="tight", facecolor=BG)
    plt.close(fig)

    return {
        "matchId": match_id,
        "date": match["match_date"],
        "stage": match["competition_stage"],
        "opponent": opp,
        "score": {"brazil": br_score, "opponent": opp_score},
        "shots": len(shots),
        "xg": round(total_xg, 3),
        "goals": goals,
        "image": f"img/br_2022_{match_id}.png",
    }


def main() -> None:
    matches = sb.matches(competition_id=WC_COMPETITION_ID, season_id=WC_2022_SEASON_ID)
    brz = matches[
        (matches["home_team"] == BRAZIL) | (matches["away_team"] == BRAZIL)
    ].sort_values("match_date")
    print(f"Rendering shot maps for {len(brz)} Brazil matches...")

    summaries: list[dict[str, Any]] = []
    for _, m in brz.iterrows():
        summary = render_match(m.to_dict())
        summaries.append(summary)
        print(
            f"  {summary['date']}  {summary['stage']:<15}  "
            f"vs {summary['opponent']:<12}  {summary['score']['brazil']}-{summary['score']['opponent']}  "
            f"shots={summary['shots']}  xG={summary['xg']}  goals={summary['goals']}"
        )

    write_json(DATA_DIR / "historical.json", {
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "source": "StatsBomb open data (WC 2022, Brazil)",
        "matches": summaries,
    })
    print(f"historical.json written with {len(summaries)} matches.")


if __name__ == "__main__":
    main()
