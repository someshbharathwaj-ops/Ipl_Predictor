import { motion } from "framer-motion";

function ProbabilityBar({ team, value, accentClass }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm text-slate-200">
        <span>{team}</span>
        <span>{Math.round(value * 100)}%</span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-white/10">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.max(6, value * 100)}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className={`h-full rounded-full ${accentClass}`}
        />
      </div>
    </div>
  );
}

export default function PredictionPanel({ prediction, loading }) {
  return (
    <section className="glass-panel rounded-[28px] p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-cyan-200/70">AI vs user</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">Outcome simulator</h2>
        </div>
        {loading ? (
          <div className="rounded-full border border-cyan-400/30 px-4 py-2 text-xs uppercase tracking-[0.25em] text-cyan-200">
            AI thinking...
          </div>
        ) : null}
      </div>

      {!prediction ? (
        <div className="rounded-3xl border border-dashed border-white/15 p-8 text-center text-slate-300">
          Select teams, shape the match setup, and launch the simulation.
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-3xl border border-white/10 bg-slate-950/55 p-5">
              <div className="text-xs uppercase tracking-[0.3em] text-slate-400">User prediction</div>
              <div className="mt-4 space-y-3 text-slate-100">
                <div className="flex justify-between"><span>{prediction.team1}</span><span>{prediction.user_predicted_score_team1}</span></div>
                <div className="flex justify-between"><span>{prediction.team2}</span><span>{prediction.user_predicted_score_team2}</span></div>
              </div>
            </div>

            <div className="rounded-3xl border border-cyan-400/20 bg-slate-950/65 p-5 shadow-neon">
              <div className="text-xs uppercase tracking-[0.3em] text-cyan-200">AI prediction</div>
              <div className="mt-4 space-y-3 text-slate-100">
                <div className="flex justify-between"><span>{prediction.team1}</span><span>{prediction.ai_predicted_score_team1}</span></div>
                <div className="flex justify-between"><span>{prediction.team2}</span><span>{prediction.ai_predicted_score_team2}</span></div>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-white/10 bg-slate-950/55 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-xs uppercase tracking-[0.3em] text-slate-400">Winner</div>
                <div className="mt-2 text-3xl font-semibold text-white">{prediction.winner_name}</div>
              </div>
              <div className="rounded-full border border-cyan-400/30 px-4 py-2 text-sm text-cyan-100">
                Confidence: {prediction.confidence}
              </div>
            </div>

            <div className="mt-6 space-y-4">
              <ProbabilityBar team={prediction.team1} value={prediction.team1_win_probability} accentClass="bg-gradient-to-r from-cyan-400 to-teal-500" />
              <ProbabilityBar team={prediction.team2} value={prediction.team2_win_probability} accentClass="bg-gradient-to-r from-orange-400 to-rose-500" />
            </div>

            <div className="mt-6 grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl bg-white/5 p-4 text-sm text-slate-200">
                <div className="text-xs uppercase tracking-[0.3em] text-slate-400">Key player signals</div>
                <div className="mt-3">{prediction.key_player_team1}</div>
                <div>{prediction.key_player_team2}</div>
              </div>
              <div className="rounded-2xl bg-white/5 p-4 text-sm text-slate-200">
                <div className="text-xs uppercase tracking-[0.3em] text-slate-400">AI verdict</div>
                <div className="mt-3">
                  {prediction.ai_agrees_with_user ? "AI agrees with your scoreboard direction." : "AI disagrees with your scoreboard direction."}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
