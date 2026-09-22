"""Application settings from environment. No secrets hardcoded."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "USGate Portal"
    app_secret_key: str = "dev-only-change-me-in-production-please-use-env"
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    app_base_url: str = "http://localhost:8080"
    # Single switch: true = in-memory mock panel; false = real 3X-UI adapter
    mock_xui: bool = True
    # When MOCK_XUI=false, allow falling back to mock on panel errors.
    # Default OFF so ops see structured failures.
    mock_xui_fallback: bool = False

    session_cookie_name: str = "usgate_session"
    session_https_only: bool = False
    session_max_age_seconds: int = 86400

    bootstrap_admin_user: str = "admin"
    bootstrap_admin_password: str = "changeme"

    xui_base_url: str = "http://VPS_IP:2053/PANEL_PATH"
    xui_username: str = "PANEL_ADMIN_USER"
    xui_password: str = "PANEL_ADMIN_PASSWORD"
    xui_api_token: str = ""
    xui_inbound_id: int = 1
    xui_sub_base_url: str = "http://VPS_IP:2096/SUB_PATH"

    login_rate_limit: int = 5
    login_rate_window_seconds: int = 60
    # Optional global request rate (0 = disabled)
    global_rate_limit: int = 120
    global_rate_window_seconds: int = 60

    database_url: str = "sqlite+aiosqlite:///./data/usgate.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
