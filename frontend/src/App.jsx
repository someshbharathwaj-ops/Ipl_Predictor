import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import MatchSetup from "./components/MatchSetup";
import PredictionPanel from "./components/PredictionPanel";
import ScoreBoard from "./components/ScoreBoard";
import TeamSelector from "./components/TeamSelector";
import { fetchMetadata, predictMatch } from "./services/api";

function createInitialForm(teams = [], keyPlayersByTeam = {}) {
  const team1 = teams[0] ?? "";
  const team2 = teams[1] ?? teams[0] ?? "";
  return {
    team1,
    team2,
    toss_winner: team1,
    user_predicted_score_team1: 180,
    user_predicted_score_team2: 170,
    key_player_team1: keyPlayersByTeam[team1]?.[0] ?? "",
    key_player_team2: keyPlayersByTeam[team2]?.[0] ?? "",
  };
}

export default function App() {
  const [teams, setTeams] = useState([]);
  const [keyPlayersByTeam, setKeyPlayersByTeam] = useState({});
  const [formData, setFormData] = useState(createInitialForm());
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function boot() {
      try {
        const metadata = await fetchMetadata();
        setTeams(metadata.teams ?? []);
        setKeyPlayersByTeam(metadata.key_players_by_team ?? {});
        setFormData(createInitialForm(metadata.teams ?? [], metadata.key_players_by_team ?? {}));
      } catch (fetchError) {
        setError(fetchError.message);
      }
    }
    boot();
  }, []);

  function updateField(field, value) {
    setFormData((current) => {
      const next = { ...current, [field]: value };
      if (field === "team1") {
        next.toss_winner = value;
        next.key_player_team1 = keyPlayersByTeam[value]?.[0] ?? "";
      }
      if (field === "team2") {
        next.key_player_team2 = keyPlayersByTeam[value]?.[0] ?? "";
      }
      return next;
    });
  }

  async function runSimulation() {
    setLoading(true);
    setError("");
    try {
      const result = await predictMatch(formData);
      setPrediction(result);
    } catch (predictionError) {
      setError(predictionError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen px-4 py-8 text-white md:px-8 xl:px-12">
      <div className="mx-auto max-w-7xl space-y-8">
        <motion.header
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel grid-noise overflow-hidden rounded-[36px] p-8"
        >
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.45em] text-cyan-200/80">IPL Neural Match Lab</p>
              <h1 className="mt-4 max-w-3xl text-4xl font-bold leading-tight text-white md:text-6xl">
                Simulate the winner, pressure, and scoreline of the next IPL showdown.
              </h1>
              <p className="mt-4 max-w-2xl text-base text-slate-300 md:text-lg">
                A micrograd-powered match engine with historical form, scoreboard projection, and an AI-vs-user prediction duel.
              </p>
            </div>
            <button
              type="button"
              onClick={runSimulation}
              disabled={loading || !formData.team1 || !formData.team2}
              className="rounded-full bg-gradient-to-r from-cyan-400 to-emerald-400 px-7 py-4 text-sm font-semibold uppercase tracking-[0.3em] text-slate-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Simulating..." : "Launch Simulation"}
            </button>
          </div>
        </motion.header>

        {error ? (
          <div className="rounded-3xl border border-rose-400/30 bg-rose-500/10 px-5 py-4 text-rose-100">
            {error}
          </div>
        ) : null}

        <div className="grid gap-8 xl:grid-cols-[1.15fr_0.85fr]">
          <div className="space-y-8">
            <TeamSelector
              title="Select Team 1"
              teams={teams}
              selectedTeam={formData.team1}
              onSelect={(team) => updateField("team1", team)}
            />
            <TeamSelector
              title="Select Team 2"
              teams={teams.filter((team) => team !== formData.team1)}
              selectedTeam={formData.team2}
              onSelect={(team) => updateField("team2", team)}
            />
            <MatchSetup
              teams={[formData.team1, formData.team2].filter(Boolean)}
              keyPlayersByTeam={keyPlayersByTeam}
              formData={formData}
              onChange={updateField}
            />
          </div>

          <div className="space-y-8">
            <PredictionPanel prediction={prediction} loading={loading} />
            <ScoreBoard prediction={prediction} />
          </div>
        </div>
      </div>
    </main>
  );
}
