from fastapi import FastAPI

app = FastAPI(title="Series 76 Assistant", version="0.1.0", description="Initial scaffold. Conversation agent and ingestion are not implemented yet.")

@app.get("/health")
def health() -> dict[str, str]:
    """Process liveness only; does not claim database or agent readiness."""
    return {"status": "ok", "stage": "ocr-prototype"}
