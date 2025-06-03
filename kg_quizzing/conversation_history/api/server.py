"""
Standalone API server for conversation history.

This module provides a standalone FastAPI server for testing the conversation history API.
"""
import os
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .router import router as conversation_router

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI application
    """
    # Create the FastAPI app
    app = FastAPI(
        title="Conversation History API",
        description="API for storing and retrieving conversation history",
        version="0.1.0",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include the conversation router
    app.include_router(conversation_router)
    
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint."""
        return {
            "message": "Conversation History API",
            "docs_url": "/docs",
            "redoc_url": "/redoc",
        }
    
    return app


def main():
    """Run the standalone API server."""
    # Create the FastAPI app
    app = create_app()
    
    # Get configuration from environment variables
    host = os.getenv("CONVERSATION_API_HOST", "0.0.0.0")
    port = int(os.getenv("CONVERSATION_API_PORT", "8000"))
    
    # Run the server
    logger.info(f"Starting Conversation History API server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
