import React from "react";

const pct = (v) => (v * 100).toFixed(1) + "%";

export default function Odds({ odds, pinnedId }) {
  const teams = odds.teams.filter((t) => t.probR16 > 0);
  const max = Math.max(0.001, ...teams.map((t) => t.probChampion));

  return (
    <>
      <p className="note">
        {odds.nSims.toLocaleString()} simulations · seed {odds.seed} ·{" "}
        topology observed: R16={odds.topologyObserved?.LAST_16 ?? 0}/8, QF={odds.topologyObserved?.QUARTER_FINALS ?? 0}/4, SF={odds.topologyObserved?.SEMI_FINALS ?? 0}/2, F={odds.topologyObserved?.FINAL ?? 0}/1
      </p>

      <div className="odds-grid" role="table" aria-label="cup-win probability">
        <div className="h">#</div>
        <div className="h">TLA</div>
        <div className="h">team</div>
        <div className="h">win probability →</div>
        <div className="h">%</div>

        {teams.slice(0, 20).map((t, i) => {
          const isPinned = t.id === pinnedId;
          const w = (t.probChampion / max) * 100;
          return (
            <div className={"row " + (isPinned ? "pinned" : "")} key={t.id}>
              <div className="rank">{i + 1}</div>
              <div className="tla">{t.tla}</div>
              <div className="name">{t.name}</div>
              <div className="bar" aria-hidden>
                <span style={{ width: `${w}%` }} />
              </div>
              <div className="pct">{pct(t.probChampion)}</div>
            </div>
          );
        })}
      </div>

      <table className="stage-table" aria-label="stage probabilities">
        <thead>
          <tr>
            <th>team</th>
            <th>R16</th>
            <th>QF</th>
            <th>SF</th>
            <th>Final</th>
            <th>Cup</th>
          </tr>
        </thead>
        <tbody>
          {teams.slice(0, 12).map((t) => {
            const isPinned = t.id === pinnedId;
            return (
              <tr key={t.id} className={isPinned ? "pinned" : ""}>
                <td>{t.tla} · {t.name}</td>
                <td>{pct(t.probR16)}</td>
                <td>{pct(t.probQF)}</td>
                <td>{pct(t.probSF)}</td>
                <td>{pct(t.probFinal)}</td>
                <td>{pct(t.probChampion)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </>
  );
}
