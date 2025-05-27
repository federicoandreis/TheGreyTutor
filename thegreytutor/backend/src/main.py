"""
The Grey Tutor Backend - Main FastAPI Application

A multi-agent AI system for Middle Earth learning with Gandalf's wisdom.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import structlog
import uvicorn

from .core.config import settings
from .core.logging import setup_logging
from .api.routes import auth, chat, agents, health, analytics
from .database.connection import init_db, close_db
from .services.cache import init_redis, close_redis
from .services.agent_orchestrator import AgentOrchestrator

# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    logger.info("Starting The Grey Tutor backend...")
    
    # Initialize database connections
    await init_db()
    logger.info("Database initialized")
    
    # Initialize Redis cache
    await init_redis()
    logger.info("Redis cache initialized")
    
    # Initialize Agent Orchestrator
    orchestrator = AgentOrchestrator()
    await orchestrator.initialize()
    app.state.orchestrator = orchestrator
    logger.info("Agent orchestrator initialized")
    
    logger.info("The Grey Tutor backend started successfully")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down The Grey Tutor backend...")
    
    await orchestrator.shutdown()
    await close_redis()
    await close_db()
    
    logger.info("The Grey Tutor backend shut down successfully")

# Create FastAPI application
app = FastAPI(
    title="The Grey Tutor API",
    description="AI-powered Middle Earth learning platform with multi-agent architecture",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

@app.get("/")
async def root():
    """Root endpoint with welcome message."""
    return {
        "message": "Welcome to The Grey Tutor API",
        "version": "1.0.0",
        "description": "AI-powered Middle Earth learning platform",
        "gandalf_quote": "All we have to decide is what to do with the time that is given us.",
        "docs": "/docs" if settings.ENVIRONMENT == "development" else "Contact admin for API documentation"
    }

@app.get("/status")
async def status():
    """System status endpoint."""
    return {
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "agents_available": True,
        "database_connected": True,
        "cache_connected": True
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler with structured logging."""
    logger.error(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method
    )
    return {
        "error": True,
        "status_code": exc.status_code,
        "message": exc.detail,
        "gandalf_wisdom": "Even the very wise cannot see all ends."
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unexpected errors."""
    logger.error(
        "Unexpected error occurred",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True
    )
    return {
        "error": True,
        "status_code": 500,
        "message": "An unexpected error occurred",
        "gandalf_wisdom": "I will not say: do not weep; for not all tears are an evil."
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )
