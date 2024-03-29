from roundtable.models.discussion_room_config import DiscussionRoomConfig
from roundtable.models.log_level import LogLevel
from roundtable.models.settings.environment import Environment
from roundtable.models.settings.settings import Settings
from roundtable.shared.decorators.singleton import Singleton


@Singleton
class Configurator:
    def __init__(self):
        self._settings = Settings()
        if self.is_debug_enabled():
            print("Debug enabled")

    def get_project_name(self) -> str:
        return self._settings.title

    def is_production_environment(self) -> bool:
        return self._settings.environment == Environment.PRODUCTION

    def is_debug_enabled(self) -> bool:
        return self._settings.log_level == LogLevel.DEBUG

    def get_settings(self) -> Settings:
        return self._settings

    def get_discussion_room_config(self) -> DiscussionRoomConfig:
        return DiscussionRoomConfig(
            base_url=self._settings.ollama_base_url,
            api_key=self._settings.ollama_api_key,
            llm_model_name=self._settings.llm_model,
            code_model_name=self._settings.code_model,
            use_code_execution=self._settings.code_execution,
            execute_code_in_docker=self._settings.docker_code_execution,
        )
