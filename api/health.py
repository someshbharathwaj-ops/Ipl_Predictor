from fastapi import FastAPI

from backend.web.api_handlers import get_health_payload

app = FastAPI()

@app.get("/")
def health() -> dict[str, str]:
    return get_health_payload()
