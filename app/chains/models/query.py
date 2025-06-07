from typing import Annotated

from typing_extensions import TypedDict


class QueryOutput(TypedDict):
    """Generated SQL query with structured output"""
    query: Annotated[str, ..., "Syntactically valid SQL query."]
