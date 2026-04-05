import { motion } from "framer-motion";

function ScoreLine({ label, score, accent }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-slate-950/55 p-4">
      <div className="text-xs uppercase tracking-[0.3em] text-slate-400">{label}</div>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`mt-3 text-4xl font-bold ${accent}`}
      >
        {score}
      </motion.div>
    </div>
  );
}

export default function ScoreBoard({ prediction }) {
  if (!prediction) {
    return (
      <div className="glass-panel rounded-[28px] p-6 text-slate-300">
        AI scoreboard will light up after the first simulation run.
      </div>
    );
  }

  return (
    <section className="glass-panel rounded-[28px] p-6">
      <div className="mb-5">
        <p className="text-xs uppercase tracking-[0.35em] text-cyan-200/70">Animated scoreboard</p>
        <h2 className="mt-2 text-2xl font-semibold text-white">Projected match scoreline</h2>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <ScoreLine label={prediction.team1} score={prediction.ai_predicted_scorecard_team1} accent="text-gold" />
        <ScoreLine label={prediction.team2} score={prediction.ai_predicted_scorecard_team2} accent="text-emerald-300" />
      </div>
    </section>
  );
}
