from typing import Sequence, TypedDict

from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langchain_experimental.llms.ollama_functions import OllamaFunctions

from roundtable.shared.utils.logger import Logger


class AgentsManager:

    def __init__(self):
        self.logger = Logger()

    @staticmethod
    def create_agent(llm: OllamaFunctions, tools: Sequence[BaseTool], system_prompt: str) \
            -> AgentExecutor:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    system_prompt,
                ),
                MessagesPlaceholder(variable_name="messages"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
                MessagesPlaceholder(variable_name="tools"),
                MessagesPlaceholder(variable_name="tool_names"),
            ]
        )
        # prompt.input_variables.append("tools")
        # prompt.input_variables.append("tool_names")

        agent = create_react_agent(llm, tools, prompt)
        executor = AgentExecutor(agent=agent, tools=tools)
        return executor

    @staticmethod
    def agent_node(state: TypedDict, agent: Runnable, name: str):
        result = agent.invoke(state)
        return {"messages": [HumanMessage(content=result["output"], name=name)]}
