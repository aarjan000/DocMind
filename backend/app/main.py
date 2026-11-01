from fastapi import FastAPI
app = FastAPI(
    title="DocMind API",
    description="Cloud backend for the DocMind multilingual RAG application.",
    version="0.1.0",
)
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "application": "DocMind API",
        "version": "0.1.0",
    }
