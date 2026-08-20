from fastapi import FastAPI

app = FastAPI(
    title="Shigavox",
    description="Local-first open-source book-to-audio engine",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}