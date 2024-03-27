from pydantic import BaseSettings, validator

from roundtable.models.log_level import LogLevel
from roundtable.models.settings.environment import Environment


class Settings(BaseSettings):
    title: str = "Roundtable"
    description: str = "This is a tool that simulates a roundtable discussion using AI agents."
    version: str = "0.1.0"
    environment: Environment = Environment.DEVELOPMENT
    log_level: LogLevel = LogLevel.DEBUG
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_api_key: str = "public_access"
    llm_model: str = "mistral:latest"
    code_model: str = "codellama:latest"

    class Config:
        env_file = ".env"

    @validator("log_level", pre=True)
    def parse_log_level(cls, value: str) -> LogLevel:
        return LogLevel.from_string(value)
