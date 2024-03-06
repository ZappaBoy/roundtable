from langchain.globals import set_debug, set_verbose

from roundtable.models.log_level import LogLevel
from roundtable.models.settings.environment import Environment
from roundtable.models.settings.settings import Settings
from roundtable.shared.decorators.singleton import Singleton


@Singleton
class Configurator:
    def __init__(self):
        self._settings = Settings()
        if self._settings.environment == Environment.TESTING:
            self._settings.log_level = LogLevel.DEBUG

    def is_production_environment(self) -> bool:
        return self._settings.environment == Environment.PRODUCTION

    def is_debug_enabled(self) -> bool:
        set_debug(True)
        set_verbose(True)
        return self._settings.log_level == LogLevel.DEBUG

    def get_settings(self) -> Settings:
        return self._settings

    def get_llm_model(self) -> str:
        return self._settings.llm_model
