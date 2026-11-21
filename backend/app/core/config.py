"""
Application Configuration.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "BundCheck API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Document upload limits
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    MAX_UNCOMPRESSED_DOCX_BYTES: int = 50 * 1024 * 1024  # 50 MB
    MAX_ZIP_RATIO: float = 20.0
    MAX_ZIP_ENTRIES: int = 1000
    MAX_PDF_PAGES: int = 200


settings = Settings()
