
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Application Settings
    APP_NAME = os.getenv("APP_NAME", "Career Advisor Chatbot")
    APP_DESCRIPTION = os.getenv("APP_DESCRIPTION", "AI-powered career guidance and professional development")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 4096))
    TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "app.log")
    
    # Session Configuration
    MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", 20))
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", 30))
    
    @staticmethod
    def validate_config():
    
        if not Config.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set. "
                "Please add it to your .env file."
            )
        
        if Config.TEMPERATURE < 0 or Config.TEMPERATURE > 1:
            raise ValueError("TEMPERATURE must be between 0 and 1.")
        
        if Config.MAX_TOKENS < 1:
            raise ValueError("MAX_TOKENS must be greater than 0.")


def get_config() -> Config:
    Config.validate_config()
    return Config
