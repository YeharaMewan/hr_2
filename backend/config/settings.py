# backend/config/settings.py - Fixed Configuration

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application configuration settings"""
    
    # Database Configuration - Fixed naming consistency
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/HRAgent")
    MONGODB_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/HRAgent")  # Alias for compatibility
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "HRAgent")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "86400"))  # 24 hours
    
    # Flask Configuration
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    DEBUG: bool = FLASK_ENV == "development"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5000"))
    
    # Multi-Agent Configuration
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "5"))
    AGENT_TIMEOUT: int = int(os.getenv("AGENT_TIMEOUT", "30"))
    MAX_HISTORY_LENGTH: int = int(os.getenv("MAX_HISTORY_LENGTH", "20"))
    
    # Gemini Model Configuration
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
    GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))
    GEMINI_MAX_TOKENS: int = int(os.getenv("GEMINI_MAX_TOKENS", "2048"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def validate(cls) -> None:
        """Validate required settings"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Use MONGO_URI for validation (the actual environment variable name)
        if not cls.MONGO_URI:
            raise ValueError("MONGO_URI environment variable is required")

settings = Settings()