"""Application configuration loaded from environment variables."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application settings
    app_name: str = "Frame by Frame: Animation Idea Generator"
    environment: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    rate_limit_per_minute: int = 10

    # NVIDIA AI Provider Settings
    nvidia_api_key: Optional[str] = Field(default=None, alias="NVIDIA_API_KEY")
    nvidia_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1", alias="NVIDIA_BASE_URL"
    )
    nvidia_model: str = Field(
        default="meta/llama-3.1-70b-instruct", alias="NVIDIA_MODEL"
    )
    nvidia_timeout_seconds: float = Field(default=45.0, alias="NVIDIA_TIMEOUT_SECONDS")
    nvidia_max_retries: int = Field(default=2, alias="NVIDIA_MAX_RETRIES")

    @property
    def is_provider_configured(self) -> bool:
        """Checks if the NVIDIA API key is configured with a valid non-empty string."""
        return bool(
            self.nvidia_api_key
            and self.nvidia_api_key.strip()
            and not self.nvidia_api_key.startswith("your_nvidia_api_key")
        )


settings = Settings()
