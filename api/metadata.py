from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.web.api_handlers import get_metadata_payload

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def metadata() -> dict[str, object]:
    return get_metadata_payload()
