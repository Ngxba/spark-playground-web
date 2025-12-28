from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:password@localhost:5432/spark_playground"
    sqlalchemy_echo: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
