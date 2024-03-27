from typing import List

from langroid import ToolMessage


class WebScraperTool(ToolMessage):
    request = "web_scraper_tool"
    purpose = "Extracts relevant to the <query> from a web search"
    query: str
    num_results: int = 3

    @classmethod
    def examples(cls) -> List["ToolMessage"]:
        return [
            cls(
                query="When was the Mistral LLM released?",
                num_results=3,
            ),
        ]

    @classmethod
    def instructions(cls) -> str:
        return """
        IMPORTANT: You must include an ACTUAL query in the `query` field,
        """
