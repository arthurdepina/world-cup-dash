import React, { useMemo, useState, useEffect } from "react";
import Bracket from "./components/Bracket.jsx";
import Odds from "./components/Odds.jsx";
import Historical from "./components/Historical.jsx";
import { useJson } from "./useJson.js";
import { colorFor } from "./teamColors.js";

const TABS = [
  { key: "bracket", label: "bracket" },
  { key: "odds", label: "monte carlo" },
  { key: "historical", label: "brazil 2022" },
];

function formatWhen(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    year: "numeric", month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export default function App() {
  const bracket = useJson("bracket.json");
  const odds = useJson("odds.json");
  const historical = useJson("historical.json");
  const elo = useJson("elo.json");

  const [tab, setTab] = useState("bracket");
  const [pinnedId, setPinnedId] = useState(null);

  // Set default pinned once bracket loads.
  useEffect(() => {
    if (pinnedId === null && bracket.data) {
      setPinnedId(bracket.data.pinnedDefault ?? 764);
    }
  }, [bracket.data, pinnedId]);

  // Apply the pinned team's accent colors as CSS vars.
  useEffect(() => {
    if (pinnedId == null) return;
    const c = colorFor(pinnedId);
    document.documentElement.style.setProperty("--accent", c.primary);
    document.documentElement.style.setProperty("--accent-2", c.secondary);
  }, [pinnedId]);

  // Team list for picker (sorted by name), from elo.json when available.
  const teams = useMemo(() => {
    const src = elo.data?.teams ?? [];
    return [...src].sort((a, b) => a.name.localeCompare(b.name));
  }, [elo.data]);

  const anyError = bracket.error || odds.error || historical.error || elo.error;
  const loading = bracket.loading || odds.loading || historical.loading || elo.loading;

  return (
    <div className="app">
      <div className="header">
        <div>
          <div className="title">WC26 · dash</div>
          <div className="meta">
            world cup 2026 · living dashboard · monte-carlo odds · brazil 2022 shot maps
          </div>
        </div>
        <div>
          {pinnedId != null && (
            <span className="pinned-chip">
              <span className="dot" />
              pinned = {teams.find((t) => t.id === pinnedId)?.tla ?? "…"}
            </span>
          )}
        </div>
      </div>

      <nav className="nav">
        {TABS.map((t) => (
          <button
            key={t.key}
            className={tab === t.key ? "active" : ""}
            onClick={() => setTab(t.key)}
          >
            ▸ {t.label}
          </button>
        ))}
      </nav>

      <div className="picker">
        <label htmlFor="pinner">pin country</label>
        <select
          id="pinner"
          value={pinnedId ?? ""}
          onChange={(e) => setPinnedId(Number(e.target.value))}
        >
          {teams.map((t) => (
            <option key={t.id} value={t.id}>
              {t.tla} — {t.name}
            </option>
          ))}
        </select>
      </div>

      {anyError && (
        <div className="section">
          <h2>error</h2>
          <p className="note" style={{ color: "var(--loss)" }}>
            {String(anyError.message ?? anyError)}
          </p>
        </div>
      )}

      {loading && !anyError && (
        <div className="section"><p className="note">loading…</p></div>
      )}

      {tab === "bracket" && bracket.data && (
        <div className="section">
          <h2>knockout bracket</h2>
          <p className="note">
            source: {bracket.data.source} · generated {formatWhen(bracket.data.generatedAt)}
          </p>
          <Bracket bracket={bracket.data} pinnedId={pinnedId} />
        </div>
      )}

      {tab === "odds" && odds.data && (
        <div className="section">
          <h2>cup-win probability</h2>
          <Odds odds={odds.data} pinnedId={pinnedId} />
        </div>
      )}

      {tab === "historical" && historical.data && (
        <div className="section">
          <h2>brazil · 2022 world cup</h2>
          <Historical historical={historical.data} />
        </div>
      )}

      <div className="footer">
        data · football-data.org
        <span className="sep">·</span> eloratings.net (seed)
        <span className="sep">·</span> statsbomb (historical)
        <span className="sep">·</span>
        <a href="https://github.com/" target="_blank" rel="noreferrer">source on github</a>
      </div>
    </div>
  );
}
