from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.contracts import router as contracts_router


app = FastAPI(title="Contract Review Platform Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contracts_router, prefix="/api/contracts", tags=["contracts"])


@app.get("/health")
def health_check():
    return {"status": "ok"}