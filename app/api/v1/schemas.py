from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# ============================================================================
# BASE REQUEST/RESPONSE SCHEMAS
# ============================================================================

class QuestionRequest(BaseModel):
    question: str = Field(..., description="Natural language question about the database")


class BaseResponse(BaseModel):
    success: bool = Field(..., description="Whether the operation was successful")
    error: str | None = Field(None, description="Error message if operation failed")


# ============================================================================
# CHAIN SCHEMAS
# ============================================================================

class ChainAnswerResponse(BaseResponse):
    question: str
    query: str | None = Field(None, description="Generated SQL query")
    result: str | None = Field(None, description="Raw SQL query results")
    answer: str = Field(..., description="Natural language answer")
    approach: str = Field("chain", description="Approach used (chain)")


class QuestionWithApprovalRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    action: Literal["start", "approve", "reject"] = Field(..., description="Action to perform")
    thread_id: str = Field("1", description="Thread ID for state persistence")


class ApprovalResponse(BaseResponse):
    thread_id: str
    status: Literal["awaiting_approval", "completed", "rejected", "error"]
    query: str | None = Field(None, description="SQL query awaiting approval")
    answer: str | None = Field(None, description="Final answer after approval")
    message: str = Field(..., description="Status message")


# ============================================================================
# AGENT SCHEMAS
# ============================================================================

class AgentAnswerResponse(BaseResponse):
    question: str
    answer: str = Field(..., description="Natural language answer")
    approach: str = Field("agent", description="Approach used (agent)")
    available_tools: list[str] = Field(default_factory=list, description="Available tools used by agent")


class VectorSearchRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    openai_api_key: str = Field(..., description="OpenAI API key for embeddings")


class VectorSearchTestRequest(BaseModel):
    query: str = Field(..., description="Search query for proper nouns")
    openai_api_key: str = Field(..., description="OpenAI API key for embeddings")


class VectorSearchTestResponse(BaseResponse):
    query: str
    results: list[str] = Field(..., description="Similar proper nouns found")


# ============================================================================
# UTILITY SCHEMAS
# ============================================================================

class SchemaResponse(BaseResponse):
    tables: list[str] = Field(default_factory=list, description="List of available tables")
    schema: str = Field("", description="Database schema information")
    sample_data: dict[str, str] = Field(default_factory=dict, description="Sample data from each table")


class TableDescriptionRequest(BaseModel):
    table_name: str = Field(..., description="Name of the table to describe")


class TableDescriptionResponse(BaseResponse):
    table_name: str
    description: str | None = Field(None, description="Agent-generated table description")


class ComparisonResponse(BaseResponse):
    question: str
    chain_result: dict[str, Any] = Field(..., description="Result from chain approach")
    agent_result: dict[str, Any] = Field(..., description="Result from agent approach")


# ============================================================================
# STREAMING SCHEMAS
# ============================================================================

class StreamingStep(BaseModel):
    type: str = Field(..., description="Type of step (write_query, execute_query, generate_answer)")
    content: Any = Field(..., description="Step content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Step timestamp")


class StreamingResponse(BaseModel):
    steps: list[StreamingStep] = Field(default_factory=list, description="List of streaming steps")
    status: Literal["streaming", "complete", "error"] = Field("streaming", description="Stream status")


# ============================================================================
# DETAILED RESPONSE SCHEMAS (for backward compatibility)
# ============================================================================

class DetailedAnswerResponse(BaseResponse):
    question: str
    sql_query: str | None = Field(None, description="Generated SQL query")
    results: str | None = Field(None, description="Raw SQL query results")
    answer: str = Field(..., description="Natural language answer")
    row_count: int = Field(0, description="Number of rows returned")
    approach: str = Field("detailed", description="Detailed approach with full information")


class AnswerResponse(BaseModel):
    question: str
    answer: str = Field(..., description="Natural language answer to the question")


# ============================================================================
# CONFIGURATION SCHEMAS
# ============================================================================

class ChainConfig(BaseModel):
    enable_streaming: bool = Field(False, description="Enable streaming responses")
    enable_approval: bool = Field(False, description="Enable human-in-the-loop approval")
    top_k_results: int = Field(10, description="Maximum number of results to return")
    thread_id: str = Field("default", description="Thread ID for stateful operations")


class AgentConfig(BaseModel):
    enable_vector_search: bool = Field(False, description="Enable vector search for proper nouns")
    openai_api_key: str | None = Field(None, description="OpenAI API key for embeddings")
    max_iterations: int = Field(10, description="Maximum agent iterations")
    enable_streaming: bool = Field(False, description="Enable streaming responses")


class ConfiguredQuestionRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    chain_config: ChainConfig | None = Field(None, description="Chain-specific configuration")
    agent_config: AgentConfig | None = Field(None, description="Agent-specific configuration")


# ============================================================================
# ERROR SCHEMAS
# ============================================================================

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error")
    details: dict[str, Any] | None = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class ValidationErrorResponse(BaseModel):
    error: str = Field("Validation Error", description="Error type")
    details: list[dict[str, Any]] = Field(..., description="Validation error details")


# ============================================================================
# METRICS SCHEMAS
# ============================================================================

class PerformanceMetrics(BaseModel):
    execution_time: float = Field(..., description="Total execution time in seconds")
    query_generation_time: float = Field(..., description="Time to generate SQL query")
    query_execution_time: float = Field(..., description="Time to execute SQL query")
    answer_generation_time: float = Field(..., description="Time to generate natural language answer")
    approach: str = Field(..., description="Approach used (chain/agent)")


class MetricsResponse(BaseResponse):
    question: str
    answer: str
    metrics: PerformanceMetrics
    query: str | None = Field(None, description="Generated SQL query")
    result_count: int = Field(0, description="Number of results returned")


# ============================================================================
# BATCH PROCESSING SCHEMAS
# ============================================================================

class BatchQuestionRequest(BaseModel):
    questions: list[str] = Field(..., description="List of questions to process")
    approach: Literal["chain", "agent", "both"] = Field("chain", description="Processing approach")
    config: dict[str, Any] | None = Field(None, description="Configuration for batch processing")


class BatchQuestionResponse(BaseResponse):
    results: list[dict[str, Any]] = Field(..., description="Results for each question")
    total_questions: int = Field(..., description="Total number of questions processed")
    successful_answers: int = Field(..., description="Number of successful answers")
    failed_answers: int = Field(..., description="Number of failed answers")
    processing_time: float = Field(..., description="Total processing time")


# ============================================================================
# HEALTH CHECK SCHEMAS
# ============================================================================

class HealthCheckResponse(BaseModel):
    status: Literal["healthy", "unhealthy"] = Field(..., description="Overall health status")
    database: str = Field(..., description="Database connection status")
    chain_qa: str = Field(..., description="Chain QA system status")
    agent_qa: str = Field(..., description="Agent QA system status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    version: str = Field("1.0.0", description="API version")


# ============================================================================
# EXPORT SCHEMAS
# ============================================================================

class ExportRequest(BaseModel):
    format: Literal["json", "csv", "xlsx"] = Field("json", description="Export format")
    include_queries: bool = Field(True, description="Include SQL queries in export")
    include_results: bool = Field(True, description="Include raw results in export")
    date_range: dict[str, str] | None = Field(None, description="Date range filter")


class ExportResponse(BaseResponse):
    download_url: str | None = Field(None, description="URL to download exported data")
    file_size: int | None = Field(None, description="Size of exported file in bytes")
    record_count: int = Field(0, description="Number of records exported")
    export_format: str = Field(..., description="Format of exported data")
