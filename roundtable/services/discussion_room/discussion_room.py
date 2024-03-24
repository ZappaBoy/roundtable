from langroid import Task

from roundtable.services.agent_manager.agent_manager import AgentManager
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

        researcher_subordinate = AgentManager.create_task(
            agent_name=RESEARCHER,
            system_message=f"""
                You are a member of the {RESEARCH_TEAM}.
                You are a research assistant who can search for up-to-date info using a search engine.
                """,
            interactive=self.interactive
        )

        web_scraper_subordinate = AgentManager.create_task(
            agent_name=WEB_SCRAPER,
            system_message="""
                You are a member of the {RESEARCH_TEAM}.
                You are a research assistant who can scrape specified urls for more detailed information.
                """,
            interactive=self.interactive
        )

        research_team_supervisor = AgentManager.create_task(
            agent_name=f"{RESEARCH_TEAM} Supervisor",
            system_message=f"""
                You are a supervisor tasked with managing a discussion between the {RESEARCH_TEAM}.     
                The goal of the discussion is to find a useful and correct answer to what is asked.
                                
                To do that you need to define a set of steps needed to find the answer.
                If you are not able to correctly do a step, you can delegate it to a member of a team based on it's 
                skills.
                
                Here is a description of the team members skills:
                {RESEARCHER}: a research assistant who can search for up-to-date info using a search engine;
                {WEB_SCRAPER}: a research assistant who can scrape specified urls for more detailed information;   
                
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
            agent_name=CODER,
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
                                
                To do that you need to define a set of steps needed to find the answer.
                If you are not able to correctly do a step, you can delegate it to a member of a team based on it's 
                skills.
                
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
                
                To do that you need to define a set of steps needed to find the answer.
                If you are not able to correctly do a step, you can delegate it to a team based on their skills.
                
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
