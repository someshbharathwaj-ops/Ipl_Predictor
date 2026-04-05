from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.web.api_handlers import PredictPayload, get_prediction_payload

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/")
def predict(payload: PredictPayload) -> dict[str, object]:
    return get_prediction_payload(payload)
