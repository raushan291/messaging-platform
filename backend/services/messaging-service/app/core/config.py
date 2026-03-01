from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    # ELASTICSEARCH_URL: str = "http://elasticsearch:9200"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    # KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    DATABASE_URL: str = "postgresql://auth_user:auth_pass@localhost:5432/messaging_db"
    # DATABASE_URL: str = "postgresql://auth_user:auth_pass@postgres:5432/messaging_db"
    JWT_SECRET: str = "super-secret-key"
    JWT_ALGORITHM: str = "HS256"
    REDIS_URL: str = "redis://localhost:6379"
    # REDIS_URL: str = "redis://redis:6379"
    MESSAGE_RATE_LIMIT: int = 5
    MESSAGE_RATE_WINDOW: int = 10
    MAX_MESSAGE_LENGTH: int = 2000 # characters
    MAX_CONNECTIONS_PER_USER: int = 3
    MAX_CONVERSATION_PARTICIPANTS: int = 1000
    CREATE_CONVERSATION_LIMIT: int = 10   # per minute
    CREATE_CONVERSATION_WINDOW: int = 60
    GET_CONVERSATION_LIMIT: int = 30 
    GET_CONVERSATION_WINDOW: int = 60
    UPDATE_CONVERSATION_LIMIT: int = 10 
    UPDATE_CONVERSATION_WINDOW: int = 60
    DELETE_CONVERSATION_LIMIT: int = 10 
    DELETE_CONVERSATION_WINDOW: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
