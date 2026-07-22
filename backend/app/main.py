from fastapi import FastAPI

from app.api.routes import api_router

app = FastAPI(title="CABRUCA API")
app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
