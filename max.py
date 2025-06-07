import uvicorn
from api.main_api import app  # Import the FastAPI app


def run_api():
    """Runs the FastAPI application using Uvicorn."""
    uvicorn.run(app, host="localhost", port=8000)


if __name__ == "__main__":
    run_api()
