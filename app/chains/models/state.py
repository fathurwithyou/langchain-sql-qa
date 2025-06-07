from typing_extensions import TypedDict


class State(TypedDict):
    """Application state for LangGraph chain"""
    question: str
    query: str
    result: str
    answer: str
