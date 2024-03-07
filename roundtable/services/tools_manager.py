from datetime import datetime

from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain_core.tools import tool, BaseTool
from langchain_experimental.tools import PythonREPLTool

from roundtable.shared.utils.logger import Logger


class ToolsManager:

    def __init__(self):
        self.logger = Logger()

    @staticmethod
    @tool
    def get_actual_date_tool(date_format: str = "%Y-%m-%d %H:%M:%S"):
        """
        Get the current time
        """
        return datetime.now().strftime(date_format)

    @staticmethod
    def get_code_executor_code() -> BaseTool:
        return PythonREPLTool()

    @staticmethod
    def get_web_search_tool() -> BaseTool:
        return DuckDuckGoSearchRun()
