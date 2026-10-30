from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(
        "postgresql+psycopg://farmacias:farmacias@localhost:5433/farmacias",
        validation_alias="DATABASE_URL",
    )
    jwt_secret_key: str = Field("change-this-in-development", validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(480, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    max_failed_attempts: int = Field(5, validation_alias="MAX_FAILED_ATTEMPTS")
    lockout_minutes: int = Field(15, validation_alias="LOCKOUT_MINUTES")
    api_prefix: str = Field("/api/v1", validation_alias="API_PREFIX")
    frontend_origin: str = Field("http://localhost:5173", validation_alias="FRONTEND_ORIGIN")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
