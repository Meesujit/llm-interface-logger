from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/llm_logger"
    redis_url: str = "redis://localhost:6379"
    groq_api_key: str = ""
    gemini_api_key: str = ""
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_model: str = "gemini-2.0-flash"
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
