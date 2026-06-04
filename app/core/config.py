from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    newsapi_key: Optional[str] = None
    serpapi_key: Optional[str] = None
    baidu_api_key: Optional[str] = None
    twitter_bearer_token: Optional[str] = None

    # Database
    database_url: str = "sqlite:///./finalert.db"

    # App Settings
    app_name: str = "FinAlert API"
    debug: bool = False
    refresh_interval_minutes: int = 5

    # Alert Settings
    default_sentiment_threshold: float = 0.3
    default_impact_threshold: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
