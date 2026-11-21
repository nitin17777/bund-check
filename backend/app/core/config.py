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

    # Detection & ML Settings
    MAX_CHECK_WORD_COUNT: int = 50000
    SYNC_WORD_THRESHOLD: int = 1000
    CHECK_TIMEOUT_SECONDS: float = 60.0
    MODEL_ARTIFACT_PATH: str = "ml/models/artifacts/gbdt_calibrated_ensemble.joblib"
    MODEL_DEVICE: str = "cpu"  # "cpu" or "cuda"
    ENABLE_GPU: bool = False
    
    # Abstain band and word count thresholds
    ABSTAIN_LOWER_THRESHOLD: float = 0.40
    ABSTAIN_UPPER_THRESHOLD: float = 0.60
    MIN_WORD_COUNT_RELIABLE: int = 150
    MIN_WORD_COUNT_EVALUATE: int = 50

    # Verification Engine Settings
    SEMANTIC_SIMILARITY_THRESHOLD_PASS: float = 0.88
    SEMANTIC_SIMILARITY_THRESHOLD_REVIEW: float = 0.75
    NLI_CONTRADICTION_THRESHOLD: float = 0.10
    ENABLE_NLI_BY_DEFAULT: bool = False
    MAX_VERIFY_TEXT_LENGTH: int = 100000  # characters

    # Improver & LLM Provider Settings
    DEFAULT_IMPROVER_PROVIDER: str = "groq"  # "groq", "openrouter", "openai", "local_small"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "meta-llama/llama-3.3-70b-instruct"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    LOCAL_SMALL_MODEL: str = "Qwen/Qwen2.5-1.5B-Instruct"
    LOCAL_SMALL_DEVICE: str = "cpu"  # CPU safe, or quantized 4-bit if cuda
    IMPROVER_TIMEOUT_SECONDS: float = 45.0
    IMPROVER_MAX_RETRIES: int = 2
    MAX_IMPROVE_WORD_COUNT: int = 10000


settings = Settings()
