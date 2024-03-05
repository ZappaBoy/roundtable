from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from roundtable.services.agents.agents_manager import AgentsManager
from roundtable.services.meeting.meeting_state import MeetingState
from roundtable.services.teams.authoring_team.authoring_team import AuthoringTeam
from roundtable.services.teams.research_team.research_team import ResearchTeam
from roundtable.shared.utils.configurator import Configurator
from roundtable.shared.utils.logger import Logger


class Meeting:
    def __init__(self):
        self.logger = Logger()
        llm_model = Configurator.instance().get_llm_model()
        self.is_openai_api_key_set = Configurator.instance().is_openai_api_key_set()
        if self.is_openai_api_key_set:
            self.llm = ChatOpenAI(model=llm_model)
        else:
            self.llm = ChatOllama(model=llm_model)
        self.super_graph = None
        self.research_team = ResearchTeam(self.llm)
        self.authoring_team = AuthoringTeam(self.llm)

    def build_meeting(self):
        supervisor_node = AgentsManager.create_team_supervisor(
            self.llm,
            "You are a supervisor tasked with managing a conversation between the"
            " following teams: {team_members}. Given the following user request,"
            " respond with the worker to act next. Each worker will perform a"
            " task and respond with their results and status. When finished,"
            " respond with FINISH.",
            ["Research team", "Paper writing team"],
        )

        research_chain = self.research_team.get_chain()
        authoring_chain = self.authoring_team.get_chain()

        super_graph = StateGraph(MeetingState)
        # First add the nodes, which will do the work
        super_graph.add_node("Research team", self.get_last_message | research_chain | self.join_graph)
        super_graph.add_node(
            "Paper writing team", self.get_last_message | authoring_chain | self.join_graph
        )
        super_graph.add_node("supervisor", supervisor_node)

        # Define the graph connections, which controls how the logic
        # propagates through the program
        super_graph.add_edge("Research team", "supervisor")
        super_graph.add_edge("Paper writing team", "supervisor")
        super_graph.add_conditional_edges(
            "supervisor",
            lambda x: x["next"],
            {
                "Paper writing team": "Paper writing team",
                "Research team": "Research team",
                "FINISH": END,
            },
        )
        super_graph.set_entry_point("supervisor")
        self.super_graph = super_graph.compile()

    def start_meeting(self):
        self.logger.info("Meeting started")
        self.build_meeting()
        running = True
        while running:
            user_input = input("Enter text (press 'q' or ctrl-c to quit): ")
            if user_input.lower() == 'q':
                running = False
            # print(f"> {user_input}")
            for s in self.super_graph.stream(
                    {
                        "messages": [
                            HumanMessage(
                                content=user_input
                            )
                        ],
                    },
                    {"recursion_limit": 150},
            ):
                if "__end__" not in s:
                    print(s)
                    print("---")
        self.end_meeting()

    def end_meeting(self):
        self.logger.info("Meeting ended")

    def save_report(self):
        self.logger.info("Report saved")
        pass

    @staticmethod
    def get_last_message(state: MeetingState) -> str:
        return state["messages"][-1].content

    @staticmethod
    def join_graph(response: dict):
        return {"messages": [response["messages"][-1]]}
