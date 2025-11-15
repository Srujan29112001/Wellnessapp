"""
Main FastAPI application with GraphQL integration
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from contextlib import asynccontextmanager
import logging
import time

from backend.api.routes import api_router
from backend.api.graphql_app import graphql_app
from backend.database.postgres import init_db, close_db
from backend.database.mongo import init_mongo, close_mongo
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown events
    """
    # Startup
    logger.info("Starting Wellness AI Backend...")

    # Initialize databases
    try:
        await init_db()
        logger.info("PostgreSQL database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL: {e}")

    try:
        await init_mongo()
        logger.info("MongoDB initialized")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Wellness AI Backend...")
    await close_db()
    await close_mongo()
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered holistic wellness platform with EEG analysis and personalized coaching",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Wellness AI API",
        "docs": "/docs",
        "graphql": "/graphql",
        "health": "/health"
    }


# Include REST API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Mount GraphQL app
app.mount("/graphql", graphql_app)

# Prometheus metrics
if settings.ENVIRONMENT == "production":
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

logger.info(f"FastAPI application configured - Environment: {settings.ENVIRONMENT}")
