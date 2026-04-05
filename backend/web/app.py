"""FastAPI app for IPL winner and score prediction."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.main import (
    PredictionRequest,
    load_key_players_by_team,
    load_team_history,
    predict_match_outcome,
    shortlisted_teams,
)

class PredictPayload(BaseModel):
    team1: str = Field(..., min_length=1)
    team2: str = Field(..., min_length=1)
    toss_winner: str = Field(..., min_length=1)
    user_predicted_score_team1: int = Field(..., ge=60, le=260)
    user_predicted_score_team2: int = Field(..., ge=60, le=260)
    key_player_team1: str = Field(..., min_length=1)
    key_player_team2: str = Field(..., min_length=1)


app = FastAPI(title="IPL Predictor API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "IPL Predictor API is running. Use the React frontend from /frontend or a deployed app."}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metadata")
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


@app.post("/predict")
def predict(payload: PredictPayload) -> dict[str, Any]:
    try:
        request = PredictionRequest(**payload.model_dump())
        return predict_match_outcome(request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
