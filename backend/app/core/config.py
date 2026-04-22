"""Core configuration for Aqina Backend."""
import json
from typing import Any, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Firebase
    firebase_project_id: str = "aqina-chicken-essence"
    firebase_storage_bucket: str = "aqina-chicken-essence.firebasestorage.app"

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "https://aqina-frontend-*.a.run.app",
    ]

    # JWT (optional, for session tokens)
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 86400  # 24 hours in seconds

    # Environment
    environment: str = "development"

    # Meta / Messenger / WhatsApp
    meta_verify_token: str = ""
    meta_app_secret: str = ""
    meta_graph_api_version: str = "v22.0"
    meta_page_access_token: str = ""
    meta_page_id: str = ""
    meta_comment_reply_template: str = "__TODO__"
    meta_private_reply_template: str = "__TODO__"
    meta_whatsapp_access_token: str = ""
    meta_whatsapp_phone_number_id: str = ""

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3-flash-preview"
    gemini_system_prompt: str = "__TODO__"

    # CRM follow-up
    crm_follow_up_rules: str = json.dumps(
        {
            "t15m": {"delay_minutes": 15, "eligible_tags": ["engaged"], "instruction": "__TODO__"},
            "t3h": {"delay_minutes": 180, "eligible_tags": ["engaged"], "instruction": "__TODO__"},
            "t12h": {"delay_minutes": 720, "eligible_tags": ["engaged"], "instruction": "__TODO__"},
            "t23h": {"delay_minutes": 1380, "eligible_tags": ["engaged"], "instruction": "__TODO__"},
        }
    )

    # Internal task security
    internal_task_secret: str = ""
    backend_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:3000"

    # Cloud Tasks
    cloud_tasks_enabled: bool = False
    cloud_tasks_project_id: Optional[str] = None
    cloud_tasks_location: str = "asia-southeast1"
    cloud_tasks_events_queue: str = "marketing-events"
    cloud_tasks_followups_queue: str = "marketing-followups"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @staticmethod
    def is_placeholder(value: str | None) -> bool:
        """Return True when a config value is still an unconfigured placeholder."""
        if value is None:
            return True
        normalized = value.strip().lower()
        return normalized in {"", "todo", "__todo__", "__placeholder__", "tbd"}

    @property
    def crm_follow_up_rules_map(self) -> dict[str, dict[str, Any]]:
        """Parsed follow-up rules configuration."""
        try:
            raw = json.loads(self.crm_follow_up_rules or "{}")
        except json.JSONDecodeError:
            return {}

        if not isinstance(raw, dict):
            return {}
        return {str(key): value for key, value in raw.items() if isinstance(value, dict)}

    @property
    def gemini_ready(self) -> bool:
        """Whether Gemini is configured with a real API key."""
        return bool(self.gemini_api_key) and not self.is_placeholder(self.gemini_model)

    @property
    def follow_up_rules_ready(self) -> bool:
        """Whether every follow-up rule contains a non-placeholder instruction."""
        rules = self.crm_follow_up_rules_map
        if not rules:
            return False

        for rule in rules.values():
            instruction = str(rule.get("instruction", ""))
            if self.is_placeholder(instruction):
                return False
        return True

Settings.model_rebuild()
settings = Settings()
