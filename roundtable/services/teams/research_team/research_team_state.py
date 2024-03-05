import operator
from typing import TypedDict, Annotated, List

from langchain_core.messages import BaseMessage


class ResearchTeamState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    team_members: List[str]
    next: str
