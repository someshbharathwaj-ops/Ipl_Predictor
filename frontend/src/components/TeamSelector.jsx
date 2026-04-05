const TEAM_GRADIENTS = {
  "Chennai Super Kings": "linear-gradient(135deg, #facc15, #d97706)",
  "Mumbai Indians": "linear-gradient(135deg, #60a5fa, #1d4ed8)",
  "Royal Challengers Bengaluru": "linear-gradient(135deg, #ef4444, #111827)",
  "Kolkata Knight Riders": "linear-gradient(135deg, #c084fc, #581c87)",
  "Rajasthan Royals": "linear-gradient(135deg, #f472b6, #7c3aed)",
  "Delhi Capitals": "linear-gradient(135deg, #38bdf8, #1d4ed8)",
  "Sunrisers Hyderabad": "linear-gradient(135deg, #fb923c, #b91c1c)",
  "Punjab Kings": "linear-gradient(135deg, #fb7185, #991b1b)",
  "Gujarat Titans": "linear-gradient(135deg, #94a3b8, #0f172a)",
  "Lucknow Super Giants": "linear-gradient(135deg, #67e8f9, #0f766e)",
};

function initials(team) {
  return team
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 3)
    .toUpperCase();
}

function TeamSelector({ title, helper, teams, selectedTeam, excludedTeam, onSelectTeam }) {
  const availableTeams = teams.filter((team) => team === selectedTeam || team !== excludedTeam);

  return (
    <section className="selector-block">
      <div className="selector-header">
        <h2>{title}</h2>
        <span>{helper}</span>
      </div>

      <div className="team-grid">
        {availableTeams.map((team) => (
          <button
            key={team}
            type="button"
            className={`team-card ${selectedTeam === team ? "selected" : ""}`}
            onClick={() => onSelectTeam(team)}
          >
            <span className="team-icon" style={{ background: TEAM_GRADIENTS[team] }}>
              {initials(team)}
            </span>
            <span className="team-name">{team}</span>
          </button>
        ))}
      </div>
    </section>
  );
}

export default TeamSelector;
