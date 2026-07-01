import React from "react";
import { imgUrl } from "../useJson.js";

export default function Historical({ historical }) {
  return (
    <>
      <p className="note">
        {historical.source}. xG figures via StatsBomb; shot maps rendered with mplsoccer.
      </p>
      <div className="legend">
        <span><span className="dot" style={{ background: "#00d68f", border: "1px solid #ffcb0e" }} /> goal</span>
        <span><span className="dot" style={{ background: "#ff5c5c" }} /> no-goal</span>
        <span>size &rarr; xG</span>
      </div>
      <div className="hist-list">
        {historical.matches.map((m) => {
          const over = m.goals > m.xg;
          return (
            <div className="hist-match" key={m.matchId}>
              <div className="headline">
                <div className="h-title">
                  Brazil {m.score.brazil} – {m.score.opponent} {m.opponent}
                </div>
                <div className="h-meta">{m.stage} · {m.date}</div>
              </div>
              <div className="figures">
                <div><span className="k">shots</span> <span className="v">{m.shots}</span></div>
                <div><span className="k">xG</span> <span className="v">{m.xg.toFixed(2)}</span></div>
                <div>
                  <span className="k">goals</span>{" "}
                  <span className={"v " + (over ? "over" : "under")}>
                    {m.goals}
                    <span style={{ color: "var(--fg-dim)", marginLeft: "1ch" }}>
                      ({over ? "+" : ""}{(m.goals - m.xg).toFixed(2)} vs xG)
                    </span>
                  </span>
                </div>
              </div>
              <img src={imgUrl(m.image)} alt={`Shot map: Brazil vs ${m.opponent}`} />
            </div>
          );
        })}
      </div>
    </>
  );
}
