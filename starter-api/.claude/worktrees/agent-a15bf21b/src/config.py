from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # Database
    database_url: str

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str

    # CORS — stored as comma-separated string to avoid pydantic-settings JSON parsing
    cors_origins: str = "http://localhost:3000"

    # Database schema
    db_schema: str = "public"

    # Rate limiting
    rate_limit_per_minute: int = 60

    # Observability
    sentry_dsn: str = ""
    axiom_token: str = ""
    axiom_dataset: str = "starter-api"
    otel_service_name: str = "starter-api"

    # Cache (Upstash Redis)
    redis_url: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
