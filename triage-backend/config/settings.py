"""
Centralized application settings via Pydantic Settings.
All configuration is driven by environment variables with sensible defaults.
"""

from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Model ────────────────────────────────────────────
    hf_token: str = ""
    base_model: str = "mistralai/Mistral-7B-Instruct-v0.3"
    hf_repo_id: str = "triage-team/triage-hospital-agent"
    mock_llm: bool = True

    # ── Database ─────────────────────────────────────────
    database_url: str = f"sqlite+aiosqlite:///{ROOT_DIR / 'triage.db'}"

    # ── Redis ────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379"
    use_redis: bool = False

    # ── API ──────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # ── Simulation ───────────────────────────────────────
    max_steps_per_episode: int = 500
    schema_drift_enabled: bool = True
    expert_mode: bool = False

    # ── Logging ──────────────────────────────────────────
    log_level: str = "INFO"

    # ── Derived ──────────────────────────────────────────
    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def agents_yaml_path(self) -> Path:
        return ROOT_DIR / "config" / "agents.yaml"
