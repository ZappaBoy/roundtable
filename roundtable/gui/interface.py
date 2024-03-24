import streamlit as st

from roundtable.services.discussion_room.discussion_room import DiscussionRoom
from roundtable.shared.utils.logger import Logger


class Interface:
    def __init__(self):
        self.logger = Logger()
        self.title = "Roundtable"
        self.subheader = 'Meeting room'
        self.input_message_placeholder = "Enter text here..."
        self.button_label = "Send"
        self.discussion_room = DiscussionRoom(interactive=False).get_discussion()

    def build(self):
        st.title(self.title)
        st.subheader(self.subheader)
        initialized_response = self.discussion_room.init("How can I help you?")
        st.write(initialized_response)

        with st.form("user_chat_form", clear_on_submit=True):
            input_text = st.text_input(label="Message", placeholder=self.input_message_placeholder, key="input_text")
            submit_form = st.form_submit_button(self.button_label)
            # TODO: Use async generator
            if submit_form:
                st.write(f"Message: {input_text}")
                try:
                    result = self.discussion_room.run(input_text)
                    st.write(f"Response: {result}")
                except Exception as e:
                    self.logger.error(e)
                    st.warning('Sorry, something goes wrong. Try with a different input')


if __name__ == '__main__':
    Interface().build()
