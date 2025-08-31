from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from pydantic_settings import BaseSettings
except Exception:  # pragma: no cover - optional during tests
    from pydantic import BaseModel as BaseSettings

from api.routers import ai_router, system_router  # Import the FastAPI routers
from api.routers.enhanced_ai_router import enhanced_ai_router  # Import enhanced router


class Settings(BaseSettings):
    api_title: str = "Max Assistant API"
    api_desc: str = "A central hub for various AI and System functionalities."
    api_version: str = "1.0.0"
    cors_origins: list[str] = ["http://localhost", "http://localhost:3000", "*"]


settings = Settings()

app = FastAPI(
    title=settings.api_title,
    description=settings.api_desc,
    version=settings.api_version,
)

app.include_router(ai_router.router)
app.include_router(system_router.router)
app.include_router(enhanced_ai_router)  # Add enhanced AI router

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Max Assistant API! Visit /docs for API documentation."
    }
