import logging
import os
from logging.handlers import RotatingFileHandler


class LoggerSetup:
    def __init__(self, log_dir="data/logs"):
        """
        Initializes the LoggerSetup with a directory for log files.
        """
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def get_logger(self, logger_name, log_file, level=logging.INFO):
        """
        Returns a logger with the specified name and log file.

        :param logger_name: The name of the logger.
        :param log_file: The file to log messages to.
        :param level: Logging level (e.g., logging.INFO, logging.DEBUG).
        :return: Configured logger.
        """
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

        # Check if the logger already has handlers
        if not logger.handlers:
            # Create rotating file handler to cap log size
            file_handler = RotatingFileHandler(
                os.path.join(self.log_dir, log_file), maxBytes=5 * 1024 * 1024, backupCount=3
            )
            file_handler.setLevel(level)

            # Create console handler with configurable log level (default INFO in dev)
            console_level_name = os.getenv("LOG_CONSOLE_LEVEL", "INFO").upper()
            console_level = getattr(logging, console_level_name, logging.INFO)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(console_level)

            # Create formatter and add it to the handlers
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Add the handlers to the logger
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger


# Example usage:
if __name__ == "__main__":
    # Initialize the logger setup
    log_setup = LoggerSetup()

    # Create loggers for different parts of the project
    app_logger = log_setup.get_logger("app_logger", "app.log")
    db_logger = log_setup.get_logger("db_logger", "db.log", level=logging.DEBUG)
    api_logger = log_setup.get_logger("api_logger", "api.log", level=logging.WARNING)

    # Log some messages
    app_logger.info("This is an info message from the app logger.")
    db_logger.debug("This is a debug message from the database logger.")
    api_logger.warning("This is a warning message from the API logger.")
