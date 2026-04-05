const state = {
  teams: [],
  keyPlayersByTeam: {},
  team1: "",
  team2: "",
  tossWinner: "",
  keyPlayerTeam1: "",
  keyPlayerTeam2: "",
  userScoreTeam1: 180,
  userScoreTeam2: 170,
};

const el = {
  team1Grid: document.getElementById("team1Grid"),
  team2Grid: document.getElementById("team2Grid"),
  tossWinner: document.getElementById("tossWinner"),
  keyPlayerTeam1: document.getElementById("keyPlayerTeam1"),
  keyPlayerTeam2: document.getElementById("keyPlayerTeam2"),
  scoreTeam1: document.getElementById("scoreTeam1"),
  scoreTeam2: document.getElementById("scoreTeam2"),
  team1ScoreValue: document.getElementById("team1ScoreValue"),
  team2ScoreValue: document.getElementById("team2ScoreValue"),
  team1ScoreLabel: document.getElementById("team1ScoreLabel"),
  team2ScoreLabel: document.getElementById("team2ScoreLabel"),
  simulateButton: document.getElementById("simulateButton"),
  errorBanner: document.getElementById("errorBanner"),
  thinkingChip: document.getElementById("thinkingChip"),
  resultPlaceholder: document.getElementById("resultPlaceholder"),
  resultContent: document.getElementById("resultContent"),
  scoreboardPlaceholder: document.getElementById("scoreboardPlaceholder"),
  scoreboardContent: document.getElementById("scoreboardContent"),
  userScores: document.getElementById("userScores"),
  aiScores: document.getElementById("aiScores"),
  winnerName: document.getElementById("winnerName"),
  confidenceBadge: document.getElementById("confidenceBadge"),
  team1ProbabilityLabel: document.getElementById("team1ProbabilityLabel"),
  team2ProbabilityLabel: document.getElementById("team2ProbabilityLabel"),
  team1ProbabilityValue: document.getElementById("team1ProbabilityValue"),
  team2ProbabilityValue: document.getElementById("team2ProbabilityValue"),
  team1Bar: document.getElementById("team1Bar"),
  team2Bar: document.getElementById("team2Bar"),
  keyPlayersText: document.getElementById("keyPlayersText"),
  agreementText: document.getElementById("agreementText"),
  scoreboardTeam1Label: document.getElementById("scoreboardTeam1Label"),
  scoreboardTeam2Label: document.getElementById("scoreboardTeam2Label"),
  scoreboardTeam1Value: document.getElementById("scoreboardTeam1Value"),
  scoreboardTeam2Value: document.getElementById("scoreboardTeam2Value"),
};

function setError(message = "") {
  el.errorBanner.textContent = message;
  el.errorBanner.classList.toggle("hidden", !message);
}

function initials(team) {
  return team.split(" ").map((part) => part[0]).join("").slice(0, 3);
}

function gradientForTeam(team) {
  const palette = {
    "Chennai Super Kings": "linear-gradient(135deg, #facc15, #d97706)",
    "Mumbai Indians": "linear-gradient(135deg, #60a5fa, #312e81)",
    "Royal Challengers Bengaluru": "linear-gradient(135deg, #ef4444, #111827)",
    "Kolkata Knight Riders": "linear-gradient(135deg, #c084fc, #581c87)",
    "Rajasthan Royals": "linear-gradient(135deg, #f472b6, #7c3aed)",
    "Delhi Capitals": "linear-gradient(135deg, #38bdf8, #1d4ed8)",
    "Sunrisers Hyderabad": "linear-gradient(135deg, #fb923c, #b91c1c)",
    "Punjab Kings": "linear-gradient(135deg, #fb7185, #991b1b)",
    "Gujarat Titans": "linear-gradient(135deg, #94a3b8, #0f172a)",
    "Lucknow Super Giants": "linear-gradient(135deg, #67e8f9, #0f766e)",
  };
  return palette[team] ?? "linear-gradient(135deg, #27f5d1, #1f4d6d)";
}

function createTeamCard(team, selectedTeam, onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `team-card ${selectedTeam === team ? "selected" : ""}`;
  button.innerHTML = `
    <div class="team-icon" style="background:${gradientForTeam(team)}">${initials(team)}</div>
    <div>${team}</div>
  `;
  button.addEventListener("click", onClick);
  return button;
}

function populateSelect(select, options, selected) {
  select.innerHTML = "";
  options.forEach((option) => {
    const elOption = document.createElement("option");
    elOption.value = option;
    elOption.textContent = option;
    if (option === selected) {
      elOption.selected = true;
    }
    select.appendChild(elOption);
  });
}

function renderTeamGrids() {
  el.team1Grid.innerHTML = "";
  el.team2Grid.innerHTML = "";

  state.teams.forEach((team) => {
    el.team1Grid.appendChild(
      createTeamCard(team, state.team1, () => {
        state.team1 = team;
        if (state.team2 === team) {
          state.team2 = state.teams.find((candidate) => candidate !== team) ?? "";
        }
        hydrateSelections();
      }),
    );
  });

  state.teams
    .filter((team) => team !== state.team1)
    .forEach((team) => {
      el.team2Grid.appendChild(
        createTeamCard(team, state.team2, () => {
          state.team2 = team;
          hydrateSelections();
        }),
      );
    });
}

