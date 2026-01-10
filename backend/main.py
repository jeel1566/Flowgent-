import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.routes import router
from models.schemas import HealthCheck
from n8n_mcp.n8n_client import get_mcp_client, N8nMcpClient

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup
    yield
    # Shutdown - close HTTP client
    await N8nMcpClient.close_client()


app = FastAPI(
    title="Flowgent Backend",
    description="AI-powered n8n workflow assistant using Google ADK",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "chrome-extension://*,http://localhost:*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", response_model=HealthCheck)
async def health():
    """Health check endpoint."""
    connected = await get_mcp_client().check_connection()
    return HealthCheck(status="healthy", version="2.0.0", mcp_connected=connected)


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Flowgent Backend",
        "version": "2.0.0",
        "description": "AI-powered n8n workflow assistant",
        "docs": "/docs"
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)
