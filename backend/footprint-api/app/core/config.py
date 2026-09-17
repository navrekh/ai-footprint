from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-based application configuration.

    All values may be overridden via environment variables or a local
    .env file. See .env.example for the documented set of variables.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Required configuration (per FRD / sprint brief section 3)
    DATABASE_URL: str = "postgresql+asyncpg://footprint:footprint@localhost:5432/footprint"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    API_KEY_PREFIX: str = "afp_dev"

    # Non-secret application metadata
    PROJECT_NAME: str = "AI Footprint API"
    API_V1_PREFIX: str = "/v1"

    # Bounds referenced by the batch endpoint (section 21)
    MAX_BATCH_SIZE: int = 100

    @property
    def sync_database_url(self) -> str:
        """Synchronous (psycopg) equivalent of DATABASE_URL, used by Alembic."""
        if "+asyncpg" in self.DATABASE_URL:
            return self.DATABASE_URL.replace("+asyncpg", "+psycopg")
        return self.DATABASE_URL

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
