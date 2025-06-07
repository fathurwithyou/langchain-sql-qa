from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import endpoints as v1_endpoints
from app.core.exceptions import (
    QueryProcessingError,
    generic_exception_handler,
    query_processing_exception_handler,
)
from app.core.logging_config import setup_logging
from app.services.database import setup_database

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Application lifespan manager"""

    logger.info("Starting SQL QA Application")
    try:
        setup_database()
        logger.info("Database setup completed")
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise

    yield

    logger.info("Shutting down SQL QA Application")


app = FastAPI(
    title="LangChain SQL QA API",
    description="""
    Complete SQL Question/Answering system following LangChain tutorial.
    - **Predictable sequence**: question → SQL → execute → answer
    - **Streaming support**: Real-time step visibility
    - **Human-in-the-loop**: Approval workflow for query execution
    - **Graph visualization**: Mermaid diagrams of execution flow
    - **Multiple queries**: Can query database multiple times
    - **Error recovery**: Automatically fixes and retries failed queries
    - **Schema exploration**: Can describe tables and database structure
    - **Vector search**: Handle high-cardinality columns with semantic search
    - **Chinook-like schema**: Comprehensive music store database
    - **Sample data**: Artists, Albums, Tracks, Customers, Invoices
    - **SQLite backend**: Easy setup and deployment
    This system executes AI-generated SQL queries. Always ensure:
    - Database permissions are scoped narrowly
    - Use human approval for sensitive operations
    - Monitor query execution in production
    1. Try `/api/v1/schema` to explore the database
    2. Use `/api/v1/chain/ask` for simple questions
    3. Use `/api/v1/agent/ask` for complex queries
    4. Enable streaming with `/api/v1/chain/ask-streaming`
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_exception_handler(QueryProcessingError,
                          query_processing_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


app.include_router(
    v1_endpoints.router,
    prefix="/api/v1",
    tags=["SQL QA System"]
)


@app.get("/", tags=["Root"])
def read_root():
    """Root endpoint with API information"""
    return {
        "message": "LangChain SQL QA System",
        "description": "Complete implementation following LangChain tutorial",
        "features": {
            "chain": "Predictable sequence with streaming & approval",
            "agent": "Multiple queries with error recovery & vector search",
            "database": "Chinook-like schema with comprehensive sample data"
        },
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/api/v1/health",
            "schema": "/api/v1/schema",
            "chain_basic": "/api/v1/chain/ask",
            "chain_streaming": "/api/v1/chain/ask-streaming",
            "chain_approval": "/api/v1/chain/ask-with-approval",
            "agent_basic": "/api/v1/agent/ask",
            "agent_streaming": "/api/v1/agent/ask-streaming",
            "agent_vector": "/api/v1/agent/ask-with-vector-search",
            "compare": "/api/v1/compare"
        },
        "tutorial_examples": {
            "simple_count": "How many employees are there?",
            "join_query": "Which country's customers spent the most?",
            "describe_table": "Describe the PlaylistTrack table",
            "proper_noun": "How many albums does Alice in Chains have?",
            "aggregation": "What is the average track length?",
            "complex": "Show me the top 5 artists by total sales revenue"
        }
    }


@app.get("/api/v1/examples", tags=["Examples"])
def get_example_questions():
    """Get example questions to try with the system"""
    return {
        "basic_questions": [
            "How many artists are in the database?",
            "How many employees are there?",
            "What are the different genres available?"
        ],
        "join_queries": [
            "Which country's customers spent the most?",
            "What are the names of all albums by AC/DC?",
            "Which artist has the most albums?",
            "Show me customers from Brazil"
        ],
        "aggregation_queries": [
            "What is the average price of tracks?",
            "Which genre has the most tracks?",
            "What is the total revenue by country?",
            "Show me the longest tracks"
        ],
        "complex_queries": [
            "List all tracks with their album and artist names",
            "Show me the top 5 customers by total purchases",
            "Which employees support the most customers?",
            "What are the most popular playlists?"
        ],
        "schema_exploration": [
            "Describe the PlaylistTrack table",
            "What tables are available in the database?",
            "Show me the structure of the Invoice table"
        ],
        "proper_noun_queries": [
            "How many albums does Alice in Chains have?",
            "Show me tracks by The Beatles",
            "What albums are by Aerosmith?"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
