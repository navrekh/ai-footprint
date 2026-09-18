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

    # Bounds referenced by POST /v1/compare and POST /v1/benchmarks/run
    # (sprint 4 FRD section 35.2)
    MAX_COMPARE_CANDIDATES: int = 10

    # Developer Console CORS allowlist (ADR-012): a comma-separated list of
    # exact origins, e.g. "http://localhost:5173,https://console.example.com".
    # Empty by default - CORS fails closed until an operator explicitly
    # configures the console's own origin(s) per environment. Never a
    # wildcard, per ADR-012.
    ALLOWED_ORIGINS: str = ""

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

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
