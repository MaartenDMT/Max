import logging

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.config import Settings
from api.dependencies import get_settings
from api.middleware import RateLimitMiddleware
from api.routers import ai_router, system_router  # Import the FastAPI routers
from api.routers.enhanced_ai_router import \
    enhanced_ai_router  # Import enhanced router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("max_api")

# Load settings from environment
settings = get_settings()

# Ensure data directories exist
settings.setup_directories()

app = FastAPI(
    title=settings.api_title,
    description=settings.api_desc,
    version=settings.api_version,
)

app.include_router(ai_router.router)
app.include_router(system_router.router)
app.include_router(enhanced_ai_router)  # Add enhanced AI router

# Add middlewares
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
if settings.rate_limit_enabled:
    app.add_middleware(
        RateLimitMiddleware,
        settings=settings,
        excluded_paths=["/health", "/docs", "/openapi.json", "/redoc"]
    )
    logger.info(f"Rate limiting enabled: {settings.rate_limit_requests} requests per {settings.rate_limit_timespan}s")


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"HTTP error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": exc.status_code,
            "message": exc.detail,
            "path": str(request.url)
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "code": 422,
            "message": "Validation error",
            "details": exc.errors(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": 500,
            "message": "Internal server error",
            "path": str(request.url)
        }
    )

@app.get("/")
async def root(settings: Settings = Depends(get_settings)):
    return {
        "message": "Welcome to Max Assistant API! Visit /docs for API documentation.",
        "version": settings.api_version,
        "status": "online"
    }

@app.get("/health")
async def health_check(settings: Settings = Depends(get_settings)):
    return {
        "status": "ok",
        "api_version": settings.api_version,
        "llm_provider": settings.llm_provider,
    }
