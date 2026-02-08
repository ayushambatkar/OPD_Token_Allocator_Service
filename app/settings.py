from enum import IntEnum
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./opd.db"
    no_show_timeout_minutes: int = 15
    allow_preemption: bool = True
    max_emergency_overflow: int = 2
    version: str = "1.0.1"

    class Config:
        env_file = ".env"


settings = Settings()
