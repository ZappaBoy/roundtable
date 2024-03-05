from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Annotated, Optional, Dict, Any

from langchain import hub
from langchain.agents import create_openai_tools_agent, AgentExecutor, create_react_agent
from langchain_community.chat_models import ChatOllama
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableSerializable
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from langchain_openai import ChatOpenAI

from roundtable.shared.utils.logger import Logger

RESEARCHER_MAX_RESULT = 5
_TEMP_DIRECTORY = TemporaryDirectory()
WORKING_DIRECTORY = Path(_TEMP_DIRECTORY.name)


class AgentsManager:

    def __init__(self):
        self.logger = Logger()

    @staticmethod
    def create_agent(llm: ChatOpenAI | ChatOllama, tools: List, system_prompt: str):
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
        if isinstance(llm, ChatOpenAI):
            agent = create_openai_tools_agent(llm, tools, prompt)
        else:
            # prompt.tool = [t.name for t in tools]
            # prompt['tool'] = tools
            prompt = hub.pull("hwchase17/react")
            agent = create_react_agent(llm, tools, prompt)
        executor = AgentExecutor(agent=agent, tools=tools)
        return executor

    @staticmethod
    def agent_node(state, agent, name):
        result = agent.invoke(state)
        return {"messages": [HumanMessage(content=result["output"], name=name)]}

    @staticmethod
    def create_team_supervisor(llm: ChatOpenAI | ChatOllama, system_prompt, members) -> RunnableSerializable[dict, Any]:
        options = ["FINISH"] + members
        function_def = {
            "name": "route",
            "description": "Select the next role.",
            "parameters": {
                "title": "routeSchema",
                "type": "object",
                "properties": {
                    "next": {
                        "title": "Next",
                        "anyOf": [
                            {"enum": options},
                        ],
                    },
                },
                "required": ["next"],
            },
        }
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="messages"),
                (
                    "system",
                    "Given the conversation above, who should act next?"
                    " Or should we FINISH? Select one of: {options}",
                ),
            ]
        ).partial(options=str(options), team_members=", ".join(members))
        return (
                prompt
                | llm.bind(functions=[function_def], function_call="route")
                | JsonOutputFunctionsParser()
        )

    @staticmethod
    def create_researcher_tool(researcher_max_results: int = RESEARCHER_MAX_RESULT) -> TavilySearchResults:
        researcher_tool = TavilySearchResults(max_results=researcher_max_results)
        return researcher_tool

    @staticmethod
    @tool
    def create_code_executor_tool(
            code: Annotated[str, "The python code to execute to generate your chart."]
    ):
        """Use this to execute python code. If you want to see the output of a value,
        you should print it out with `print(...)`. This is visible to the user."""
        try:
            repl = PythonREPL()
            result = repl.run(code)
        except BaseException as e:
            return f"Failed to execute. Error: {repr(e)}"
        return f"Succesfully executed:\n```python\n{code}\n```\nStdout: {result}"

    @staticmethod
    @tool
    def create_webscraper_tool(urls: List[str]) -> str:
        """Use requests and bs4 to scrape the provided web pages for detailed information."""
        loader = WebBaseLoader(urls)
        docs = loader.load()
        return "\n\n".join(
            [
                f'<Document name="{doc.metadata.get("title", "")}">\n{doc.page_content}\n</Document>'
                for doc in docs
            ]
        )

    @staticmethod
    @tool
    def create_outline(
            points: Annotated[List[str], "List of main points or sections."],
            file_name: Annotated[str, "File path to save the outline."],
    ) -> Annotated[str, "Path of the saved outline file."]:
        """Create and save an outline."""
        with (WORKING_DIRECTORY / file_name).open("w") as file:
            for i, point in enumerate(points):
                file.write(f"{i + 1}. {point}\n")
        return f"Outline saved to {file_name}"

    @staticmethod
    @tool
    def read_document(
            file_name: Annotated[str, "File path to save the document."],
            start: Annotated[Optional[int], "The start line. Default is 0"] = None,
            end: Annotated[Optional[int], "The end line. Default is None"] = None,
    ) -> str:
        """Read the specified document."""
        with (WORKING_DIRECTORY / file_name).open("r") as file:
            lines = file.readlines()
        if start is not None:
            start = 0
        return "\n".join(lines[start:end])

    @staticmethod
    @tool
    def write_document(
            content: Annotated[str, "Text content to be written into the document."],
            file_name: Annotated[str, "File path to save the document."],
    ) -> Annotated[str, "Path of the saved document file."]:
        """Create and save a text document."""
        with (WORKING_DIRECTORY / file_name).open("w") as file:
            file.write(content)
        return f"Document saved to {file_name}"

    @staticmethod
    @tool
    def edit_document(
            file_name: Annotated[str, "Path of the document to be edited."],
            inserts: Annotated[
                Dict[int, str],
                "Dictionary where key is the line number (1-indexed) and value is the text to be inserted at that line.",
            ],
    ) -> Annotated[str, "Path of the edited document file."]:
        """Edit a document by inserting text at specific line numbers."""

        with (WORKING_DIRECTORY / file_name).open("r") as file:
            lines = file.readlines()

        sorted_inserts = sorted(inserts.items())

        for line_number, text in sorted_inserts:
            if 1 <= line_number <= len(lines) + 1:
                lines.insert(line_number - 1, text + "\n")
            else:
                return f"Error: Line number {line_number} is out of range."

        with (WORKING_DIRECTORY / file_name).open("w") as file:
            file.writelines(lines)

        return f"Document edited and saved to {file_name}"

    @staticmethod
    def load_files(state):
        written_files = []
        if not WORKING_DIRECTORY.exists():
            WORKING_DIRECTORY.mkdir()
        try:
            written_files = [
                f.relative_to(WORKING_DIRECTORY) for f in WORKING_DIRECTORY.rglob("*")
            ]
        except:
            pass
        if not written_files:
            return {**state, "current_files": "No files written."}
        return {
            **state,
            "current_files": "\nBelow are files your team has written to the directory:\n"
                             + "\n".join([f" - {f}" for f in written_files]),
        }
