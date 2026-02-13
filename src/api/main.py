"""
Main API server combining REST, GraphQL, and WebSocket support.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from loguru import logger

from src.api.rest import app as rest_app
from src.api.graphql_api import graphql_router
from config.settings import settings


# Create main FastAPI app
app = FastAPI(
    title="OpenSearch-Docling-GraphRAG API",
    description="Unified API with REST, GraphQL, and WebSocket support",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API
app.mount("/", rest_app)

# Mount GraphQL API
app.include_router(graphql_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "OpenSearch-Docling-GraphRAG API",
        "version": "1.0.0",
        "endpoints": {
            "rest_docs": "/api/docs",
            "graphql": "/api/graphql",
            "websocket": "/api/ws"
        }
    }


if __name__ == "__main__":
    logger.info("Starting API server...")
    uvicorn.run(
        "src.api.main:app",
        host=settings.app_host,
        port=8000,
        reload=True,
        log_level="info"
    )

# Made with Bob
