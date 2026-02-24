from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    DATABASE_URL: str = "postgresql://auth_user:auth_pass@localhost:5432/messaging_db"
    JWT_SECRET: str = "super-secret-key"
    JWT_ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"


settings = Settings()
