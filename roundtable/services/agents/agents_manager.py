from typing import List

from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_community.chat_models import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_experimental.tools import PythonREPLTool

from roundtable.shared.utils.logger import Logger


class AgentsManager:
    def __init__(self):
        self.logger = Logger()
        self.researcher_max_results = 5

    @staticmethod
    def create_agent(llm: ChatOpenAI, tools: List, system_prompt: str):
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    system_prompt,
                ),
                MessagesPlaceholder(variable_name="messages"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        agent = create_openai_tools_agent(llm, tools, prompt)
        executor = AgentExecutor(agent=agent, tools=tools)
        return executor

    def create_researcher_tool(self) -> TavilySearchResults:
        researcher_tool = TavilySearchResults(max_results=self.researcher_max_results)
        return researcher_tool

    @staticmethod
    def create_code_executor_tool() -> PythonREPLTool:
        code_executor_tool = PythonREPLTool()
        return code_executor_tool
