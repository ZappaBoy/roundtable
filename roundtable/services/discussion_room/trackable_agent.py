import streamlit as st

from autogen import AssistantAgent, UserProxyAgent


def show_message(sender: str, message: str):
    with st.chat_message(sender):
        st.markdown(message)


class GUIAssistantAgent(AssistantAgent):
    def _process_received_message(self, message, sender, silent):
        print(f"GUIAssistantAgent: {message}")
        show_message(sender.name, message['content'])
        return super()._process_received_message(message, sender, silent)


class GUIUserProxyAgent(UserProxyAgent):
    def _process_received_message(self, message, sender, silent):
        print(f"GUIUserProxyAgent: {message}")
        show_message(sender.name, message['content'])
        return super()._process_received_message(message, sender, silent)
