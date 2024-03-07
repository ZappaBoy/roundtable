import streamlit as st

from roundtable.services.meeting.meeting import Meeting
from roundtable.shared.utils.logger import Logger


class Interface:
    def __init__(self):
        self.logger = Logger()
        self.title = "Roundtable"
        self.subheader = 'Meeting room'
        self.input_message_placeholder = "Enter text here..."
        self.button_label = "Send"
        self.meeting_chain = Meeting().get_chain()

    def build(self):
        st.title(self.title)
        st.subheader(self.subheader)
        input_text = st.text_area(self.input_message_placeholder)
        if st.button(self.button_label):
            if input_text:
                # TODO: Use async generator
                try:
                    inputs = {"input": input_text, "chat_history": []}
                    for s in self.meeting_chain.stream(inputs):
                        if "__end__" not in s:
                            st.write('---')
                            result = list(s.values())[0]
                            st.write(result)
                except Exception as e:
                    self.logger.error(e)
                    st.warning('Sorry, something goes wrong. Try with a different input')
            else:
                st.warning("Please write a message...")


if __name__ == '__main__':
    Interface().build()
