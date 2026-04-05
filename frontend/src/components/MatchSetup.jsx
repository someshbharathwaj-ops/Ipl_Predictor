function MatchSetup({ selection, tossOptions, team1Players, team2Players, onChange }) {
  return (
    <section className="panel setup-panel">
      <p className="eyebrow">MATCH SETUP</p>
      <h2>Tune the simulation</h2>

      <div className="form-grid">
        <label>
          <span>Toss winner</span>
          <select
            value={selection.tossWinner}
            onChange={(event) => onChange({ tossWinner: event.target.value })}
          >
            {tossOptions.map((team) => (
              <option key={team} value={team}>
                {team}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Key player: Team 1</span>
          <select
            value={selection.keyPlayerTeam1}
            onChange={(event) => onChange({ keyPlayerTeam1: event.target.value })}
          >
            {team1Players.map((player) => (
              <option key={player} value={player}>
                {player}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Key player: Team 2</span>
          <select
            value={selection.keyPlayerTeam2}
            onChange={(event) => onChange({ keyPlayerTeam2: event.target.value })}
          >
            {team2Players.map((player) => (
              <option key={player} value={player}>
                {player}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="slider-grid">
        <label className="slider-card">
          <div className="slider-head">
            <span>User predicted {selection.team1 || "Team 1"} score</span>
            <strong>{selection.userScoreTeam1}</strong>
          </div>
          <input
            type="range"
            min="120"
            max="220"
            value={selection.userScoreTeam1}
            onChange={(event) => onChange({ userScoreTeam1: Number(event.target.value) })}
          />
        </label>

        <label className="slider-card">
          <div className="slider-head">
            <span>User predicted {selection.team2 || "Team 2"} score</span>
            <strong>{selection.userScoreTeam2}</strong>
          </div>
          <input
            type="range"
            min="120"
            max="220"
            value={selection.userScoreTeam2}
            onChange={(event) => onChange({ userScoreTeam2: Number(event.target.value) })}
          />
        </label>
      </div>
    </section>
  );
}

export default MatchSetup;
