import { motion } from "framer-motion";

const TEAM_STYLES = {
  "Chennai Super Kings": "from-yellow-400 to-amber-600",
  "Mumbai Indians": "from-blue-400 to-indigo-700",
  "Royal Challengers Bengaluru": "from-red-500 to-zinc-800",
  "Royal Challengers Bangalore": "from-red-500 to-zinc-800",
  "Kolkata Knight Riders": "from-fuchsia-500 to-purple-800",
  "Rajasthan Royals": "from-pink-400 to-violet-700",
  "Delhi Capitals": "from-sky-400 to-blue-800",
  "Sunrisers Hyderabad": "from-orange-400 to-red-700",
  "Punjab Kings": "from-rose-500 to-red-800",
  "Kings XI Punjab": "from-rose-500 to-red-800",
  "Gujarat Titans": "from-slate-400 to-slate-800",
  "Lucknow Super Giants": "from-cyan-300 to-teal-700",
};

function initials(team) {
  return team
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 3);
}

export default function TeamSelector({ title, teams, selectedTeam, onSelect }) {
  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">{title}</h2>
        <span className="text-xs uppercase tracking-[0.35em] text-cyan-200/70">
          Click a franchise
        </span>
      </div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
        {teams.map((team) => {
          const selected = team === selectedTeam;
          return (
            <motion.button
              key={team}
              type="button"
              whileHover={{ y: -4, scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onSelect(team)}
              className={`glass-panel grid-noise rounded-3xl border p-4 text-left transition ${
                selected ? "team-card-selected" : "border-white/10"
              }`}
            >
              <div
                className={`mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br ${
                  TEAM_STYLES[team] ?? "from-cyan-400 to-slate-700"
                } text-lg font-bold text-white`}
              >
                {initials(team)}
              </div>
              <div className="text-sm font-medium text-white">{team}</div>
            </motion.button>
          );
        })}
      </div>
    </section>
  );
}
