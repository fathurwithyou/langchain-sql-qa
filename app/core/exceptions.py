from fastapi import Request
from fastapi.responses import JSONResponse


class QueryProcessingError(Exception):
    def __init__(self, detail: str = "Error processing the query with the agent."):
        self.detail = detail


async def query_processing_exception_handler(request: Request, exc: QueryProcessingError):  # noqa: ARG001
    return JSONResponse(
        status_code=500,
        content={"error": "Query Processing Failed", "detail": exc.detail},
    )


async def generic_exception_handler(request: Request, exc: Exception): # noqa: ARG001
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error",
                 "detail": "An unexpected error occurred."},
    )
