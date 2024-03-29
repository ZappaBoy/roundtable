from typing import Callable

from autogen import GroupChatManager


class CallbackGroupChatManager(GroupChatManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback = None

    def set_callback(self, callback: Callable):
        self.callback = callback

    def _process_received_message(self, message, sender, silent):
        self.callback(sender.name, message)
        return super()._process_received_message(message, sender, silent)
