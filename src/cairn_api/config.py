"""Runtime configuration, read from environment variables prefixed with ``CAIRN_``.

Infrastructure values (database URL, bucket names, hostnames) come from cairn-infra outputs and
reach the service as Fly secrets; nothing environment-specific is hard-coded here.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CAIRN_", env_file=".env", extra="ignore")

    environment: Literal["local", "test", "staging", "prod"] = "local"
    database_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
