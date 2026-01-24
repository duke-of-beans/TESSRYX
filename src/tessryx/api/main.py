"""Main FastAPI application for TESSRYX API."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import close_db, init_db
from .routers_entities import router as entities_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="TESSRYX API",
    description="Universal Dependency Intelligence System",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(entities_router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint.
    
    Returns:
        API information
    """
    return {
        "name": "TESSRYX API",
        "version": "0.1.0",
        "description": "Universal Dependency Intelligence System",
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint.
    
    Returns:
        Health status
    """
    return {"status": "healthy"}
