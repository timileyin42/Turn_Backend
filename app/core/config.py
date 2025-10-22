"""
Application configuration using Pydantic v2 settings.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = Field(alias="APP_NAME")
    environment: str = Field(alias="ENVIRONMENT")
    debug: bool = Field(alias="DEBUG")
    
    # Database
    database_url: str = Field(alias="DATABASE_URL")
    database_url_sync: str = Field(alias="DATABASE_URL_SYNC")
    
    # Security
    secret_key: str = Field(alias="SECRET_KEY")
    algorithm: str = Field(alias="ALGORITHM")
    access_token_expire_minutes: int = Field(alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # AI Services - FREE ALTERNATIVES ONLY
    # openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")  # REMOVED - PAID
    # elevenlabs_api_key: Optional[str] = Field(default=None, alias="ELEVENLABS_API_KEY")  # REMOVED - PAID
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")  # Google Gemini - FREE TIER
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")  # Groq - FREE TIER
    
    # Email Configuration - Brevo (Free tier: 300 emails/day)
    brevo_api_key: Optional[str] = Field(default=None, alias="BREVO_API_KEY")
    brevo_sender_email: str = Field(alias="BREVO_SENDER_EMAIL")
    brevo_sender_name: str = Field(alias="BREVO_SENDER_NAME")
    brevo_base_url: str = Field(alias="BREVO_BASE_URL")
    from_email: str = Field(alias="FROM_EMAIL")
    
    # Email verification enabled with Brevo
    email_verification_enabled: bool = Field(alias="EMAIL_VERIFICATION_ENABLED")
    
    # File Storage - Cloudinary (Free tier: 25GB storage, 25GB bandwidth/month)
    cloudinary_cloud_name: Optional[str] = Field(default=None, alias="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: Optional[str] = Field(default=None, alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: Optional[str] = Field(default=None, alias="CLOUDINARY_API_SECRET")
    
    # Redis
    redis_url: str = Field(alias="REDIS_URL")
    
    # External Services
    stripe_publishable_key: Optional[str] = Field(default=None, alias="STRIPE_PUBLISHABLE_KEY")
    stripe_secret_key: Optional[str] = Field(default=None, alias="STRIPE_SECRET_KEY")
    
    # Termii SMS Configuration (African markets)
    termii_api_key: Optional[str] = Field(default=None, alias="TERMII_API_KEY")
    termii_sender_id: str = Field(alias="TERMII_SENDER_ID")
    
    # YouTube Data API Configuration (Free tier: 10,000 units/day)
    youtube_api_key: Optional[str] = Field(default=None, alias="YOUTUBE_API_KEY")
    
    # Job Scraping
    job_scraping_enabled: bool = Field(alias="JOB_SCRAPING_ENABLED")
    
    # CORS Settings
    allowed_hosts: str = Field(alias="ALLOWED_HOSTS")
    
    # Frontend and Platform URLs
    frontend_url: str = Field(alias="FRONTEND_URL")
    platform_url: str = Field(alias="PLATFORM_URL")
    help_center_url: str = Field(alias="HELP_CENTER_URL")
    
    # Social Media URLs
    social_linkedin: str = Field(alias="SOCIAL_LINKEDIN")
    social_twitter: str = Field(alias="SOCIAL_TWITTER")
    social_facebook: str = Field(alias="SOCIAL_FACEBOOK")
    social_instagram: str = Field(alias="SOCIAL_INSTAGRAM")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() in ("development", "dev", "local")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() in ("production", "prod")


# Global settings instance
settings = Settings()