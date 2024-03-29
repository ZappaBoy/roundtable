from textwrap import dedent
from typing import Callable

from autogen import UserProxyAgent, ConversableAgent, AssistantAgent, GroupChat, GroupChatManager

from roundtable.models.discussion_room_config import DiscussionRoomConfig
from roundtable.services.discussion_room.trackable_agent import CallbackGroupChatManager
from roundtable.shared.utils.configurator import Configurator
from roundtable.shared.utils.logger import Logger

ADMIN = "Admin"
SUPERVISOR = "Supervisor"
ASSISTANT = "Assistant"
ENGINEER = "Engineer"
EXECUTOR = "Executor"
CRITIC = "Critic"

TERMINATE = "TERMINATE"
NEVER = "NEVER"
CONTINUE = "CONTINUE"

REPLY_TERMINATE_ON_SUCCESS = dedent(f"""
    Reply {TERMINATE} if the task has been solved at full satisfaction.
    Otherwise, reply {CONTINUE}, or the reason why the task is not solved yet.""")


class DiscussionRoom:
    def __init__(self, callback: Callable = None):
        self.logger = Logger()
        self.callback: Callable = callback
        self.discussion = None
        self.manager = None
        configurator = Configurator.instance()
        self.config: DiscussionRoomConfig = configurator.get_discussion_room_config()

    def get_llm_config(self, model_name: str):
        llm_config = [{"base_url": self.config.base_url, "api_key": self.config.api_key, "model": model_name}]
        return {"config_list": llm_config}

    def build_discussion_room(self):
        if self.callback:
            group_chat_manager = CallbackGroupChatManager
        else:
            group_chat_manager = GroupChatManager

        llm_config = self.get_llm_config(self.config.llm_model_name)
        code_config = self.get_llm_config(self.config.code_model_name)

        code_execution_config = {}
        if self.config.use_code_execution:
            code_execution_config = {"work_dir": "generated_code", "use_docker": self.config.execute_code_in_docker}

        admin = UserProxyAgent(
            name=ADMIN,
            max_consecutive_auto_reply=10,
            llm_config=llm_config,
            system_message=dedent(f"""
                {ADMIN}. Interact with the {SUPERVISOR} to discuss the plan. Plan execution needs to be approved 
                by this {ADMIN}.
                {REPLY_TERMINATE_ON_SUCCESS}
                """),
        )

        supervisor = AssistantAgent(
            name=SUPERVISOR,
            llm_config=llm_config,
            system_message=dedent(f"""
                {SUPERVISOR}. Suggest a plan. Revise the plan based on feedback from {ADMIN} and {CRITIC}, until 
                {ADMIN} approval. The plan may involve the {ENGINEER} who can write code, the {EXECUTOR} that 
                run the code and the {ASSISTANT} that analyze and elaborate the output of the code and conversation. 
                Explain the plan first. Be clear which step is performed by the {ENGINEER} and which step 
                is performed by the {ASSISTANT}.
                If the {ASSISTANT} gives the correct output say {TERMINATE} and write the correct answer.
                """),
        )

        assistant = AssistantAgent(
            name=ASSISTANT,
            llm_config=llm_config,
            system_message=dedent(f"""
                {ASSISTANT}. You follow an approved plan. You are able to analyze and elaborate the output of the 
                {EXECUTOR} and the entire conversation to make simply understandable. You don't write code.
                """),
        )

        engineer = AssistantAgent(
            name=ENGINEER,
            llm_config=code_config,
            system_message=dedent(f"""
                {ENGINEER}. You follow an approved plan. You write python/shell code to solve tasks. 
                Wrap the code in a code block that specifies the script type. The user can't modify your code. So do 
                not suggest incomplete code which requires others to modify. Don't use a code block if it's not 
                intended to be executed by the executor.
                Don't include multiple code blocks in one response. Do not ask others to copy and paste the result. 
                Check the execution result returned by the executor.
                If the result indicates there is an error, fix the error and output the code again. Suggest the full 
                code instead of partial code or code changes. If the error can't be fixed or if the task is not solved
                even after the code is executed successfully, analyze the problem, revisit your assumption, collect 
                additional info you need, and think of a different approach to try.
                """),
        )

        executor = AssistantAgent(
            name=EXECUTOR,
            llm_config=code_config,
            code_execution_config=code_execution_config,
            human_input_mode=NEVER,
            system_message=dedent(f"""
                {EXECUTOR}. You must execute the code written by the {ENGINEER} and report the result. Install all the 
                required dependencies before running the code. If the code execution fails, report the error message.
                """),
        )

        critic = AssistantAgent(
            name=CRITIC,
            llm_config=llm_config,
            human_input_mode=NEVER,
            system_message=dedent(f"""
                {CRITIC}. Double check plan, claims, code from other agents and provide feedback. Check whether the plan 
                includes adding verifiable info such as source URL.
                """),
        )

        group_chat = GroupChat(messages=[], max_round=20, admin_name=ADMIN,
                               speaker_selection_method="round_robin",
                               agents=[admin, supervisor, critic, engineer, executor, assistant])

        self.manager = group_chat_manager(groupchat=group_chat, llm_config=llm_config,
                                          human_input_mode=TERMINATE,
                                          is_termination_msg=DiscussionRoom.is_termination_message)
        if self.callback:
            self.manager.set_callback(self.callback)

        self.discussion = admin

    @staticmethod
    def is_termination_message(message: dict) -> bool:
        return message.get("content", "").rstrip().endswith(TERMINATE)

    def start(self):
        self.logger.info("Meeting started")
        self.build_discussion_room()
        try:
            user_input = input("Enter your message: ")
            self.discuss(user_input)
        except Exception as e:
            self.logger.error(e)
            print('Sorry, something goes wrong. Try with a different input')

    def get_discussion(self) -> tuple[ConversableAgent, GroupChatManager]:
        if self.discussion is None:
            self.build_discussion_room()
        return self.discussion, self.manager

    def discuss(self, message: str):
        discussion, manager = self.get_discussion()
        return discussion.initiate_chat(manager, message=message)
