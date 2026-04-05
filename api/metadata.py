from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.main import load_key_players_by_team, load_team_history, shortlisted_teams

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def metadata() -> dict[str, Any]:
    team_history = load_team_history()
    teams = shortlisted_teams(team_history)
    key_players_by_team = load_key_players_by_team()
    return {
        "teams": teams,
        "key_players_by_team": {
            team: key_players_by_team.get(team, [])
            for team in teams
        },
    }
