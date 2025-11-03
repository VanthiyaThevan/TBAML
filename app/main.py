"""
TBAML System - Main FastAPI Application
UC1: Line of Business Verification
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import setup_logging, get_logger
from pydantic_settings import BaseSettings

# Setup logging
setup_logging()
logger = get_logger(__name__)


class Settings(BaseSettings):
    """Application settings"""
    app_name: str = "TBAML System"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore"  # Ignore extra fields from .env (like API keys)
    }


settings = Settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Trade-Based Anti-Money Laundering System - UC1: Line of Business Verification",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Application starting up", version=settings.app_version)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Application shutting down")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


# Include API routes
from app.api.routes import router as api_router
app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

