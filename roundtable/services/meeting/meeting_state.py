import operator
from typing import TypedDict, Annotated, Sequence

from langchain_core.messages import BaseMessage


class MeetingState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
