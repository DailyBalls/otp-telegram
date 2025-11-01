"""
Logging utility module for the Telegram bot.
Configures logging with timestamps and file output.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from os import getenv, makedirs


def setup_logger(web_id: str = None, log_dir: str = "logs") -> logging.Logger:
    """
    Setup logger with timestamp and file output.
    
    Args:
        web_id: The web ID to use for log file naming (format: {web_id}.log)
        log_dir: Directory to store log files (default: "logs")
    
    Returns:
        Configured logger instance
    """
    # Get web_id from environment if not provided
    if web_id is None:
        web_id = getenv("WEB_ID", "bot")
    
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Create log file name
    log_file = log_path / f"{web_id}.log"
    
    # Create logger
    logger = logging.getLogger("bot")
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter with timestamp
    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Console handler (optional, for development)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger() -> logging.Logger:
    """
    Get the configured logger instance.
    If logger hasn't been setup, creates a default one.
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger("bot")
    if not logger.handlers:
        # If logger not initialized, setup with default
        return setup_logger()
    return logger

