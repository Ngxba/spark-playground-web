from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/spark_playground"
    sqlalchemy_echo: bool = False
    secret_key: str = "your-secret-key-change-this-in-production-use-openssl-rand-hex-32"
    access_token_expire_minutes: int = 30

    # Spark Cluster
    spark_master_url: str = "spark://localhost:7077"
    spark_master_ui_url: str = "http://localhost:8080"
    spark_shuffle_partitions: int = 4
    spark_executor_cores: int = 2
    spark_driver_memory: str = "2g"
    spark_executor_memory: str = "2g"

    # Spark Event Logging
    spark_event_log_dir: Optional[str] = None
    spark_history_server_url: str = "http://localhost:18080"
    spark_active_ui_url: str = "http://localhost:4040"

    # MinIO (S3-compatible storage)
    minio_endpoint: Optional[str] = None
    minio_access_key: Optional[str] = None
    minio_secret_key: Optional[str] = None

    # PySpark JARs
    pyspark_jars_dir: str = "pyspark_jars"

    # Sankey Spec Generator
    sankey_bucket_count: int = 4
    sankey_skew_p95_median_ratio: float = 2.0
    sankey_skew_max_avg_ratio: float = 3.0
    sankey_link_max_width: int = 80


settings = Settings()
