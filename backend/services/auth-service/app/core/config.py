from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str="postgresql://auth_user:auth_pass@localhost:5432/auth_db"
    JWT_SECRET: str = "super-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

settings = Settings()
