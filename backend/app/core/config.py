"""
Application configuration and environment settings.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Checkmate"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "mysql+pymysql://user:password@mysql:3306/checkmate"
    DB_ECHO: bool = False
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:8080"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/jpg"]
    UPLOAD_DIR: str = "app/static"
    
    # OCR
    OCR_SERVICE_URL: str = "http://ocr:8000"  # Legacy - for custom OCR service
    OCR_API_KEY: str = "K81156818088957"  # API key for OCR service (e.g., OCR.space, Google Vision)
    OCR_PROVIDER: str = "openai_vision"  # Options: "ocrspace", "google_vision", "naver_clova", "openai_vision", "tesseract"
    
    # Naver Clova OCR
    NAVER_CLOVA_API_URL: str = ""  # Naver Clova OCR API Gateway URL (e.g., https://xxxxx.apigw.ntruss.com)
    NAVER_CLOVA_SECRET_KEY: str = ""  # Naver Clova OCR Secret Key (X-OCR-SECRET)
    NAVER_CLOVA_TEMPLATE_IDS: str = ""  # Optional: Comma-separated template IDs for template-based OCR (e.g., "123,456")
    NAVER_CLOVA_AUTO_INTEGRATION: bool = False  # If True, use auto integration (JSON with base64), else use manual (multipart/form-data)
    
    # Exchange Rate
    FX_API_KEY: str = ""
    FX_BASE_CURRENCY: str = "KRW"
    
    # OpenAI (for category classification)
    OPENAI_API_KEY: str = ""  # OpenAI API key for expense category classification (set via .env file)
    OPENAI_API_URL: str = "https://api.openai.com/v1/chat/completions"  # OpenAI API endpoint
    OPENAI_MODEL: str = "gpt-3.5-turbo"  # OpenAI model to use (gpt-3.5-turbo, gpt-4, etc.)
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"  # Embedding model (text-embedding-3-small, text-embedding-ada-002)
    OPENAI_CLASSIFICATION_METHOD: str = "embeddings"  # Classification method: "chat" (Chat Completions) or "embeddings" (Embeddings API - recommended)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

