from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:password@localhost:5432/spark_playground"
    sqlalchemy_echo: bool = False
    secret_key: str = "your-secret-key-change-this-in-production-use-openssl-rand-hex-32"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
