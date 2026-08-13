from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app configuration, including the non-negotiable compliance gate flags.

    PUBLIC_LAUNCH_ENABLED, PUBLIC_SIGNALS_ENABLED, COMMERCIAL_DATA_ENABLED and
    ML_SIGNALS_ENABLED must stay False until PSX data-licensing and SECP research-regulation
    review has actually been completed and documented (see docs/rights_matrix.template.md).
    Do not flip these defaults in code — override via environment/.env only,
    and only after that review exists.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "PSX Fertilizer Research Platform"
    environment: str = "development"

    database_url: str = "postgresql+psycopg2://psx:psx@localhost:55432/psx_fertilizer"

    # Compliance gate — see docs/rights_matrix.template.md and docs/research_disclaimer.md
    public_launch_enabled: bool = False
    public_signals_enabled: bool = False
    commercial_data_enabled: bool = False
    ml_signals_enabled: bool = False

    # Data freshness / source policy
    data_delay_disclaimer: str = "Data is end-of-day / delayed public data, not a licensed real-time feed."

    cors_origins: list[str] = ["http://localhost:3000"]

    # SBP EasyData API (https://easydata.sbp.org.pk) — free account + generated key required.
    # Macro ingestion (app/ingestion/sbp_macro.py) no-ops with a warning when unset.
    sbp_easydata_api_key: str | None = None
    sbp_easydata_base_url: str = "https://easydata.sbp.org.pk/api/v1"

    # Anthropic API key for the PSX Senior Analyst Agent (LLM synthesis node).
    # When unset, the analyst endpoint returns all deterministic data (forensics, CAPM,
    # factor model) but skips the LLM synthesis step with synthesis_status="requires_api_key".
    # Obtain a key at https://console.anthropic.com.
    anthropic_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
