"""One-shot script: seed pipeline/data/elo_seed.json from eloratings.net's World.tsv
for the 48 WC 2026 teams. Rerun manually if you want to re-anchor the seed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

from common import CACHE_DIR, SEED_DIR

# football-data.org TLA -> eloratings.net 2-letter code.
# Standard ISO 3166-1 alpha-2 except:
#   ENG -> EN (custom UK sub-nation)
#   SCO -> SQ (custom UK sub-nation, verified via /Scotland.tsv)
#   COD -> CD (DR Congo, ISO alpha-2)
# The remaining 45 are standard ISO alpha-2.
TLA_TO_ELO_CODE = {
    "ALG": "DZ", "ARG": "AR", "AUS": "AU", "AUT": "AT", "BEL": "BE",
    "BIH": "BA", "BRA": "BR", "CAN": "CA", "CPV": "CV", "COL": "CO",
    "COD": "CD", "CRO": "HR", "CUW": "CW", "CZE": "CZ", "ECU": "EC",
    "EGY": "EG", "ENG": "EN", "FRA": "FR", "GER": "DE", "GHA": "GH",
    "HAI": "HT", "IRN": "IR", "IRQ": "IQ", "CIV": "CI", "JPN": "JP",
    "JOR": "JO", "MEX": "MX", "MAR": "MA", "NED": "NL", "NZL": "NZ",
    "NOR": "NO", "PAN": "PA", "PAR": "PY", "POR": "PT", "QAT": "QA",
    "KSA": "SA", "SCO": "SQ", "SEN": "SN", "RSA": "ZA", "KOR": "KR",
    "ESP": "ES", "SWE": "SE", "SUI": "CH", "TUN": "TN", "TUR": "TR",
    "USA": "US", "URU": "UY", "UZB": "UZ",
}


def main() -> None:
    raw_matches_path = CACHE_DIR / "wc_matches_raw.json"
    if not raw_matches_path.exists():
        sys.exit("Run build_live.py first to populate pipeline/cache/wc_matches_raw.json")
    raw = json.loads(raw_matches_path.read_text(encoding="utf-8"))

    # Collect the 48 unique WC teams from matches.
    teams: dict[int, dict] = {}
    for m in raw["matches"]:
        for side in ("homeTeam", "awayTeam"):
            t = m.get(side)
            if t and t.get("id"):
                teams[t["id"]] = {
                    "id": t["id"],
                    "name": t["name"],
                    "shortName": t.get("shortName"),
                    "tla": t.get("tla"),
                    "crest": t.get("crest"),
                }

    # Fetch current Elo snapshot from eloratings.net.
    resp = requests.get(
        "https://www.eloratings.net/World.tsv",
        timeout=30,
        headers={"User-Agent": "wc26-dash/0.1"},
    )
    resp.raise_for_status()
    resp.encoding = "utf-8"
    elo_by_code: dict[str, int] = {}
    for line in resp.text.splitlines():
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        code = parts[2]
        try:
            elo_by_code[code] = int(parts[3])
        except ValueError:
            continue

    # Build seed for our 48 teams.
    seed = {}
    missing = []
    for tid, team in sorted(teams.items()):
        tla = team["tla"]
        iso = TLA_TO_ELO_CODE.get(tla)
        if not iso or iso not in elo_by_code:
            missing.append(f"{tla} ({team['name']})")
            continue
        seed[str(tid)] = {
            **team,
            "eloCode": iso,
            "elo": elo_by_code[iso],
        }

    if missing:
        print("WARNING: unmapped teams:", missing)

    out = SEED_DIR / "elo_seed.json"
    out.write_text(
        json.dumps(
            {
                "source": "https://www.eloratings.net/World.tsv",
                "generatedAt": raw.get("resultSet", {}).get("last"),
                "teams": seed,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {out} with {len(seed)} teams.")


if __name__ == "__main__":
    main()
