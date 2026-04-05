"""Shared API contracts and handlers for local and deployed entrypoints."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
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


def get_health_payload() -> dict[str, str]:
    """Return the health response for the API."""

    return {"status": "ok"}


def get_metadata_payload() -> dict[str, Any]:
    """Return teams and key-player options for the frontend."""

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


def get_prediction_payload(payload: PredictPayload) -> dict[str, Any]:
    """Run the match prediction workflow and normalize validation errors."""

    try:
        request = PredictionRequest(**payload.model_dump())
        return predict_match_outcome(request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
