import functools
import traceback
from textwrap import dedent

from langchain_community.output_parsers.ernie_functions import JsonOutputFunctionsParser
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langgraph.graph import END, StateGraph

from roundtable.services.agents_manager import AgentsManager
from roundtable.services.meeting.meeting_state import MeetingState
from roundtable.services.tools_manager import ToolsManager
from roundtable.shared.utils.configurator import Configurator
from roundtable.shared.utils.logger import Logger

SUPERVISOR = 'Supervisor'
RESEARCHER = 'Researcher'
CODER = 'Coder'
FINISH = 'FINISH'


class Meeting:

    def __init__(self):
        self.logger = Logger()
        llm_model = Configurator.instance().get_llm_model()
        self.llm = OllamaFunctions(model=llm_model)
        self.meeting_chain = None
        self.tool_executor = None
        self.agent_runnable = None

    def build_team(self):
        members = [RESEARCHER, CODER]
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
                | self.llm.bind_functions(functions=[function_def], function_call="route")
                | JsonOutputFunctionsParser()
        )

        research_agent = AgentsManager.create_agent(
            self.llm,
            [ToolsManager.get_web_search_tool()],
            "You are a web researcher."
        )
        research_node = functools.partial(AgentsManager.agent_node, agent=research_agent, name=RESEARCHER)

        code_agent = AgentsManager.create_agent(
            self.llm,
            [ToolsManager.get_code_executor_code()],
            "You may generate safe python code to analyze data and generate charts using matplotlib.",
        )
        code_node = functools.partial(AgentsManager.agent_node, agent=code_agent, name=CODER)

        workflow_graph = StateGraph(MeetingState)
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

        self.meeting_chain = workflow_graph.compile()

    def start_meeting(self):
        self.logger.info("Meeting started")
        self.build_team()
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
                for s in self.meeting_chain.stream(inputs, {"recursion_limit": 100}, ):
                    if "__end__" not in s:
                        print("---")
                        result = list(s.values())[0]
                        print(result)
            except Exception as e:
                self.logger.error(e)
                traceback.print_exc()
                print('Sorry, something goes wrong. Try with a different input')

        self.end_meeting()

    def end_meeting(self):
        self.logger.info("Meeting ended")

    def get_chain(self):
        if self.meeting_chain is None:
            self.build_team()
        return self.meeting_chain