function hydrateSelections() {
  const tossOptions = [state.team1, state.team2].filter(Boolean);
  if (!tossOptions.includes(state.tossWinner)) {
    state.tossWinner = tossOptions[0] ?? "";
  }

  const team1Players = state.keyPlayersByTeam[state.team1] ?? [];
  const team2Players = state.keyPlayersByTeam[state.team2] ?? [];
  if (!team1Players.includes(state.keyPlayerTeam1)) {
    state.keyPlayerTeam1 = team1Players[0] ?? "";
  }
  if (!team2Players.includes(state.keyPlayerTeam2)) {
    state.keyPlayerTeam2 = team2Players[0] ?? "";
  }

  renderTeamGrids();
  populateSelect(el.tossWinner, tossOptions, state.tossWinner);
  populateSelect(el.keyPlayerTeam1, team1Players, state.keyPlayerTeam1);
  populateSelect(el.keyPlayerTeam2, team2Players, state.keyPlayerTeam2);

  el.team1ScoreValue.textContent = state.userScoreTeam1;
  el.team2ScoreValue.textContent = state.userScoreTeam2;
  el.team1ScoreLabel.textContent = `User predicted ${state.team1 || "Team 1"} score`;
  el.team2ScoreLabel.textContent = `User predicted ${state.team2 || "Team 2"} score`;
}

async function loadMetadata() {
  const response = await fetch("/metadata");
  if (!response.ok) {
    throw new Error("Failed to load metadata from backend");
  }
  const data = await response.json();
  state.teams = data.teams ?? [];
  state.keyPlayersByTeam = data.key_players_by_team ?? {};
  state.team1 = state.teams[0] ?? "";
  state.team2 = state.teams[1] ?? "";
  hydrateSelections();
}

function renderPrediction(prediction) {
  el.resultPlaceholder.classList.add("hidden");
  el.resultContent.classList.remove("hidden");
  el.scoreboardPlaceholder.classList.add("hidden");
  el.scoreboardContent.classList.remove("hidden");

  el.userScores.innerHTML = `
    <div class="probability-label"><span>${prediction.team1}</span><strong>${prediction.user_predicted_score_team1}</strong></div>
    <div class="probability-label" style="margin-top:10px"><span>${prediction.team2}</span><strong>${prediction.user_predicted_score_team2}</strong></div>
  `;
  el.aiScores.innerHTML = `
    <div class="probability-label"><span>${prediction.team1}</span><strong>${prediction.ai_predicted_score_team1}</strong></div>
    <div class="probability-label" style="margin-top:10px"><span>${prediction.team2}</span><strong>${prediction.ai_predicted_score_team2}</strong></div>
  `;
  el.winnerName.textContent = prediction.winner_name;
  el.confidenceBadge.textContent = `Confidence: ${prediction.confidence}`;
  el.team1ProbabilityLabel.textContent = prediction.team1;
  el.team2ProbabilityLabel.textContent = prediction.team2;
  el.team1ProbabilityValue.textContent = `${Math.round(prediction.team1_win_probability * 100)}%`;
  el.team2ProbabilityValue.textContent = `${Math.round(prediction.team2_win_probability * 100)}%`;
  el.team1Bar.style.width = `${Math.max(6, prediction.team1_win_probability * 100)}%`;
  el.team2Bar.style.width = `${Math.max(6, prediction.team2_win_probability * 100)}%`;
  el.keyPlayersText.innerHTML = `${prediction.key_player_team1}<br />${prediction.key_player_team2}`;
  el.agreementText.textContent = prediction.ai_agrees_with_user
    ? "AI agrees with your scoreboard direction."
    : "AI disagrees with your scoreboard direction.";
  el.scoreboardTeam1Label.textContent = prediction.team1;
  el.scoreboardTeam2Label.textContent = prediction.team2;
  el.scoreboardTeam1Value.textContent = prediction.ai_predicted_scorecard_team1;
  el.scoreboardTeam2Value.textContent = prediction.ai_predicted_scorecard_team2;
}

async function simulate() {
  setError("");
  el.thinkingChip.classList.remove("hidden");
  try {
    const response = await fetch("/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        team1: state.team1,
        team2: state.team2,
        toss_winner: state.tossWinner,
        user_predicted_score_team1: state.userScoreTeam1,
        user_predicted_score_team2: state.userScoreTeam2,
        key_player_team1: state.keyPlayerTeam1,
        key_player_team2: state.keyPlayerTeam2,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail ?? "Prediction failed");
    }
    renderPrediction(payload);
  } catch (error) {
    setError(error.message);
  } finally {
    el.thinkingChip.classList.add("hidden");
  }
}

el.tossWinner.addEventListener("change", (event) => {
  state.tossWinner = event.target.value;
});

el.keyPlayerTeam1.addEventListener("change", (event) => {
  state.keyPlayerTeam1 = event.target.value;
});

el.keyPlayerTeam2.addEventListener("change", (event) => {
  state.keyPlayerTeam2 = event.target.value;
});

el.scoreTeam1.addEventListener("input", (event) => {
  state.userScoreTeam1 = Number(event.target.value);
  hydrateSelections();
});

el.scoreTeam2.addEventListener("input", (event) => {
  state.userScoreTeam2 = Number(event.target.value);
  hydrateSelections();
});

el.simulateButton.addEventListener("click", simulate);

loadMetadata().catch((error) => {
  setError(error.message);
});
