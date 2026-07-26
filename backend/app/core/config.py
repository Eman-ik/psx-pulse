from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app configuration, including the non-negotiable compliance gate flags.

    PUBLIC_LAUNCH_ENABLED, PUBLIC_SIGNALS_ENABLED and COMMERCIAL_DATA_ENABLED
    must stay False until PSX data-licensing and SECP research-regulation
    review has actually been completed and documented (see docs/rights_matrix.template.md).
    Do not flip these defaults in code — override via environment/.env only,
    and only after that review exists.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "PSX Fertilizer Research Platform"
    environment: str = "development"

    database_url: str = "postgresql+psycopg2://psx:psx@localhost:5432/psx_fertilizer"

    # Compliance gate — see docs/rights_matrix.template.md and docs/research_disclaimer.md
    public_launch_enabled: bool = False
    public_signals_enabled: bool = False
    commercial_data_enabled: bool = False

    # Data freshness / source policy
    data_delay_disclaimer: str = "Data is end-of-day / delayed public data, not a licensed real-time feed."

    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
