from langchain import hub
from langchain.agents import create_react_agent
from langchain_community.chat_models import ChatOllama
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolInvocation, ToolExecutor

from roundtable.services.meeting.meeting_state import MeetingState
from roundtable.services.tools_manager import ToolsManager
from roundtable.shared.utils.configurator import Configurator
from roundtable.shared.utils.logger import Logger


class Meeting:
    def __init__(self):
        self.logger = Logger()
        llm_model = Configurator.instance().get_llm_model()
        self.llm = ChatOllama(model=llm_model)
        self.prompt = hub.pull("hwchase17/react")
        self.meeting_chain = None
        self.tool_executor = None
        self.agent_runnable = None

    def build_team(self):
        tools = [ToolsManager.get_actual_date_tool]
        self.tool_executor = ToolExecutor(tools)
        self.agent_runnable = create_react_agent(self.llm, tools, self.prompt)

        workflow_graph = StateGraph(MeetingState)

        workflow_graph.add_node("agent", self.run_agent)
        workflow_graph.add_node("action", self.execute_tools)

        workflow_graph.set_entry_point("agent")

        workflow_graph.add_conditional_edges(
            "agent", self.should_continue, {"continue": "action", "end": END}
        )

        workflow_graph.add_edge("action", "agent")
        self.meeting_chain = workflow_graph.compile()

    def start_meeting(self):
        self.logger.info("Meeting started")
        self.build_team()
        running = True
        while running:
            user_input = input("Enter text (press 'q' or ctrl-c to quit): ")
            if user_input.lower() == 'q':
                running = False
            # print(f"> {user_input}")
            inputs = {"input": user_input, "chat_history": []}
            for s in self.meeting_chain.stream(inputs):
                if "__end__" not in s:
                    # print(s)
                    print("---")
                    result = list(s.values())[0]
                    print(result)
        self.end_meeting()

    def end_meeting(self):
        self.logger.info("Meeting ended")

    def get_chain(self):
        if self.meeting_chain is None:
            self.build_team()
        return self.meeting_chain

    def execute_tools(self, state):
        print("Called `execute_tools`")
        messages = [state["agent_outcome"]]
        last_message = messages[-1]

        tool_name = last_message.tool

        print(f"Calling tool: {tool_name}")

        action = ToolInvocation(
            tool=tool_name,
            tool_input=last_message.tool_input,
        )
        response = self.tool_executor.invoke(action)
        return {"intermediate_steps": [(state["agent_outcome"], response)]}

    def run_agent(self, state):
        """
        #if you want to better manages intermediate steps
        inputs = state.copy()
        if len(inputs['intermediate_steps']) > 5:
            inputs['intermediate_steps'] = inputs['intermediate_steps'][-5:]
        """
        agent_outcome = self.agent_runnable.invoke(state)
        return {"agent_outcome": agent_outcome}

    @staticmethod
    def should_continue(state):
        messages = [state["agent_outcome"]]
        last_message = messages[-1]
        if "Action" not in last_message.log:
            return "end"
        else:
            return "continue"
