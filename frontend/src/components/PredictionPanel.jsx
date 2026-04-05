function ProbabilityRow({ label, value, tone }) {
  return (
    <div className="probability-row">
      <div className="probability-label">
        <span>{label}</span>
        <span>{Math.round((value ?? 0) * 100)}%</span>
      </div>
      <div className="bar-shell">
        <div className={`bar-fill ${tone}`} style={{ width: `${Math.max(6, (value ?? 0) * 100)}%` }} />
      </div>
    </div>
  );
}

function PredictionPanel({ prediction, loading }) {
  const showPlaceholder = !prediction;

  return (
    <section className="panel result-panel">
      <p className="eyebrow">AI VS USER</p>
      <h2>Outcome simulator</h2>
      {loading ? <div className="thinking-chip">AI THINKING...</div> : null}

      {showPlaceholder ? (
        <div className="placeholder">Select teams, shape the match setup, and launch the simulation.</div>
      ) : (
        <div className="prediction-body">
          <div className="prediction-split">
            <div className="split-card">
              <div className="card-eyebrow">USER PREDICTION</div>
              <div className="score-pair">
                <span>{prediction.team1}</span>
                <strong>{prediction.user_predicted_score_team1}</strong>
              </div>
              <div className="score-pair">
                <span>{prediction.team2}</span>
                <strong>{prediction.user_predicted_score_team2}</strong>
              </div>
            </div>

            <div className="split-card neon-border">
              <div className="card-eyebrow accent">AI PREDICTION</div>
              <div className="score-pair">
                <span>{prediction.team1}</span>
                <strong>{prediction.ai_predicted_score_team1}</strong>
              </div>
              <div className="score-pair">
                <span>{prediction.team2}</span>
                <strong>{prediction.ai_predicted_score_team2}</strong>
              </div>
            </div>
          </div>

          <div className="winner-card">
            <div>
              <div className="card-eyebrow">WINNER</div>
              <div className="winner-name">{prediction.winner_name}</div>
            </div>
            <div className="confidence-badge">Confidence: {prediction.confidence}</div>
          </div>

          <div className="probability-group">
            <ProbabilityRow label={prediction.team1} value={prediction.team1_win_probability} tone="cyan" />
            <ProbabilityRow label={prediction.team2} value={prediction.team2_win_probability} tone="ember" />
          </div>

          <div className="insight-grid">
            <div className="insight-card">
              <div className="card-eyebrow">KEY PLAYER SIGNALS</div>
              <div>{prediction.key_player_team1}</div>
              <div>{prediction.key_player_team2}</div>
            </div>

            <div className="insight-card">
              <div className="card-eyebrow">AI VERDICT</div>
              <div>
                {prediction.ai_agrees_with_user
                  ? "AI agrees with your scoreboard direction."
                  : "AI disagrees with your scoreboard direction."}
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

export default PredictionPanel;
