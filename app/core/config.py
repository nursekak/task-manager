from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    PROJECT_NAME: str = "Task Manager API"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://taskmanager:taskmanager_secret@localhost:5432/taskmanager_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Rate limiting (requests per minute per user)
    RATE_LIMIT_PER_MINUTE: int = 60

    # Email (for notifications - mock/smtp)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@taskmanager.local"


settings = Settings()
