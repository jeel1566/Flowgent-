"""FastAPI main application for Flowgent backend."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models.schemas import HealthCheck
from api.routes import router as api_router
from mcp.n8n_client import get_mcp_client

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Flowgent API",
    description="AI-powered backend for Flowgent n8n assistant",
    version="1.0.0"
)

# Configure CORS for Chrome Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify extension ID
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/", response_model=HealthCheck)
async def root():
    """Root endpoint."""
    return HealthCheck(status="healthy", version="1.0.0")


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    # Check MCP connection status
    mcp_client = get_mcp_client()
    mcp_connected = await mcp_client.check_connection()
    
    return HealthCheck(
        status="healthy",
        version="1.0.0",
        mcp_connected=mcp_connected
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port, reload=True)
