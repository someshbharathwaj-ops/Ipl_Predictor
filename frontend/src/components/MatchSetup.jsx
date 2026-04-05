export default function MatchSetup({
  teams,
  keyPlayersByTeam,
  formData,
  onChange,
}) {
  const team1Players = keyPlayersByTeam[formData.team1] ?? [];
  const team2Players = keyPlayersByTeam[formData.team2] ?? [];

  return (
    <section className="glass-panel rounded-[28px] p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-cyan-200/70">Match setup</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">Tune the simulation</h2>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <label className="space-y-2">
          <span className="text-sm text-slate-200">Toss winner</span>
          <select
            value={formData.toss_winner}
            onChange={(event) => onChange("toss_winner", event.target.value)}
            className="w-full rounded-2xl border border-cyan-400/20 bg-slate-950/70 px-4 py-3 text-white outline-none"
          >
            {teams.map((team) => (
              <option key={team} value={team}>
                {team}
              </option>
            ))}
          </select>
        </label>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="space-y-2">
            <span className="text-sm text-slate-200">Key player: Team 1</span>
            <select
              value={formData.key_player_team1}
              onChange={(event) => onChange("key_player_team1", event.target.value)}
              className="w-full rounded-2xl border border-cyan-400/20 bg-slate-950/70 px-4 py-3 text-white outline-none"
            >
              {team1Players.map((player) => (
                <option key={player} value={player}>
                  {player}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-2">
            <span className="text-sm text-slate-200">Key player: Team 2</span>
            <select
              value={formData.key_player_team2}
              onChange={(event) => onChange("key_player_team2", event.target.value)}
              className="w-full rounded-2xl border border-cyan-400/20 bg-slate-950/70 px-4 py-3 text-white outline-none"
            >
              {team2Players.map((player) => (
                <option key={player} value={player}>
                  {player}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-5">
          <div className="flex items-center justify-between text-sm text-slate-200">
            <span>User predicted {formData.team1 || "Team 1"} score</span>
            <span className="text-xl font-semibold text-gold">{formData.user_predicted_score_team1}</span>
          </div>
          <input
            type="range"
            min="120"
            max="220"
            value={formData.user_predicted_score_team1}
            onChange={(event) => onChange("user_predicted_score_team1", Number(event.target.value))}
            className="mt-4 w-full accent-cyan-400"
          />
        </div>

        <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-5">
          <div className="flex items-center justify-between text-sm text-slate-200">
            <span>User predicted {formData.team2 || "Team 2"} score</span>
            <span className="text-xl font-semibold text-ember">{formData.user_predicted_score_team2}</span>
          </div>
          <input
            type="range"
            min="120"
            max="220"
            value={formData.user_predicted_score_team2}
            onChange={(event) => onChange("user_predicted_score_team2", Number(event.target.value))}
            className="mt-4 w-full accent-orange-400"
          />
        </div>
      </div>
    </section>
  );
}
