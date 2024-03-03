import streamlit as st


class Interface:
    def __init__(self):
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
                output_text = input_text.upper()
                st.write("Response:")
                st.write(output_text)
            else:
                st.warning("Please write a message...")


if __name__ == '__main__':
    Interface().build()
