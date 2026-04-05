from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.main import PredictionRequest, predict_match_outcome

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictPayload(BaseModel):
    team1: str = Field(..., min_length=1)
    team2: str = Field(..., min_length=1)
    toss_winner: str = Field(..., min_length=1)
    user_predicted_score_team1: int = Field(..., ge=60, le=260)
    user_predicted_score_team2: int = Field(..., ge=60, le=260)
    key_player_team1: str = Field(..., min_length=1)
    key_player_team2: str = Field(..., min_length=1)


@app.post("/")
def predict(payload: PredictPayload) -> dict[str, Any]:
    try:
        request = PredictionRequest(**payload.model_dump())
        return predict_match_outcome(request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
