from typing import List

from langroid import ChatAgent, Task, ChatAgentConfig
from langroid.agent.tools import RecipientTool
from langroid.language_models import OpenAIGPTConfig

from roundtable.shared.utils.configurator import Configurator
from roundtable.shared.utils.logger import Logger


class AgentManager:
    default_llm_model = Configurator.instance().get_llm_model()
    default_chat_context_length = Configurator.instance().get_llm_chat_length()

    def __init__(self):
        self.logger = Logger()

    @staticmethod
    def create_agent(llm_model: str = default_llm_model,
                     chat_context_length: int = default_chat_context_length,
                     use_tools: bool = True
                     ) -> ChatAgent:
        llm_config = OpenAIGPTConfig(
            chat_model=llm_model,
            chat_context_length=chat_context_length,
        )

        config = ChatAgentConfig(
            llm=llm_config,
            use_tools=use_tools,
            use_functions_api=not use_tools,
            vecdb=None,
        )

        return ChatAgent(config)

    @staticmethod
    def create_task(
            agent_name: str,
            system_message: str,
            user_message: str = "Can you help me with some questions?",
            is_supervisor: bool = False,
            agent: ChatAgent = None,
            interactive: bool = True,
            tools: List = None,
    ) -> Task:
        if agent is None:
            agent = AgentManager.create_agent()
        if is_supervisor:
            agent.enable_message(RecipientTool)

        if tools is not None:
            for tool in tools:
                agent.enable_message(tool)

        task = Task(
            agent,
            name=agent_name,
            interactive=interactive,
            system_message=system_message,
            llm_delegate=is_supervisor,
            single_round=not is_supervisor,
            user_message=user_message,
        )

        return task

    @staticmethod
    def create_team(supervisor_task: Task, subordinate_tasks: List[Task]) -> Task:
        supervisor_task.add_sub_task(subordinate_tasks)
        return supervisor_task
