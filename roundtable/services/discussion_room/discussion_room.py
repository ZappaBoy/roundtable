from langroid import Task
from langroid.agent.tools import GoogleSearchTool

from roundtable.services.agent_manager.agent_manager import AgentManager
from roundtable.services.tools.web_scraper_tool import WebScraperTool
from roundtable.shared.utils.logger import Logger

RESEARCHER = "Researcher"
WEB_SCRAPER = "Web Scraper"
CODER = "Coder"
DATA_ANALYST = "Data Analyst"

RESEARCH_TEAM = "Research Team"
CODING_TEAM = "Coding Team"
TEAMS = [RESEARCH_TEAM, CODING_TEAM]


class DiscussionRoom:
    def __init__(self, interactive: bool = True):
        self.logger = Logger()
        self.interactive = interactive
        self.discussion: Task | None = None

    def build_discussion_room(self):

        search_tool_handler_method = GoogleSearchTool.default_value("request")

        researcher_subordinate = AgentManager.create_task(
            agent_name=RESEARCHER,
            system_message=f"""
                You are a member of the {RESEARCH_TEAM}.
                You are a helpful assistant. You will try your best to answer my questions.
                Here is how you should answer my questions:
                - IF my question is about a topic you ARE CERTAIN about, answer it directly
                - OTHERWISE, use the `{search_tool_handler_method}` tool/function-call to
                  get up to 5 results from a web-search, to help you answer the question.
                  I will show you the results from the web-search, and you can use those
                  to answer the question.
                - If I EXPLICITLY ask you to search the web/internet, then use the 
                    `{search_tool_handler_method}` tool/function-call to get up to 5 results
                    from a web-search, to help you answer the question.
        
                Be very CONCISE in your responses, use no more than 1-2 sentences.
                When you answer based on a web search, First show me your answer, 
                and then show me the SOURCE(s) and EXTRACT(s) to justify your answer,
                in this format:
                
                <your answer here>
                SOURCE: https://www.wikihow.com/Be-a-Good-Assistant-Manager
                EXTRACT: Be a Good Assistant ... requires good leadership skills.
                
                SOURCE: ...
                EXTRACT: ...
                
                For the EXTRACT, ONLY show up to first 3 words, and last 3 words.
                DO NOT MAKE UP YOUR OWN SOURCES; ONLY USE SOURCES YOU FIND FROM A WEB SEARCH.
                """,
            interactive=self.interactive,
            tools=[GoogleSearchTool]
        )

        web_scraper_subordinate = AgentManager.create_task(
            agent_name=WEB_SCRAPER,
            system_message=f"""
                You are a member of the {RESEARCH_TEAM}.
                You are a research assistant who can scrape specified urls for more detailed information.
                """,
            interactive=self.interactive,
            tools=[WebScraperTool]
        )

        research_team_supervisor = AgentManager.create_task(
            agent_name=f"{RESEARCH_TEAM} Supervisor",
            system_message=f"""
                You are a supervisor tasked with managing a discussion between the {RESEARCH_TEAM}.     
                The goal of the discussion is to find a useful and correct answer to what is asked.
                
                If you are not able to correctly answer to the question, you can delegate it to a member of a team 
                based on it's skills.
                
                Here is a description of the team members skills:
                {RESEARCHER}: a research assistant who can search for up-to-date info using a search engine;
                {WEB_SCRAPER}: a research assistant who can scrape specified urls for more detailed information;   
                
                Here is how you should answer my questions:
                - IF my question is about a topic you ARE CERTAIN about, answer it directly
                - OTHERWISE, use the `{RESEARCHER}` member to get up to 3 results from a web-search, 
                  to help you answer the question. I will show you the results from the web-search, and you can use 
                  those to answer the question.
                - If I EXPLICITLY ask you to look for a specific url, then use the `{WEB_SCRAPER}` member to get the 
                  content of the page to help you answer the question.
        
                Be very CONCISE in your responses, use no more than 1-2 sentences.
                When you answer based on a web search, First show me your answer, 
                and then show me the SOURCE(s) and EXTRACT(s) to justify your answer,
                in this format:
                
                <your answer here>
                SOURCE: https://www.wikihow.com/Be-a-Good-Assistant-Manager
                EXTRACT: Be a Good Assistant ... requires good leadership skills.
                
                SOURCE: ...
                EXTRACT: ...
                
                For the EXTRACT, ONLY show up to first 3 words, and last 3 words.
                DO NOT MAKE UP YOUR OWN SOURCES; ONLY USE SOURCES YOU FIND FROM A WEB SEARCH.                
                
                Once you find a correct answer to the question say DONE and show the result. 
                """,
            is_supervisor=True,
            interactive=self.interactive
        )
        research_team_members = [researcher_subordinate, web_scraper_subordinate]
        research_team = AgentManager.create_team(research_team_supervisor, research_team_members)

        coder_subordinate = AgentManager.create_task(
            agent_name=CODER,
            system_message=f"""
                You are a member of the {CODING_TEAM}.
                You are a coder who can create and run python code.
                """,
            interactive=self.interactive
        )

        data_analyst_subordinate = AgentManager.create_task(
            agent_name=DATA_ANALYST,
            system_message=f"""
                You are a member of the {CODING_TEAM}.
                You are a data analyst that process and analyze data.
                """,
            interactive=self.interactive
        )

        coding_team_supervisor = AgentManager.create_task(
            agent_name=f"{CODING_TEAM} Supervisor",
            system_message=f"""
                You are a supervisor tasked with managing a discussion between the {CODING_TEAM}.     
                The goal of the discussion is to find a useful and correct answer to what is asked.
                                
                If you are not able to correctly answer to the question, you can delegate it to a member of a team 
                based on it's skills.
                
                Here is a description of the team members skills:
                {CODER}: a coder who can create and run python code; 
                {DATA_ANALYST}: a data analyst that process and analyze data; 
                
                Once you find a correct answer to the question say DONE and show the result. 
                """,
            is_supervisor=True,
            interactive=self.interactive
        )
        coding_team_members = [coder_subordinate, data_analyst_subordinate]
        coding_team = AgentManager.create_team(coding_team_supervisor, coding_team_members)

        discussion_supervisor = AgentManager.create_task(
            agent_name="Discussion Supervisor",
            system_message=f"""
                You are a supervisor tasked with managing a discussion between the following teams: {TEAMS}.     
                The goal of the discussion is to find a useful and correct answer to what is asked form the user.
                
                If you are not able to correctly answer to the question, you can delegate it to a team based on 
                their skills.
                
                Here is a description of the team skills:
                {RESEARCH_TEAM}: this team can find specific information using internet;
                {CODING_TEAM}: this team can create and run python code;              
                
                Once you find a correct answer to the question say DONE and show the result. 
                """,
            is_supervisor=True,
            interactive=self.interactive
        )

        teams = [research_team, coding_team]
        # What is the output of the following code: "import requests; request.get('https://www.google.com/search?q=set')" ?
        self.discussion = AgentManager.create_team(discussion_supervisor, teams)

    def start(self):
        self.logger.info("Meeting started")
        self.build_discussion_room()
        try:
            self.discussion.run()
        except Exception as e:
            self.logger.error(e)
            print('Sorry, something goes wrong. Try with a different input')

    def get_discussion(self):
        if self.discussion is None:
            self.build_discussion_room()
        return self.discussion
