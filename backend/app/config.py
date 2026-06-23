from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://matchsnapper:matchsnapper@localhost:5432/matchsnapper"
    secret_key: str = "changeme"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    storage_backend: str = "minio"
    aws_access_key_id: str = "minioadmin"
    aws_secret_access_key: str = "minioadmin"
    aws_endpoint_url: str | None = "http://localhost:9000"
    aws_bucket_name: str = "matchsnapper"
    aws_region: str = "us-east-1"


settings = Settings()
