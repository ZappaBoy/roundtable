from pydantic.v1 import BaseSettings

from roundtable.models.log_level import LogLevel
from roundtable.models.settings.environment import Environment


class Settings(BaseSettings):
    title: str = "Roundtable"
    description: str = "This is a tool that simulates a roundtable discussion using AI agents."
    version: str = "0.1.0"
    environment: Environment = Environment.DEVELOPMENT
    log_level: LogLevel = LogLevel.DEBUG

    class Config:
        env_file = ".env"
