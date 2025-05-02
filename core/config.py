# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file
class Settings(BaseSettings):
    """
    Application settings loaded from .env file or environment variables.
    """
    # MongoDB Settings
    mongodb_uri: str = os.getenv("MONGODB_URI")
    mongodb_db_name: str = os.getenv("MONGODB_DB_NAME")

    # Gemini API Key
    gemini_api_key: str = os.getenv("GEMINI_API_KEY")

    # FastAPI/Uvicorn Settings (Optional examples)
    # host: str = "127.0.0.1"
    # port: int = 8000

    # Tells pydantic-settings to load from a .env file
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore' # Ignore extra fields from env vars/file
    )

# Use lru_cache to load settings only once
@lru_cache
def get_settings() -> Settings:
    """Returns the application settings."""
    return Settings()

# Make settings easily accessible
settings = get_settings()

# Example usage (optional, just for testing):
# if __name__ == "__main__":
#     print("Loaded Settings:")
#     print(f"MongoDB URI: {settings.mongodb_uri}")
#     print(f"MongoDB DB Name: {settings.mongodb_db_name}")
#     # Be careful printing API keys, even in tests
#     # print(f"Gemini API Key: {settings.gemini_api_key[:5]}...")