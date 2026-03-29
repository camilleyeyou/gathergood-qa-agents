"""Type-safe environment configuration via pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_URL: str = "https://event-management-production-ad62.up.railway.app/api/v1"
    BASE_URL: str = "https://event-management-two-red.vercel.app"
    STRIPE_TEST_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
