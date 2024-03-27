from textwrap import dedent

from autogen import UserProxyAgent, ConversableAgent, AssistantAgent, GroupChat, GroupChatManager

from roundtable.models.discussion_room_config import DiscussionRoomConfig
from roundtable.services.discussion_room.trackable_agent import GUIUserProxyAgent, GUIAssistantAgent
from roundtable.shared.utils.configurator import Configurator
from roundtable.shared.utils.logger import Logger

# TODO
# RESEARCHER = "Researcher"
# WEB_SCRAPER = "Web Scraper"
CODER = "Coder"
# DATA_ANALYST = "Data Analyst"
#
# RESEARCH_TEAM = "Research Team"
# CODING_TEAM = "Coding Team"
# TEAMS = [RESEARCH_TEAM, CODING_TEAM]

USER_PROXY = "UserProxy"
ASSISTANT = "Assistant"

TERMINATE = "TERMINATE"
CONTINUE = "CONTINUE"
REPLY_TERMINATE_ON_SUCCESS = dedent(f"""
    Reply {TERMINATE} if the task has been solved at full satisfaction.
    Otherwise, reply {CONTINUE}, or the reason why the task is not solved yet.""")


class DiscussionRoom:
    def __init__(self, gui: bool = False):
        self.logger = Logger()
        self.gui = gui
        self.discussion = None
        self.manager = None
        configurator = Configurator.instance()
        self.config: DiscussionRoomConfig = configurator.get_discussion_room_config()

    def get_llm_config(self, model_name: str):
        llm_config = [{"base_url": self.config.base_url, "api_key": self.config.api_key, "model": model_name}]
        return {"config_list": llm_config}

    def build_discussion_room(self):
        if self.gui:
            user_proxy_agent = GUIUserProxyAgent
            assistant_agent = GUIAssistantAgent
        else:
            user_proxy_agent = UserProxyAgent
            assistant_agent = AssistantAgent

        llm_config = self.get_llm_config(self.config.llm_model_name)
        code_config = self.get_llm_config(self.config.code_model_name)

        user_proxy = user_proxy_agent(
            name=USER_PROXY,
            max_consecutive_auto_reply=10,
            llm_config=llm_config,
            system_message=REPLY_TERMINATE_ON_SUCCESS
            # code_execution_config={"work_dir": "user", "use_docker": False},
        )

        coder = assistant_agent(
            name=CODER,
            llm_config=code_config,
            system_message=REPLY_TERMINATE_ON_SUCCESS,
            # code_execution_config={"work_dir": "coder", "use_docker": False}
        )

        assistant = assistant_agent(
            name=ASSISTANT,
            llm_config=llm_config,
            system_message=REPLY_TERMINATE_ON_SUCCESS
            # code_execution_config={"work_dir": "assistant", "use_docker": False}
        )

        group_chat = GroupChat(agents=[user_proxy, coder, assistant], messages=[], max_round=12)
        self.manager = GroupChatManager(groupchat=group_chat, llm_config=llm_config,
                                        human_input_mode=TERMINATE,
                                        is_termination_msg=DiscussionRoom.is_termination_message)
        self.discussion = user_proxy

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
