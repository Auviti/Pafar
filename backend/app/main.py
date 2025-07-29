"""
Main FastAPI application for the Pafar Transport Management Platform.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.core.redis import redis_client
from app.api.v1 import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await redis_client.connect()
    await init_db()
    yield
    # Shutdown
    await redis_client.disconnect()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.pafar.com"]
)

# Include API routes
app.include_router(auth.router, prefix=settings.API_V1_STR)

# Import and include fleet router
from app.api.v1 import fleet
app.include_router(fleet.router, prefix=f"{settings.API_V1_STR}/fleet", tags=["fleet"])

# Import and include booking router
from app.api.v1 import bookings
app.include_router(bookings.router, prefix=settings.API_V1_STR)

# Import and include payment router
from app.api.v1 import payments
app.include_router(payments.router, prefix=f"{settings.API_V1_STR}/payments", tags=["payments"])

# Import and include tracking router
from app.api.v1 import tracking
app.include_router(tracking.router, prefix=f"{settings.API_V1_STR}/tracking", tags=["tracking"])

# Import and include websocket router
from app.api.v1 import websocket
app.include_router(websocket.router, prefix=f"{settings.API_V1_STR}", tags=["websocket"])

# Import and include reviews router
from app.api.v1 import reviews
app.include_router(reviews.router, prefix=f"{settings.API_V1_STR}", tags=["reviews"])

# Import and include admin router
from app.api.v1 import admin
app.include_router(admin.router, prefix=settings.API_V1_STR)

# Import and include maps router
from app.api.v1 import maps
app.include_router(maps.router, prefix=f"{settings.API_V1_STR}/maps", tags=["maps"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )