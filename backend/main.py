import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import BASE_DIR, HOST, PORT, DEBUG
from backend.api.routes import router as api_router, ollama_svc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SignBridge")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("==================================================")
    logger.info("   SIGNBRIDGE APPLICATION BACKEND STARTING UP    ")
    logger.info("   ASL & ISL Recognition | Translation | 3D Avatar")
    logger.info(f"   Server listening at: http://{HOST}:{PORT}")
    logger.info("==================================================")
    try:
        ollama_ok = ollama_svc.ensure_running()
        if ollama_ok:
            logger.info("   [Ollama] Local Ollama service is connected and active.")
        else:
            logger.warning("   [Ollama] Ollama could not be auto-started; fallback dictionary active.")
    except Exception as e:
        logger.warning(f"   [Ollama] Auto-start check notice: {e}")
    yield
    logger.info("SignBridge backend shutting down.")

app = FastAPI(
    title="SIGNBRIDGE API",
    description="Unified ASL + ISL Sign Recognition, Translation & 3D Signing Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local cross-origin development if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Mount API routes
app.include_router(api_router)

# Mount static frontend directory
frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

@app.get("/")
def serve_index():
    """Serves the single-page application dashboard."""
    index_file = BASE_DIR / "frontend" / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "SIGNBRIDGE Backend Running. frontend/index.html not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=DEBUG)
