import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener
from queue import Queue
from typing import Dict, Optional, Any


class LoggerSetup:
    """
    High-performance logging utility that provides consistent logging across the application.
    Features:
    - Asynchronous logging with queue-based handlers for minimal impact on application performance
    - File rotation to prevent logs from growing too large
    - Console and file output with different formatting
    - Consistent log formatting across the application
    - Singleton pattern to avoid duplicate loggers
    - Thread-safe implementation
    """

    # Cache for loggers to implement singleton pattern
    _loggers: Dict[str, logging.Logger] = {}
    # Queue listeners for async logging
    _listeners: Dict[str, QueueListener] = {}
    # Thread pool for background logging tasks
    _executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="logger")

    def __init__(self, log_dir="data/logs", max_size_mb=10, backup_count=5):
        """
        Initialize the logger setup with the given log directory.

        Args:
            log_dir: Directory to store log files
            max_size_mb: Maximum size of log files in MB before rotation
            backup_count: Number of backup files to keep
        """
        self.log_dir = log_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.backup_count = backup_count
        os.makedirs(log_dir, exist_ok=True)

    def get_logger(self, logger_name, log_file, level=logging.INFO):
        """
        Returns a logger with the specified name and log file.
        Uses a singleton pattern to ensure only one logger per name is created.

        Args:
            logger_name: The name of the logger
            log_file: The file to log messages to
            level: Logging level (e.g., logging.INFO, logging.DEBUG)

        Returns:
            Configured logger instance
        """
        # Return cached logger if it exists
        if logger_name in self._loggers:
            return self._loggers[logger_name]

        # Create a new logger
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

        # Prevent propagation to root logger to avoid duplicate logs
        logger.propagate = False

        # Remove existing handlers if any
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Set up queue-based logging for performance
        log_queue = Queue(-1)  # No limit on queue size

        # Create formatters
        file_formatter = logging.Formatter(
            fmt='%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )

        # Create handlers
        file_handler = RotatingFileHandler(
            os.path.join(self.log_dir, log_file),
            maxBytes=self.max_size_bytes,
            backupCount=self.backup_count,
            delay=True  # Only open file when needed
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)

        # Console level is configurable
        console_level_name = os.getenv("LOG_CONSOLE_LEVEL", "INFO").upper()
        console_level = getattr(logging, console_level_name, logging.INFO)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(console_formatter)

        # Set up queue listener in background thread
        queue_listener = QueueListener(
            log_queue, file_handler, console_handler, respect_handler_level=True
        )
        queue_listener.start()

        # Save listener reference
        self._listeners[logger_name] = queue_listener

        # Add queue handler to logger
        queue_handler = QueueHandler(log_queue)
        logger.addHandler(queue_handler)

        # Cache and return the logger
        self._loggers[logger_name] = logger
        return logger


    @staticmethod
    def get_log_level_from_string(level_name: str) -> int:
        """Convert a string log level to its numeric value"""
        return getattr(logging, level_name.upper(), logging.INFO)

    @classmethod
    def shutdown(cls):
        """Properly shut down all loggers and listeners"""
        for name, listener in cls._listeners.items():
            listener.stop()
        cls._executor.shutdown(wait=True)
        cls._loggers.clear()
        cls._listeners.clear()

    @classmethod
    def log_exception(cls, logger, exc: Exception, message: str = "Exception occurred"):
        """
        Log an exception with full traceback and context information

        Args:
            logger: The logger to use
            exc: The exception to log
            message: Optional message to include
        """
        import traceback
        tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        logger.error(f"{message}: {str(exc)}\n{tb}")


# Example usage:
if __name__ == "__main__":
    try:
        # Initialize the logger setup
        log_setup = LoggerSetup(log_dir="logs", max_size_mb=5)

        # Create loggers for different parts of the project
        app_logger = log_setup.get_logger("app_logger", "app.log")
        db_logger = log_setup.get_logger("db_logger", "db.log", level=logging.DEBUG)
        api_logger = log_setup.get_logger("api_logger", "api.log", level=logging.WARNING)

        # Log some messages
        app_logger.info("This is an info message from the app logger.")
        db_logger.debug("This is a debug message from the database logger.")
        api_logger.warning("This is a warning message from the API logger.")

        # Test exception logging
        try:
            1/0
        except Exception as e:
            LoggerSetup.log_exception(app_logger, e, "Division error")

    finally:
        # Ensure proper shutdown
        LoggerSetup.shutdown()
