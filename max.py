import os
import sys
import signal
import uvicorn
import argparse
from typing import Optional

from api.main_api import app  # Import the FastAPI app
from api.config import Settings
from api.dependencies import get_settings
from utils.loggers import LoggerSetup


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Max Assistant API Server")
    parser.add_argument("--host", help="Host to bind the server (overrides env settings)")
    parser.add_argument("--port", type=int, help="Port to run the server (overrides env settings)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    return parser.parse_args()


def configure_signal_handlers():
    """Configure graceful shutdown on signals."""
    def handle_exit(signum, frame):
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        # Cleanup resources
        LoggerSetup.shutdown()
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)


def run_api():
    """Runs the FastAPI application using Uvicorn."""
    try:
        # Parse command line arguments
        args = parse_arguments()

        # Get application settings
        settings = get_settings()

        # Override settings with command line arguments if provided
        host = args.host or settings.uvicorn_host
        port = args.port or settings.uvicorn_port
        debug = args.debug or settings.debug

        # Configure logging
        log_level = "debug" if debug else "info"
        log_setup = LoggerSetup()
        logger = log_setup.get_logger("max", "max.log")
        logger.info(f"Starting Max Assistant API v{settings.api_version}")

        # Ensure data directories exist
        settings.setup_directories()

        # Configure signal handlers for graceful shutdown
        configure_signal_handlers()

        # Log startup information
        logger.info(f"Server running at http://{host}:{port}")
        logger.info(f"API documentation available at http://{host}:{port}/docs")
        logger.info(f"Using LLM provider: {settings.llm_provider}")

        # Run the application
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_level,
            reload=args.reload
        )
    except Exception:
        print(f"Error starting server.")
        logger.exception("Error starting server.")
        sys.exit(1)


if __name__ == "__main__":
    run_api()
