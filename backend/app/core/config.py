from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    PROJECT_NAME: str = "NGO Impact Data Commons"

    DATABASE_URL: str = "sqlite:///./ngo_commons.db"

    JWT_SECRET: str = "ngo_super_secret_jwt_key_2026_production_grade"

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    GEMINI_API_KEY: str = ""

    # Email / SMTP Config
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()