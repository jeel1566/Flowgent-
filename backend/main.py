import os
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.routes import router
from models.schemas import HealthCheck
from n8n_mcp.n8n_client import get_mcp_client, N8nMcpClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
logger.info("Environment variables loaded")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup
    yield
    # Shutdown - close HTTP client
    try:
        client = get_mcp_client()
        await client.close()
    except Exception as e:
        print(f"Error closing MCP client: {e}")


app = FastAPI(
    title="Flowgent Backend",
    description="AI-powered n8n workflow assistant using Google ADK",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration - Allow all origins for chrome extension compatibility
# Chrome extensions use unique IDs, so we need to be permissive
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins_str == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

logger.info(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.include_router(router)


@app.get("/health", response_model=HealthCheck)
async def health():
    """Health check endpoint."""
    try:
        logger.info("Health check requested")
        connected = await get_mcp_client().check_connection()
        logger.info(f"MCP connection status: {connected}")
        return HealthCheck(status="healthy", version="2.0.0", mcp_connected=connected)
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return HealthCheck(status="degraded", version="2.0.0", mcp_connected=False)


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
