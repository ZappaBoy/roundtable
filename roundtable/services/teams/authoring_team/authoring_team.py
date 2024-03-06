import functools
from typing import List

from langchain_core.messages import HumanMessage
from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from roundtable.services.agents.agents_manager import AgentsManager
from roundtable.services.teams.authoring_team.authoring_team_state import AuthoringTeamState
from roundtable.shared.utils.logger import Logger


class AuthoringTeam:

    def __init__(self, llm: ChatOpenAI | OllamaFunctions):
        self.logger = Logger()
        self.llm = llm
        self.authoring_chain = None

    def build_team(self):
        doc_writer_agent = AgentsManager.create_agent(
            self.llm,
            [AgentsManager.write_document, AgentsManager.edit_document, AgentsManager.read_document],
            "You are an expert writing a research document.\n"
            # The {current_files} value is populated automatically by the graph state
            "Below are files currently in your directory:\n{current_files}",
        )
        # Injects current directory working state before each call
        context_aware_doc_writer_agent = self.prelude | doc_writer_agent
        doc_writing_node = functools.partial(
            AgentsManager.agent_node, agent=context_aware_doc_writer_agent, name="Doc Writer"
        )

        note_taking_agent = AgentsManager.create_agent(
            self.llm,
            [AgentsManager.create_outline, AgentsManager.read_document],
            "You are an expert senior researcher tasked with writing a paper outline and"
            " taking notes to craft a perfect paper.{current_files}",
        )
        context_aware_note_taking_agent = self.prelude | note_taking_agent
        note_taking_node = functools.partial(
            AgentsManager.agent_node, agent=context_aware_note_taking_agent, name="Note Taker"
        )

        chart_generating_agent = AgentsManager.create_agent(
            self.llm,
            [AgentsManager.read_document, AgentsManager.create_code_executor_tool],
            "You are a data viz expert tasked with generating charts for a research project."
            "{current_files}",
        )
        context_aware_chart_generating_agent = self.prelude | chart_generating_agent
        chart_generating_node = functools.partial(
            AgentsManager.agent_node, agent=context_aware_note_taking_agent, name="Chart Generator"
        )

        doc_writing_supervisor = AgentsManager.create_team_supervisor(
            self.llm,
            "You are a supervisor tasked with managing a conversation between the"
            " following workers:  {team_members}. Given the following user request,"
            " respond with the worker to act next. Each worker will perform a"
            " task and respond with their results and status. When finished,"
            " respond with FINISH.",
            ["Doc Writer", "Note Taker", "Chart Generator"],
        )

        authoring_graph = StateGraph(AuthoringTeamState)
        authoring_graph.add_node("Doc Writer", doc_writing_node)
        authoring_graph.add_node("Note Taker", note_taking_node)
        authoring_graph.add_node("Chart Generator", chart_generating_node)
        authoring_graph.add_node("supervisor", doc_writing_supervisor)

        # Add the edges that always occur
        authoring_graph.add_edge("Doc Writer", "supervisor")
        authoring_graph.add_edge("Note Taker", "supervisor")
        authoring_graph.add_edge("Chart Generator", "supervisor")

        # Add the edges where routing applies
        authoring_graph.add_conditional_edges(
            "supervisor",
            lambda x: x["next"],
            {
                "Doc Writer": "Doc Writer",
                "Note Taker": "Note Taker",
                "Chart Generator": "Chart Generator",
                "FINISH": END,
            },
        )

        authoring_graph.set_entry_point("supervisor")
        # research_graph = ResearchTeam(self.llm_model).get_chain()
        # chain = research_graph.compile()

        self.authoring_chain = (
                functools.partial(self.enter_chain, members=authoring_graph.nodes)
                | authoring_graph.compile()
        )

    @staticmethod
    def prelude(state):
        return AgentsManager.load_files(state)

    def get_chain(self):
        if self.authoring_chain is None:
            self.build_team()
        return self.authoring_chain

    @staticmethod
    def enter_chain(message: str, members: List[str]):
        results = {
            "messages": [HumanMessage(content=message)],
            "team_members": ", ".join(members),
        }
        return results
