import logging

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    DATABASE_URI: str = "sqlite:///./chinook_qa.db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_TEMPERATURE: float = 0.0
    GEMINI_MAX_TOKENS: int | None = None
    GEMINI_TIMEOUT: int | None = None
    GEMINI_MAX_RETRIES: int = 2

    OPENAI_API_KEY: str | None = None
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    OPENAI_EMBEDDING_DIMENSIONS: int = 1536

    CHAIN_TOP_K_RESULTS: int = 10
    CHAIN_ENABLE_STREAMING: bool = True
    CHAIN_ENABLE_APPROVAL: bool = False
    CHAIN_DEFAULT_THREAD_ID: str = "default"

    CHAIN_QUERY_TIMEOUT: int = 30
    CHAIN_MAX_QUERY_LENGTH: int = 1000
    CHAIN_ENABLE_QUERY_VALIDATION: bool = True

    AGENT_MAX_ITERATIONS: int = 10
    AGENT_ENABLE_STREAMING: bool = True
    AGENT_ENABLE_VECTOR_SEARCH: bool = False
    AGENT_TOP_K_RESULTS: int = 5

    AGENT_ENABLE_QUERY_CHECKER: bool = True
    AGENT_ENABLE_SCHEMA_TOOLS: bool = True
    AGENT_ENABLE_LIST_TABLES: bool = True

    VECTOR_SEARCH_K: int = 5
    VECTOR_SEARCH_SCORE_THRESHOLD: float = 0.7
    VECTOR_SEARCH_ENABLE_CACHING: bool = True

    ALLOWED_SQL_KEYWORDS: list[str] = [
        "SELECT", "FROM", "WHERE", "JOIN", "GROUP BY", "ORDER BY", "HAVING", "LIMIT"]
    FORBIDDEN_SQL_KEYWORDS: list[str] = [
        "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE", "REPLACE", "MERGE"]

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 30
    RATE_LIMIT_REQUESTS_PER_HOUR: int = 500

    APPROVAL_REQUIRED_FOR_KEYWORDS: list[str] = [
        "COUNT(*)", "DELETE", "UPDATE", "DROP"]
    APPROVAL_TIMEOUT: int = 300

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "logs/sql_qa.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024
    LOG_BACKUP_COUNT: int = 5

    API_V1_PREFIX: str = "/api/v1"
    API_TITLE: str = "LangChain SQL QA API"
    API_DESCRIPTION: str = "Complete SQL Question/Answering system following LangChain tutorial"
    API_VERSION: str = "1.0.0"

    CORS_ALLOW_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    ENABLE_CACHING: bool = True
    CACHE_TTL: int = 3600
    CACHE_MAX_SIZE: int = 1000

    MAX_CONCURRENT_REQUESTS: int = 10
    REQUEST_TIMEOUT: int = 60

    QUERY_RESULT_LIMIT: int = 1000
    ENABLE_QUERY_EXPLAIN: bool = False

    ENABLE_METRICS: bool = True
    METRICS_ENDPOINT: str = "/metrics"

    HEALTH_CHECK_INTERVAL: int = 60
    HEALTH_CHECK_TIMEOUT: int = 5

    DEBUG: bool = False
    RELOAD: bool = False

    TESTING: bool = False
    TEST_DATABASE_URI: str = "sqlite:///./test_chinook_qa.db"

    ENABLE_CHAIN_APPROACH: bool = True
    ENABLE_AGENT_APPROACH: bool = True
    ENABLE_COMPARISON_MODE: bool = True
    ENABLE_BATCH_PROCESSING: bool = True
    ENABLE_EXPORT_FUNCTIONALITY: bool = True

    ENABLE_EXPERIMENTAL_FEATURES: bool = False
    ENABLE_MULTI_DATABASE: bool = False
    ENABLE_CUSTOM_FUNCTIONS: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_settings()

    def _validate_settings(self):
        """Validate configuration settings"""

        if not self.GEMINI_API_KEY:
            logger.warning(
                "GEMINI_API_KEY not set. Some features may not work.")

        if self.AGENT_ENABLE_VECTOR_SEARCH and not self.OPENAI_API_KEY:
            logger.warning(
                "OPENAI_API_KEY not set. Vector search will be disabled.")
            self.AGENT_ENABLE_VECTOR_SEARCH = False

        if self.CHAIN_TOP_K_RESULTS <= 0:
            logger.warning(
                "CHAIN_TOP_K_RESULTS must be positive. Setting to 10.")
            self.CHAIN_TOP_K_RESULTS = 10

        if self.AGENT_MAX_ITERATIONS <= 0:
            logger.warning(
                "AGENT_MAX_ITERATIONS must be positive. Setting to 10.")
            self.AGENT_MAX_ITERATIONS = 10

        if self.RATE_LIMIT_REQUESTS_PER_MINUTE <= 0:
            logger.warning(
                "RATE_LIMIT_REQUESTS_PER_MINUTE must be positive. Setting to 30.")
            self.RATE_LIMIT_REQUESTS_PER_MINUTE = 30

    def get_database_url(self, testing: bool = False) -> str:
        """Get database URL for the given environment"""
        if testing or self.TESTING:
            return self.TEST_DATABASE_URI
        return self.DATABASE_URI

    def get_llm_config(self) -> dict:
        """Get LLM configuration dictionary"""
        return {
            "model": self.GEMINI_MODEL,
            "temperature": self.GEMINI_TEMPERATURE,
            "max_tokens": self.GEMINI_MAX_TOKENS,
            "timeout": self.GEMINI_TIMEOUT,
            "max_retries": self.GEMINI_MAX_RETRIES,
            "api_key": self.GEMINI_API_KEY
        }

    def get_agent_config(self) -> dict:
        """Get agent configuration dictionary"""
        return {
            "max_iterations": self.AGENT_MAX_ITERATIONS,
            "enable_streaming": self.AGENT_ENABLE_STREAMING,
            "enable_vector_search": self.AGENT_ENABLE_VECTOR_SEARCH,
            "top_k_results": self.AGENT_TOP_K_RESULTS,
            "enable_query_checker": self.AGENT_ENABLE_QUERY_CHECKER,
            "enable_schema_tools": self.AGENT_ENABLE_SCHEMA_TOOLS
        }

    def get_chain_config(self) -> dict:
        """Get chain configuration dictionary"""
        return {
            "top_k_results": self.CHAIN_TOP_K_RESULTS,
            "enable_streaming": self.CHAIN_ENABLE_STREAMING,
            "enable_approval": self.CHAIN_ENABLE_APPROVAL,
            "query_timeout": self.CHAIN_QUERY_TIMEOUT,
            "enable_query_validation": self.CHAIN_ENABLE_QUERY_VALIDATION
        }

    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.DEBUG or self.RELOAD

    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.is_development() and not self.TESTING


settings = Settings()


__all__ = ["settings", "Settings"]
