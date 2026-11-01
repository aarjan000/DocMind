from fastapi import FastAPI
from app.core.config import get_settings
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description="Cloud backend for the DocMind multilingual RAG application.",
    version=settings.app_version,
)
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "application": settings.app_name,
        "version": settings.app_version,
    }
