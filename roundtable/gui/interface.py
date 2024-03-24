import streamlit as st

from roundtable.shared.utils.logger import Logger


class Interface:
    def __init__(self):
        self.logger = Logger()
        self.title = "Roundtable"
        self.subheader = 'Meeting room'
        self.input_message_placeholder = "Enter text here..."
        self.button_label = "Send"

    def build(self):
        st.title(self.title)
        st.subheader(self.subheader)
        input_text = st.text_area(self.input_message_placeholder)
        if st.button(self.button_label):
            if input_text:
                # TODO: Use async generator
                try:
                    st.write(input_text)
                except Exception as e:
                    self.logger.error(e)
                    st.warning('Sorry, something goes wrong. Try with a different input')
            else:
                st.warning("Please write a message...")


if __name__ == '__main__':
    Interface().build()
