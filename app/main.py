"""FastAPI application main entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import is_mock_firebase, is_production, CORS_ORIGINS

app = FastAPI(
    title="Smart Electrical Grid Backend",
    description="Backend for registration and login with Firebase Auth + Postgres",
    version="1.0.0",
    debug=is_production() is False,
)

# CORS middleware
if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Default development CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API routes
from app.api.v1.endpoints import router
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint returning service info."""
    return {
        "message": "Smart Electrical Grid Backend",
        "version": "1.0.0",
        "environment": is_production() and "production" or "development",
        "firebase_status": "mock" if is_mock_firebase() else "real",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "backend"}