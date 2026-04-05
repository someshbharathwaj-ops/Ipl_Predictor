import { useEffect, useMemo, useState } from "react";
import MatchSetup from "./components/MatchSetup";
import PredictionPanel from "./components/PredictionPanel";
import ScoreBoard from "./components/ScoreBoard";
import TeamSelector from "./components/TeamSelector";
import { getMetadata, predictMatch } from "./services/api";

const DEFAULT_TEAM_SCORES = {
  team1: 180,
  team2: 170,
};

function App() {
  const [teams, setTeams] = useState([]);
  const [keyPlayersByTeam, setKeyPlayersByTeam] = useState({});
  const [selection, setSelection] = useState({
    team1: "",
    team2: "",
    tossWinner: "",
    keyPlayerTeam1: "",
    keyPlayerTeam2: "",
    userScoreTeam1: DEFAULT_TEAM_SCORES.team1,
    userScoreTeam2: DEFAULT_TEAM_SCORES.team2,
  });
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const data = await getMetadata();
        if (!active) {
          return;
        }

        const loadedTeams = data.teams ?? [];
        const loadedPlayers = data.key_players_by_team ?? {};
        const team1 = loadedTeams[0] ?? "";
        const team2 = loadedTeams[1] ?? "";

        setTeams(loadedTeams);
        setKeyPlayersByTeam(loadedPlayers);
        setSelection((current) => ({
          ...current,
          team1,
          team2,
          tossWinner: team1,
          keyPlayerTeam1: loadedPlayers[team1]?.[0] ?? "",
          keyPlayerTeam2: loadedPlayers[team2]?.[0] ?? "",
        }));
      } catch (loadError) {
        if (active) {
          setError(loadError.message);
        }
      }
    }

    load();

    return () => {
      active = false;
    };
  }, []);

  const team1Players = useMemo(
    () => keyPlayersByTeam[selection.team1] ?? [],
    [keyPlayersByTeam, selection.team1],
  );
  const team2Players = useMemo(
    () => keyPlayersByTeam[selection.team2] ?? [],
    [keyPlayersByTeam, selection.team2],
  );
  const tossOptions = useMemo(
    () => [selection.team1, selection.team2].filter(Boolean),
    [selection.team1, selection.team2],
  );

  useEffect(() => {
    if (!selection.team1 || !selection.team2) {
      return;
    }

    setSelection((current) => {
      const next = { ...current };

      if (!tossOptions.includes(current.tossWinner)) {
        next.tossWinner = tossOptions[0] ?? "";
      }
      if (!team1Players.includes(current.keyPlayerTeam1)) {
        next.keyPlayerTeam1 = team1Players[0] ?? "";
      }
      if (!team2Players.includes(current.keyPlayerTeam2)) {
        next.keyPlayerTeam2 = team2Players[0] ?? "";
      }

      return next;
    });
  }, [team1Players, team2Players, tossOptions, selection.team1, selection.team2]);

  function updateSelection(patch) {
    setSelection((current) => ({ ...current, ...patch }));
  }

  function handleSelectTeam(slot, team) {
    setSelection((current) => {
      const next = { ...current, [slot]: team };

      if (slot === "team1" && current.team2 === team) {
        next.team2 = teams.find((candidate) => candidate !== team) ?? "";
      }
      if (slot === "team2" && current.team1 === team) {
        next.team1 = teams.find((candidate) => candidate !== team) ?? "";
      }

      return next;
    });
  }

  async function handleSimulate() {
    if (!selection.team1 || !selection.team2) {
      setError("Please choose two teams before running the simulation.");
      return;
    }
    setError("");
    setLoading(true);

    try {
      const result = await predictMatch({
        team1: selection.team1,
        team2: selection.team2,
        toss_winner: selection.tossWinner,
        user_predicted_score_team1: selection.userScoreTeam1,
        user_predicted_score_team2: selection.userScoreTeam2,
        key_player_team1: selection.keyPlayerTeam1,
        key_player_team2: selection.keyPlayerTeam2,
      });
      setPrediction(result);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-shell">
      <div className="ambient ambient-a" />
      <div className="ambient ambient-b" />

      <main className="app-shell">
        <section className="hero-panel panel">
          <div className="hero-copy">
            <p className="eyebrow">IPL NEURAL MATCH LAB</p>
            <h1>Simulate the winner, pressure, and scoreline of the next IPL showdown.</h1>
            <p className="subcopy">
              A micrograd-powered match engine with historical form, scoreboard projection,
              and an AI-vs-user prediction duel.
            </p>
          </div>

          <button className="launch-button" type="button" onClick={handleSimulate} disabled={loading}>
            {loading ? "SIMULATING..." : "LAUNCH SIMULATION"}
          </button>
        </section>

        {error ? <div className="error-banner">{error}</div> : null}

        <div className="content-grid">
          <section className="left-rail">
            <TeamSelector
              title="Select Team 1"
              helper="Click a franchise"
              teams={teams}
              selectedTeam={selection.team1}
              excludedTeam={selection.team2}
              onSelectTeam={(team) => handleSelectTeam("team1", team)}
            />
            <TeamSelector
              title="Select Team 2"
              helper="Click a franchise"
              teams={teams}
              selectedTeam={selection.team2}
              excludedTeam={selection.team1}
              onSelectTeam={(team) => handleSelectTeam("team2", team)}
            />
            <MatchSetup
              selection={selection}
              tossOptions={tossOptions}
              team1Players={team1Players}
              team2Players={team2Players}
              onChange={updateSelection}
            />
          </section>

          <section className="right-rail">
            <PredictionPanel prediction={prediction} loading={loading} />
            <ScoreBoard prediction={prediction} />
          </section>
        </div>
      </main>
    </div>
  );
}

export default App;
