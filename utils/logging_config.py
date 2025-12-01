"""Centralized logging configuration for HealthVista Analytics."""
import logging
import sys
import os
from pathlib import Path


# Configure root logger on import
_configured = False


def configure_app_logging():
    """
    Configure application-wide logging.
    This should be called once at application startup.
    """
    global _configured
    if _configured:
        return

    # Get log level from environment (default: INFO)
    log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)

    # Add file handler for application logs
    log_file = log_dir / 'hospital_dashboard.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logging.getLogger().addHandler(file_handler)

    _configured = True


def setup_logging(name='healthvista', log_file=None, level=logging.INFO):
    """
    Configure logging for a specific module.

    Args:
        name: Logger name
        log_file: Optional log file path
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    # Ensure app logging is configured
    if not _configured:
        configure_app_logging()

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # If specific log file requested, add handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance

    Example:
        >>> from utils.logging_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    if not _configured:
        configure_app_logging()

    return logging.getLogger(name)