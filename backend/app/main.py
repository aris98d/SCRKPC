from fastapi import FastAPI
from app.api.contracts import router as contracts_router

app = FastAPI(title="Contract Review Platform Demo")

app.include_router(contracts_router, prefix="/api/contracts", tags=["contracts"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
