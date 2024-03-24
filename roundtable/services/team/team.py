from langroid import Task

from roundtable.services.agent_manager.agent_manager import AgentManager
from roundtable.shared.utils.logger import Logger


class Team:
    def __init__(self, interactive: bool = True):
        self.logger = Logger()
        self.interactive = interactive
        self.team: Task | None = None

    def build_team(self):

        supervisor = AgentManager.create_task(
            agent_name="Supervisor",
            system_message="""
        You will receive a list of numbers from me (the user).
        Your goal is to apply a transformation to each number.
        However you do not know how to do this transformation.
        You can take the help of two people to perform the 
        transformation.
        If the number is even, send it to EvenHandler,
        and if it is odd, send it to OddHandler.
        
        IMPORTANT: send the numbers ONE AT A TIME
        
        The handlers will transform the number and give you a new number.        
        If you send it to the wrong person, you will receive a negative value.
        Your aim is to never get a negative number, so you must 
        clearly specify who you are sending the number to.
        
        Once all numbers in the given list have been transformed, 
        say DONE and show me the result. 
        Start by asking me for the list of numbers.
        """,
            is_supervisor=True,
            interactive=self.interactive
        )

        event_subordinate = AgentManager.create_task(
            agent_name="EvenHandler",
            system_message="""
                You will be given a number. 
                If it is even, divide by 2 and say the result, nothing else.
                If it is odd, say -10
                """,
            interactive=self.interactive
        )

        odd_subordinate = AgentManager.create_task(
            agent_name="OddHandler",
            system_message="""
                You will be given a number n.
                If it is odd, return (n*3+1), say nothing else.
                If it is even, say -10
                """,
            interactive=self.interactive
        )

        self.team = AgentManager.create_team(supervisor, [event_subordinate, odd_subordinate])

    def start(self):
        self.logger.info("Meeting started")
        self.build_team()
        try:
            self.team.run()
        except Exception as e:
            self.logger.error(e)
            print('Sorry, something goes wrong. Try with a different input')

    def get_team(self):
        if self.team is None:
            self.build_team()
        return self.team
