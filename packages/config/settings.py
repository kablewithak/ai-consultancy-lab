from __future__ import annotations

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SuperlinkedSettings(BaseSettings):
    """Runtime settings for the Superlinked inference provider.

    Secrets must come from environment variables or .env.
    They must never be committed, printed, or logged.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    sie_base_url: str = Field(..., description="Superlinked SIE base URL.")
    sie_api_key: SecretStr | None = Field(default=None, description="Superlinked API key.")
    sie_embedding_model: str = Field(default="BAAI/bge-m3")
    sie_timeout_s: float = Field(default=60.0, gt=0)

    @field_validator("sie_base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        if not normalized.startswith(("http://", "https://")):
            raise ValueError("SIE_BASE_URL must start with http:// or https://")
        return normalized

    @property
    def api_key_value(self) -> str | None:
        if self.sie_api_key is None:
            return None
        value = self.sie_api_key.get_secret_value().strip()
        return value or None
