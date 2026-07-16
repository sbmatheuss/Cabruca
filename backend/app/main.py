from fastapi import FastAPI

app = FastAPI(title="CABRUCA API")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
