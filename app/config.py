from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application configuration
    repo_url: str = "https://github.com/seriaati/image-host"
    api_key: str = Field(..., description="API key for authentication")
    filesize_limit: int = Field(default=20 * 1024 * 1024, description="Maximum file size in bytes")
    uploads_enabled: bool = Field(default=True, description="Whether uploading is enabled")

    # Storage configuration
    storage_type: str = Field(default="local", description="Storage type: 'local' or 's3'")
    s3_endpoint_url: str | None = Field(default=None, description="S3 endpoint URL")
    s3_access_key_id: str | None = Field(default=None, description="S3 access key ID")
    s3_secret_access_key: str | None = Field(default=None, description="S3 secret access key")
    s3_bucket_name: str | None = Field(default=None, description="S3 bucket name")
    s3_region: str = Field(default="auto", description="S3 region")
    s3_custom_domain: str | None = Field(default=None, description="Custom domain for S3 file URLs")


# Create a global settings instance
settings = Settings()  # pyright: ignore[reportCallIssue]
