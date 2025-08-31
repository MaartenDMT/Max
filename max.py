import uvicorn
from pydantic_settings import BaseSettings

from api.main_api import app  # Import the FastAPI app


class Settings(BaseSettings):
    uvicorn_host: str = "0.0.0.0"
    uvicorn_port: int = 8000


def run_api():
    """Runs the FastAPI application using Uvicorn."""
    settings = Settings()
    uvicorn.run(app, host=settings.uvicorn_host, port=settings.uvicorn_port)


if __name__ == "__main__":
    run_api()
