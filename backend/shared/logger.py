"""Logging configuration"""
import logging
from shared.config import settings

def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
