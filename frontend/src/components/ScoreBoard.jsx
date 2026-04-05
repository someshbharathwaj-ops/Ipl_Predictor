function ScoreBoard({ prediction }) {
  return (
    <section className="panel scoreboard-panel">
      <p className="eyebrow">ANIMATED SCOREBOARD</p>
      <h2>Projected match scoreline</h2>

      {!prediction ? (
        <div className="scoreboard-placeholder">
          AI scoreboard will light up after the first simulation run.
        </div>
      ) : (
        <div className="scoreboard-grid">
          <div className="score-line">
            <div className="card-eyebrow">{prediction.team1}</div>
            <div className="score-text gold">{prediction.ai_predicted_scorecard_team1}</div>
          </div>
          <div className="score-line">
            <div className="card-eyebrow">{prediction.team2}</div>
            <div className="score-text green">{prediction.ai_predicted_scorecard_team2}</div>
          </div>
        </div>
      )}
    </section>
  );
}

export default ScoreBoard;
