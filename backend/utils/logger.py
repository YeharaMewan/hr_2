import logging
import sys
import os
from typing import Optional

# Import settings with fallback
try:
    from backend.config.settings import settings
except ImportError:
    from config.settings import settings

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir, exist_ok=True)

# Configure logging handlers
def setup_logging():
    """Setup logging configuration"""
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Add file handler if logs directory exists
    log_file_path = os.path.join(logs_dir, 'hr_system.log')
    try:
        file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))
        handlers.append(file_handler)
    except Exception as e:
        print(f"Warning: Could not create log file handler: {e}")
    
    # Configure basic logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format=settings.LOG_FORMAT,
        handlers=handlers,
        force=True  # Override any existing configuration
    )

# Setup logging when module is imported
setup_logging()

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name"""
    logger = logging.getLogger(name)
    
    # Ensure logger has appropriate level
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    return logger

def log_agent_interaction(agent_name: str, user_id: str, action: str, result: str):
    """Log agent interactions for monitoring and debugging"""
    logger = get_logger(f"agent.{agent_name}")
    logger.info(f"User: {user_id} | Action: {action} | Result: {result[:100]}...")

def log_system_event(event_type: str, message: str, level: str = "INFO"):
    """Log system-wide events"""
    logger = get_logger("system")
    log_level = getattr(logging, level.upper())
    logger.log(log_level, f"[{event_type}] {message}")