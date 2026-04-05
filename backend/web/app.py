"""FastAPI app for IPL winner and score prediction."""

from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.web.api_handlers import (
    PredictPayload,
    get_health_payload,
    get_metadata_payload,
    get_prediction_payload,
)


app = FastAPI(title="IPL Predictor API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
api_router = APIRouter(prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "IPL Predictor API is running. Use /api/health, /api/metadata, and /api/predict."}


@api_router.get("/health")
def health() -> dict[str, str]:
    return get_health_payload()


@api_router.get("/metadata")
def metadata() -> dict[str, object]:
    return get_metadata_payload()


@api_router.post("/predict")
def predict(payload: PredictPayload) -> dict[str, object]:
    return get_prediction_payload(payload)


app.include_router(api_router)
