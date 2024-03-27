import langroid.utils.configuration as langroid_configuration

from roundtable.models.log_level import LogLevel
from roundtable.models.settings.environment import Environment
from roundtable.models.settings.settings import Settings
from roundtable.shared.decorators.singleton import Singleton


@Singleton
class Configurator:
    def __init__(self):
        self._settings = Settings()
        if self.is_debug_enabled():
            langroid_configuration.set_global(
                langroid_configuration.Settings(debug=True)
            )

    def get_project_name(self) -> str:
        return self._settings.title

    def is_production_environment(self) -> bool:
        return self._settings.environment == Environment.PRODUCTION

    def is_debug_enabled(self) -> bool:
        return self._settings.log_level == LogLevel.DEBUG

    def get_settings(self) -> Settings:
        return self._settings

    def get_llm_model(self) -> str:
        return self._settings.llm_model

    def get_llm_chat_length(self) -> int:
        return self._settings.llm_chat_length
