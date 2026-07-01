import React from "react";

const STAGE_ORDER = [
  { code: "LAST_32", label: "R32" },
  { code: "LAST_16", label: "R16" },
  { code: "QUARTER_FINALS", label: "QF" },
  { code: "SEMI_FINALS", label: "SF" },
  { code: "FINAL", label: "Final" },
];

function TeamRow({ team, score, isWinner, isLoser, isPinned }) {
  const tla = team?.tla ?? "???";
  const cls = ["tla", isPinned && "is-pinned"].filter(Boolean).join(" ");
  return (
    <>
      {team?.crest ? (
        <img className="crest" src={team.crest} alt="" loading="lazy" />
      ) : (
        <span className="flag" />
      )}
      <span className={cls}>{tla}</span>
      <span className={"score " + (isWinner ? "win" : isLoser ? "loser" : "")}>
        {score ?? "—"}
      </span>
    </>
  );
}

function TieCard({ match, pinnedId }) {
  const home = match.home;
  const away = match.away;
  const played = match.played;
  const winnerId = match.winnerId;

  const homeIsWinner = played && winnerId === home?.id;
  const awayIsWinner = played && winnerId === away?.id;
  const pinnedInvolved =
    (home?.id === pinnedId) || (away?.id === pinnedId);
  const bothTbd = !home && !away;

  const cls = [
    "tie",
    played ? "played" : "upcoming",
    pinnedInvolved ? "pinned" : "",
    bothTbd ? "tbd" : "",
  ].filter(Boolean).join(" ");

  const dt = match.utcDate ? new Date(match.utcDate) : null;
  const when = dt
    ? dt.toLocaleDateString(undefined, { month: "short", day: "numeric" })
    : "TBD";

  return (
    <div className={cls}>
      <TeamRow
        team={home}
        score={played ? match.score?.home : null}
        isWinner={homeIsWinner}
        isLoser={played && !homeIsWinner}
        isPinned={home?.id === pinnedId}
      />
      <TeamRow
        team={away}
        score={played ? match.score?.away : null}
        isWinner={awayIsWinner}
        isLoser={played && !awayIsWinner}
        isPinned={away?.id === pinnedId}
      />
      <div className="meta-line">
        {played ? (
          <>
            played
            {match.score?.duration && match.score.duration !== "REGULAR" ? (
              <> · <span className="duration">
                {match.score.duration === "PENALTY_SHOOTOUT" ? "pens" : "AET"}
              </span></>
            ) : null}
          </>
        ) : (
          <>{when}</>
        )}
      </div>
    </div>
  );
}

export default function Bracket({ bracket, pinnedId }) {
  const stages = new Map(bracket.stages.map((s) => [s.code, s]));

  return (
    <div className="bracket-scroll">
      <div className="bracket">
        {STAGE_ORDER.map(({ code, label }) => {
          const s = stages.get(code);
          if (!s) return null;
          return (
            <div className="column" key={code}>
              <div className="col-head">{label}</div>
              <div className="matches">
                {s.matches.map((m) => (
                  <TieCard key={m.id} match={m} pinnedId={pinnedId} />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
