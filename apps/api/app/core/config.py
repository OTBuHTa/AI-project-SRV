from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "AI-project SRV"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://aisrv:aisrv@postgres:5432/aisrv"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = "change-me-before-external-access"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 14
    bootstrap_enabled: bool = True
    llm_base_url: str = "http://host.docker.internal:11434/v1"
    llm_model: str = "qwen2.5:7b"
    llm_api_key: str = ""
    llm_timeout_seconds: float = 90.0
    backup_alert_webhook_url: str = ""
    backup_alert_webhook_timeout_seconds: float = 10.0
    notification_webhook_allow_private_networks: bool = False
    notification_webhook_signing_secret: str = ""
    metrics_bearer_token: str = ""
    secure_headers_hsts_enabled: bool = False
    auth_rate_limit_enabled: bool = False
    auth_rate_limit_window_seconds: int = 300
    auth_rate_limit_ip_attempts: int = 20
    auth_rate_limit_account_attempts: int = 10
    forwarded_allow_ips: str = "127.0.0.1"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
