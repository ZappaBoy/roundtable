import functools
import operator
from datetime import datetime
from textwrap import dedent
from typing import Sequence, TypedDict, Annotated

from langchain.agents import create_react_agent, AgentExecutor
from langchain_community.output_parsers.ernie_functions import JsonOutputFunctionsParser
from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool, tool
from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langchain_experimental.tools import PythonREPLTool
from langgraph.graph import END, StateGraph

SUPERVISOR = 'Supervisor'
RESEARCHER = 'Researcher'
CODER = 'Coder'
FINISH = 'FINISH'
members = [RESEARCHER, CODER]


class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str


def create_agent(llm: OllamaFunctions, tools: Sequence[BaseTool], system_prompt: str) \
        -> Runnable:
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

    return create_react_agent(llm, tools, prompt)


def create_agent_executor(llm: OllamaFunctions, tools: Sequence[BaseTool],
                          system_prompt: str) -> AgentExecutor:
    agent = create_agent(llm, tools, system_prompt)
    executor = AgentExecutor(agent=agent, tools=tools)
    return executor


def agent_node(state: TypedDict, agent: Runnable, name: str):
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=result["output"], name=name)]}


@tool
def get_actual_date_tool(date_format: str = "%Y-%m-%d %H:%M:%S"):
    """
    Get the current time
    """
    return datetime.now().strftime(date_format)


def get_code_executor_code() -> BaseTool:
    return PythonREPLTool()


def get_web_search_tool() -> BaseTool:
    return DuckDuckGoSearchRun()


llm = OllamaFunctions(model="openhermes")

options = [FINISH] + members

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
            }
        },
        "required": ["next"],
    },
}
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            dedent("""
                You are a supervisor tasked with managing a conversation between the following workers: 
                {members}. Given the following user request, respond with the worker to act next. Each worker 
                will perform a task and respond with their results and status. When finished, respond with 
                FINISH.
            """)
        ),
        MessagesPlaceholder(variable_name="messages"),
        (
            "system",
            dedent("""
                Given the conversation above, who should act next? Or should we FINISH? Select one of: {options}
            """)
        ),
    ]
).partial(options=str(options), members=", ".join(members))

supervisor_chain = (
        prompt
        | llm.bind(functions=[function_def], function_call={"name": "route"})
        | JsonOutputFunctionsParser()
)

research_agent = create_agent_executor(
    llm,
    [get_web_search_tool()],
    "You are a web researcher."
)
research_node = functools.partial(agent_node, agent=research_agent, name=RESEARCHER)

code_agent = create_agent_executor(
    llm,
    [get_code_executor_code()],
    "You may generate safe python code to analyze data and generate charts using matplotlib.",
)
code_node = functools.partial(agent_node, agent=code_agent, name=CODER)

workflow_graph = StateGraph(GraphState)
workflow_graph.add_node(RESEARCHER, research_node)
workflow_graph.add_node(CODER, code_node)
workflow_graph.add_node(SUPERVISOR, supervisor_chain)

for member in members:
    # We want our workers to ALWAYS "report back" to the supervisor when done
    workflow_graph.add_edge(member, SUPERVISOR)
# The supervisor populates the "next" field in the graph state
# which routes to a node or finishes
conditional_map = {k: k for k in members}
conditional_map[FINISH] = END
workflow_graph.add_conditional_edges(SUPERVISOR, lambda x: x["next"], conditional_map)
# Finally, add entrypoint
workflow_graph.set_entry_point(SUPERVISOR)

chain = workflow_graph.compile()

running = True
while running:
    user_input = input("Enter text (press 'q' or ctrl-c to quit): ")
    if user_input.lower() == 'q':
        running = False
    try:
        inputs = {
            "messages": [
                HumanMessage(content=user_input)
            ]
        }
        for s in chain.stream(inputs, {"recursion_limit": 100}, ):
            if "__end__" not in s:
                print("---")
                result = list(s.values())[0]
                print(result)
    except Exception as e:
        print(e)
        print('Sorry, something goes wrong. Try with a different input')
