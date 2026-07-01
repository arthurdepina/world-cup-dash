# world-cup-dash

A living, minimalist dashboard for the FIFA World Cup 2026. Rebuilds itself
every ~6 hours via GitHub Actions and deploys as a static site to GitHub Pages.
No server, no database, $0.

Three modules:

1. **Bracket** — live knockout tree from football-data.org. The pinned team's
   road to the final is highlighted; played ties show scores, upcoming ties
   show the kickoff date.
2. **Monte Carlo** — 10,000 sims of the remaining bracket using national-team
   Elo. Shows each team's probability of reaching R16/QF/SF/Final and of
   lifting the cup.
3. **Brazil · 2022** — shot maps for every Brazil match at the 2022 World Cup
   (StatsBomb open data + mplsoccer), plus xG-vs-actual-goals per match.

Aesthetic: The Monospace Web with a black background and a small palette that
recolors around whichever country is pinned.

## Data flow

```
                 ┌─────────────────────┐
   football-data → build_live.py  ────→ bracket.json
   .org (WC API)                        │
                                        ▼
   eloratings.net ─→ build_elo_seed.py → elo_seed.json (committed)
      (one-shot)                        │
                                        ▼
                    elo.py       ────→ elo.json  (Elo evolves match-by-match)
                                        │
                                        ▼
                    simulate.py  ────→ odds.json (10k MC sims)

   StatsBomb ─────→ build_historical.py→ historical.json + shot map PNGs
   open data       (run once; static)
```

Every JSON above lands in `site/public/data/`; shot map PNGs go to
`site/public/img/`. Vite serves them as static assets.

## Local setup

Requirements: Python 3.11+, Node 18+, and a football-data.org token
(free tier at [football-data.org](https://www.football-data.org/client/register)).

### 1. Token

Set the token as a **User** environment variable in Windows (PowerShell):

```powershell
[System.Environment]::SetEnvironmentVariable("FOOTBALL_DATA_TOKEN","<your_token>","User")
```

On macOS/Linux, add to your shell rc file:

```bash
export FOOTBALL_DATA_TOKEN=<your_token>
```

Open a new terminal so the variable is picked up.

### 2. Pipeline

```bash
pip install -r pipeline/requirements.txt

# One-time bootstrap (only if pipeline/data/elo_seed.json is missing):
python pipeline/build_elo_seed.py

# The three that run every cycle:
python pipeline/build_live.py     # -> site/public/data/bracket.json
python pipeline/elo.py            # -> site/public/data/elo.json (incremental)
python pipeline/simulate.py       # -> site/public/data/odds.json

# Run-once historical (do NOT put this in cron):
python pipeline/build_historical.py  # -> site/public/img/br_2022_*.png + historical.json
```

### 3. Site

```bash
cd site
npm install
npm run dev        # http://localhost:5173
npm run build      # -> site/dist
npm run preview    # serves the built site locally
```

## Deployment (GitHub Pages via Actions)

The workflow at `.github/workflows/update.yml`:

- Runs every 6 hours (`cron: 0 */6 * * *`) and on `workflow_dispatch`.
- Re-runs `build_live.py → elo.py → simulate.py`.
- Commits any JSON changes back to `main` (so Elo persists across runs).
- Builds the Vite site with the correct base path.
- Deploys the built artifact to GitHub Pages.

The historical pipeline is **not** scheduled — StatsBomb open data is static,
so those PNGs and `historical.json` are generated once and committed.

### One-time setup (from a shell where `gh` is authenticated)

```bash
# 1. Create the public repo and push
gh repo create world-cup-dash --public --source=. --remote=origin --push

# 2. Add the token as an Actions secret
gh secret set FOOTBALL_DATA_TOKEN --body "$FOOTBALL_DATA_TOKEN"

# 3. Enable Pages (Actions source)
gh api -X POST repos/:owner/:repo/pages -f "build_type=workflow" \
  || gh api -X PUT  repos/:owner/:repo/pages -f "build_type=workflow"

# 4. Kick off the first run
gh workflow run update.yml
```

The site will be live at `https://<user>.github.io/world-cup-dash/` a couple
of minutes later.

## Design notes

- **Bracket connections.** football-data.org only fills a match's team fields
  when both parents are finished. `build_live.py` records observed parents;
  `simulate.py` fills the unobserved gaps by pairing free slots in id order.
  `odds.json` exposes `topologyObserved` counts so the UI can flag which
  rounds are still speculative.
- **Elo updates.** K=50 with the eloratings.net goal-difference multiplier
  (1 / 1.5 / (11+GD)/8). Penalty shootouts count as draws (both teams get
  0.5); extra-time wins count as normal wins.
- **Pinned team.** Default is Brazil (team id 764). Picker in the header
  changes the accent colors and highlights the country across all views.

## Repo layout

```
pipeline/
  build_live.py         # live matches + bracket derivation
  elo.py                # incremental Elo update
  simulate.py           # Monte-Carlo bracket sim
  build_historical.py   # StatsBomb Brazil-2022 shot maps (run once)
  build_elo_seed.py     # one-shot: eloratings.net → seed
  common.py
  data/
    elo_seed.json       # committed baseline Elo (48 teams)
  cache/                # gitignored — regenerated per run
site/
  src/
    App.jsx
    components/
      Bracket.jsx
      Odds.jsx
      Historical.jsx
    styles.css
    teamColors.js
    useJson.js
  public/
    data/*.json         # bracket, elo, odds, historical
    img/br_2022_*.png   # shot maps
.github/workflows/update.yml
```
