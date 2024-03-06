from datetime import datetime

from langchain_core.tools import tool

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
