import streamlit as st

from autogen import AssistantAgent, UserProxyAgent


class GUIAssistantAgent(AssistantAgent):
    def _process_received_message(self, message, sender, silent):
        print(f"GUIAssistantAgent: {message}")
        with st.chat_message(sender.name):
            st.markdown(message['content'])
        return super()._process_received_message(message, sender, silent)


class GUIUserProxyAgent(UserProxyAgent):
    def _process_received_message(self, message, sender, silent):
        print(f"GUIUserProxyAgent: {message}")
        with st.chat_message(sender.name):
            st.markdown(message['content'])
        return super()._process_received_message(message, sender, silent)
