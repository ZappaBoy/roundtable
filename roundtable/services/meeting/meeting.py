import langroid as lr
import langroid.language_models as lm

from roundtable.shared.utils.configurator import Configurator
from roundtable.shared.utils.logger import Logger


class Meeting:
    def __init__(self):
        self.logger = Logger()
        llm_model = Configurator.instance().get_llm_model()
        self.llm_config = lm.OpenAIGPTConfig(
            chat_model=llm_model,
            chat_context_length=16_000,
        )
        self.use_tools = True
        self.supervisor = None
        self.supervisor_task = None

    def build_team(self):
        config = lr.ChatAgentConfig(
            llm=self.llm_config,
            # system_message="You are helpful but concise",
            use_tools=self.use_tools,
            use_functions_api=not self.use_tools,
            vecdb=None,
        )

        self.supervisor = lr.ChatAgent(config)
        self.supervisor.enable_message(lr.agent.tools.RecipientTool)

        self.supervisor_task = lr.Task(
            self.supervisor,
            name="Processor",
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
            llm_delegate=True,
            single_round=False,
        )

        even_agent = lr.ChatAgent(config)
        even_task = lr.Task(
            even_agent,
            name="EvenHandler",
            system_message="""
                You will be given a number. 
                If it is even, divide by 2 and say the result, nothing else.
                If it is odd, say -10
                """,
            single_round=True,
        )

        odd_agent = lr.ChatAgent(config)
        odd_task = lr.Task(
            odd_agent,
            name="OddHandler",
            system_message="""
                You will be given a number n. 
                If it is odd, return (n*3+1), say nothing else. 
                If it is even, say -10
                """,
            single_round=True,
        )

        self.supervisor_task.add_sub_task([even_task, odd_task])

    def start_meeting(self):
        self.logger.info("Meeting started")
        self.build_team()
        try:
            self.supervisor_task.run()
        except Exception as e:
            self.logger.error(e)
            print('Sorry, something goes wrong. Try with a different input')

        self.end_meeting()

    def end_meeting(self):
        self.logger.info("Meeting ended")
