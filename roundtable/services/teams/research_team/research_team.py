import functools

from langchain_core.messages import HumanMessage
from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from roundtable.services.agents.agents_manager import AgentsManager
from roundtable.services.teams.research_team.research_team_state import ResearchTeamState
from roundtable.shared.utils.logger import Logger


class ResearchTeam:
    def __init__(self, llm: ChatOpenAI | OllamaFunctions):
        self.logger = Logger()
        self.llm = llm
        self.research_chain = None

    def build_team(self):
        search_agent = AgentsManager.create_agent(
            self.llm,
            [AgentsManager.create_researcher_tool],
            "You are a research assistant who can search for up-to-date info using the DuckDuckGo search engine.",
        )
        search_node = functools.partial(AgentsManager.agent_node, agent=search_agent, name="Search")

        research_agent = AgentsManager.create_agent(
            self.llm,
            [AgentsManager.create_webscraper_tool],
            "You are a research assistant who can scrape specified urls for more detailed information using the scrape_webpages function.",
        )
        research_node = functools.partial(AgentsManager.agent_node, agent=research_agent, name="Web Scraper")

        supervisor_agent = AgentsManager.create_team_supervisor(
            self.llm,
            "You are a supervisor tasked with managing a conversation between the"
            " following workers:  Search, Web Scraper. Given the following user request,"
            " respond with the worker to act next. Each worker will perform a"
            " task and respond with their results and status. When finished,"
            " respond with FINISH.",
            ["Search", "Web Scraper"],
        )

        research_graph = StateGraph(ResearchTeamState)
        research_graph.add_node("Search", search_node)
        research_graph.add_node("Web Scraper", research_node)
        research_graph.add_node("supervisor", supervisor_agent)

        # Define the control flow
        research_graph.add_edge("Search", "supervisor")
        research_graph.add_edge("Web Scraper", "supervisor")
        research_graph.add_conditional_edges(
            "supervisor",
            lambda x: x["next"],
            {"Search": "Search", "Web Scraper": "Web Scraper", "FINISH": END},
        )

        research_graph.set_entry_point("supervisor")
        chain = research_graph.compile()

        self.research_chain = self.enter_chain | chain

    def get_chain(self):
        if self.research_chain is None:
            self.build_team()
        return self.research_chain

    @staticmethod
    def enter_chain(message: str):
        results = {
            "messages": [HumanMessage(content=message)],
        }
        return results
