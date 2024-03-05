import operator
from typing import TypedDict, Annotated, List

from langchain_core.messages import BaseMessage


class MeetingState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    next: str
