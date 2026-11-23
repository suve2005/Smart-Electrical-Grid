"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORS_ORIGINS, is_mock_firebase, is_production

app = FastAPI(
    title="Smart Electrical Grid Backend",
    description="Firebase Authentication with PostgreSQL-backed profiles and authorization",
    version="1.0.0",
    debug=not is_production(),
)

# VS Code Live Server normally runs on 5500. Preserve any additional
# comma-separated origins configured in .env.
DEFAULT_CORS_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:5501",
    "http://127.0.0.1:5501",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if is_production():
    allowed_origins = CORS_ORIGINS
else:
    allowed_origins = list(dict.fromkeys(DEFAULT_CORS_ORIGINS + CORS_ORIGINS))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1.endpoints import router

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "Smart Electrical Grid Backend",
        "version": "1.0.0",
        "environment": "production" if is_production() else "development",
        "firebase_status": "mock" if is_mock_firebase() else "real",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "backend"}
