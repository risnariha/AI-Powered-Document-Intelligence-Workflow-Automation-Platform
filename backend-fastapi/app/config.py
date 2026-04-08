from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Document Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    DEBUG: bool = True
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")

    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    REQUEST_TIMEOUT: int = 60

    # Database
    DATABASE_URL: str = Field(default="postgresql://user:pass@localhost:5432/docintel")
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_CACHE_TTL: int = 3600  # 1 hour

    # Vector Store (Qdrant)
    QDRANT_HOST: str = Field(default="localhost")
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "documents"
    VECTOR_SIZE: int = 1536  # OpenAI embedding size

    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    ANTHROPIC_API_KEY: Optional[str] = None
    DEFAULT_LLM_PROVIDER: str = "openai"  # or "anthropic"

    # Local Models (fallback)
    LOCAL_EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    LOCAL_LLM_MODEL: str = "mistral-7b"  # For local inference

    # RAG Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RETRIEVAL: int = 5
    USE_HYBRID_SEARCH: bool = True
    RERANKING_ENABLED: bool = True

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_DOCUMENTS: str = "document-events"
    KAFKA_TOPIC_QUERIES: str = "query-events"
    KAFKA_CONSUMER_GROUP: str = "docintel-group"

    # Storage
    S3_BUCKET_NAME: str = "docintel-storage"
    S3_REGION: str = "us-east-1"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_DAY: int = 1000

    # Monitoring
    PROMETHEUS_PORT: int = 9090
    SENTRY_DSN: Optional[str] = None

    # Agent Configuration
    MAX_AGENT_ITERATIONS: int = 5
    AGENT_TIMEOUT_SECONDS: int = 30

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


settings = Settings()