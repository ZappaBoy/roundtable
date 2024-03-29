import streamlit as st

from roundtable.services.discussion_room.discussion_room import DiscussionRoom
from roundtable.shared.utils.logger import Logger

USER_NAME = "User"


class Interface:

    def __init__(self):
        self.logger = Logger()
        self.title = "Roundtable"
        self.subheader = 'Meeting room'
        self.input_message_placeholder = "Enter text here..."
        self.button_label = "Send"
        self.discussion_room = DiscussionRoom(callback=self.show_message)

    def build(self):
        st.title(self.title)
        st.subheader(self.subheader)

        with st.form("user_chat_form", clear_on_submit=True):
            st.write("Enter your message:")
            input_text = st.text_input(label="Message", placeholder=self.input_message_placeholder, key="input_text")
            submit_form = st.form_submit_button(self.button_label)
            if submit_form:
                try:
                    discussion, manager = self.discussion_room.get_discussion()
                    discussion.initiate_chat(manager, message=input_text)
                except Exception as e:
                    self.logger.error(e)
                    st.warning('Sorry, something goes wrong. Try with a different input')

    @staticmethod
    def show_message(sender: str, message: str):
        with st.chat_message(sender):
            st.markdown(message)


if __name__ == '__main__':
    Interface().build()
