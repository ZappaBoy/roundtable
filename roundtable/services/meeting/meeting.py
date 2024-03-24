import langroid as lr
import langroid.language_models as lm

from roundtable.shared.utils.configurator import Configurator
from roundtable.shared.utils.logger import Logger


class Meeting:
    def __init__(self):
        self.logger = Logger()
        llm_model = Configurator.instance().get_llm_model()
        llm_config = lm.OpenAIGPTConfig(
            chat_model=llm_model,
            chat_context_length=16_000,
        )
        agent_config = lr.ChatAgentConfig(
            llm=llm_config,
            system_message="You are helpful but concise",
        )
        self.agent = lr.ChatAgent(agent_config)

    def build_team(self):
        pass

    def start_meeting(self):
        self.logger.info("Meeting started")
        self.build_team()
        try:
            task = lr.Task(self.agent, interactive=True)
            task.run()
        except Exception as e:
            self.logger.error(e)
            print('Sorry, something goes wrong. Try with a different input')

        self.end_meeting()

    def end_meeting(self):
        self.logger.info("Meeting ended")
