from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Google Cloud Storage settings
    GCS_BUCKET: str
    
    BASE_URL: str = "/"
    SENSOR_URL: str = "http://localhost:8080"
    
    PORT: int = 8000
    
    ENV: str = "development"
    INFLUX_HOST: Optional[str] = None
    INFLUX_DB: Optional[str] = None
    INFLUX_TOKEN: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings() 