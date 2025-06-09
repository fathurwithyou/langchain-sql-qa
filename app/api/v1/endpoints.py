import io
import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.agents.sql_agent import SQLAgentQA
from app.api.v1 import schemas
from app.chains.sql_chain import SQLChainQA
from app.services.database import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter()


_chain_qa = None
_agent_qa = None


def get_chain_qa():
    """Get or create chain QA instance"""
    global _chain_qa
    if _chain_qa is None:
        db = get_db_connection()
        _chain_qa = SQLChainQA(database=db)
    return _chain_qa


def get_agent_qa():
    """Get or create agent QA instance"""
    global _agent_qa
    if _agent_qa is None:
        db = get_db_connection()
        _agent_qa = SQLAgentQA(database=db, enable_vector_search=False)
    return _agent_qa


def serialize_message(message):
    """Safely serialize LangChain message objects"""
    try:
        return {
            "type": getattr(message, 'type', 'unknown'),
            "content": getattr(message, 'content', ''),
            "id": getattr(message, 'id', None),
            "name": getattr(message, 'name', None),
            "tool_calls": [
                {
                    "name": getattr(tc, 'name', tc.get('name', 'unknown') if isinstance(tc, dict) else 'unknown'),
                    "args": getattr(tc, 'args', tc.get('args', {}) if isinstance(tc, dict) else {}),
                    "id": getattr(tc, 'id', tc.get('id', None) if isinstance(tc, dict) else None)
                }
                for tc in getattr(message, 'tool_calls', [])
            ] if hasattr(message, 'tool_calls') and message.tool_calls else []
        }
    except Exception as e:
        logger.warning(f"Error serializing message: {e}")
        return {
            "type": "error",
            "content": f"Could not serialize message: {str(e)}",
            "error": str(e)
        }


@router.post("/chain/ask", response_model=schemas.ChainAnswerResponse)
def ask_question_chain(request: schemas.QuestionRequest):
    """
    Ask question using Chain approach (predictable sequence)
    """
    try:
        chain_qa = get_chain_qa()
        result = chain_qa.run(request.question)

        return schemas.ChainAnswerResponse(
            question=result["question"],
            query=result["query"],
            result=result["result"],
            answer=result["answer"],
            success=True,
            approach="chain"
        )
    except Exception as e:
        logger.error(f"Error in chain QA: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/chain/ask-streaming")
def ask_question_chain_streaming(request: schemas.QuestionRequest):
    """
    Ask question using Chain approach with streaming
    """
    def generate_stream():
        try:
            chain_qa = get_chain_qa()
            for step in chain_qa.graph.stream(
                {"question": request.question},
                stream_mode="updates"
            ):
                yield f"data: {json.dumps(step)}\n\n"

            yield f"data: {json.dumps({'status': 'complete'})}\n\n"

        except Exception as e:
            logger.error(f"Error in streaming chain QA: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={"Content-Type": "text/event-stream"}
    )


@router.post("/chain/ask-with-approval", response_model=schemas.ApprovalResponse)
def ask_question_chain_with_approval(request: schemas.QuestionWithApprovalRequest):
    """
    Ask question using Chain approach with human-in-the-loop approval
    """
    try:
        chain_qa = get_chain_qa()

        if request.action == "start":
            steps = []
            generated_query = None

            for step in chain_qa.run_with_approval(request.question, request.thread_id):
                steps.append(step)
                logger.info(f"Approval workflow step: {step}")

                if isinstance(step, dict) and "write_query" in step:
                    query_result = step["write_query"]
                    if isinstance(query_result, dict) and "query" in query_result:
                        generated_query = query_result["query"]
                        logger.info(
                            f"Captured generated query: {generated_query}")

            if generated_query:
                return schemas.ApprovalResponse(
                    thread_id=request.thread_id,
                    status="awaiting_approval",
                    query=generated_query,
                    message=f"Query generated: '{generated_query}'. Do you want to execute it?",
                    success=True
                )
            else:
                try:
                    config = {"configurable": {"thread_id": request.thread_id}}
                    current_state = chain_qa.graph_with_approval.get_state(
                        config)

                    if current_state and hasattr(current_state, 'values'):
                        state_values = current_state.values
                        if "query" in state_values:
                            return schemas.ApprovalResponse(
                                thread_id=request.thread_id,
                                status="awaiting_approval",
                                query=state_values["query"],
                                message=f"Query generated: '{state_values['query']}'. Do you want to execute it?",
                                success=True
                            )
                except Exception as state_error:
                    logger.warning(f"Could not get state: {state_error}")

                return schemas.ApprovalResponse(
                    thread_id=request.thread_id,
                    status="error",
                    message="Could not generate or capture query for approval",
                    success=False,
                    error="No query was generated"
                )

        elif request.action == "approve":
            steps = chain_qa.continue_after_approval(request.thread_id)
            final_answer = "Processing completed"
            executed_query = None

            for step in steps:
                logger.info(f"Post-approval step: {step}")

                if isinstance(step, dict):
                    if "execute_query" in step:
                        execute_result = step["execute_query"]
                        if isinstance(execute_result, dict) and "result" in execute_result:
                            logger.info("Query executed successfully")

                    if "generate_answer" in step:
                        answer_result = step["generate_answer"]
                        if isinstance(answer_result, dict) and "answer" in answer_result:
                            final_answer = answer_result["answer"]

            try:
                config = {"configurable": {"thread_id": request.thread_id}}
                final_state = chain_qa.graph_with_approval.get_state(config)
                if final_state and hasattr(final_state, 'values'):
                    state_values = final_state.values
                    executed_query = state_values.get("query")
            except Exception as state_error:
                logger.warning(f"Could not get final state: {state_error}")

            return schemas.ApprovalResponse(
                thread_id=request.thread_id,
                status="completed",
                query=executed_query,
                answer=final_answer,
                message="Query executed successfully and answer generated",
                success=True
            )

        elif request.action == "reject":
            return schemas.ApprovalResponse(
                thread_id=request.thread_id,
                status="rejected",
                message="Query execution was rejected by user",
                success=True
            )

        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid action. Use 'start', 'approve', or 'reject'"
            )

    except Exception as e:
        logger.error(f"Error in approval workflow: {e}")
        return schemas.ApprovalResponse(
            thread_id=request.thread_id,
            status="error",
            message=f"Error in approval workflow: {str(e)}",
            success=False,
            error=str(e)
        )


@router.post("/agent/ask", response_model=schemas.AgentAnswerResponse)
def ask_question_agent(request: schemas.QuestionRequest):
    """
    Ask question using Agent approach (can make multiple queries)
    """
    try:
        agent_qa = get_agent_qa()
        result = agent_qa.run(request.question)

        return schemas.AgentAnswerResponse(
            question=result["question"],
            answer=result["answer"],
            success=result["success"],
            approach="agent",
            error=result.get("error"),
            query=result.get("query"),
            available_tools=agent_qa.get_available_tools()
        )
    except Exception as e:
        logger.error(f"Error in agent QA: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/agent/ask-streaming")
def ask_question_agent_streaming(request: schemas.QuestionRequest):
    """
    Ask question using Agent approach with streaming
    """
    def generate_stream():
        try:
            agent_qa = get_agent_qa()
            step_count = 0

            for step in agent_qa.run_streaming(request.question):
                step_count += 1

                try:

                    step_data = {
                        "step_number": step_count,
                        "timestamp": None,
                    }

                    if "messages" in step and len(step["messages"]) > 0:
                        last_message = step["messages"][-1]
                        step_data.update({
                            "message": serialize_message(last_message),
                            "total_messages": len(step["messages"])
                        })

                        logger.info(
                            f"Streaming step {step_count}: {step_data['message']['type']}")

                    if "error" in step:
                        step_data["error"] = step["error"]

                    if "success" in step:
                        step_data["success"] = step["success"]

                    yield f"data: {json.dumps(step_data)}\n\n"

                except Exception as serialize_error:
                    logger.error(
                        f"Error serializing step {step_count}: {serialize_error}")
                    error_data = {
                        "step_number": step_count,
                        "error": f"Serialization error: {str(serialize_error)}",
                        "step_type": str(type(step))
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"

            yield f"data: {json.dumps({'status': 'complete', 'total_steps': step_count})}\n\n"

        except Exception as e:
            logger.error(f"Error in streaming agent QA: {e}")
            yield f"data: {json.dumps({'error': str(e), 'status': 'failed'})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={"Content-Type": "text/event-stream"}
    )


@router.post("/agent/ask-with-vector-search", response_model=schemas.AgentAnswerResponse)
def ask_question_agent_with_vector_search(request: schemas.VectorSearchRequest):
    """
    Ask question using Agent approach with vector search for high-cardinality columns
    """
    try:
        db = get_db_connection()
        agent_qa = SQLAgentQA(
            database=db,
            enable_vector_search=True,
            openai_api_key=request.openai_api_key
        )

        result = agent_qa.run(request.question)

        return schemas.AgentAnswerResponse(
            question=result["question"],
            answer=result["answer"],
            success=result["success"],
            approach="agent_with_vector_search",
            error=result.get("error"),
            available_tools=agent_qa.get_available_tools()
        )
    except Exception as e:
        logger.error(f"Error in agent QA with vector search: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/agent/test-vector-search", response_model=schemas.VectorSearchTestResponse)
def test_vector_search(request: schemas.VectorSearchTestRequest):
    """
    Test vector search functionality
    """
    try:
        db = get_db_connection()
        agent_qa = SQLAgentQA(
            database=db,
            enable_vector_search=True,
            openai_api_key=request.openai_api_key
        )

        results = agent_qa.test_vector_search(request.query)

        return schemas.VectorSearchTestResponse(
            query=request.query,
            results=results,
            success=True
        )
    except Exception as e:
        logger.error(f"Error testing vector search: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/schema", response_model=schemas.SchemaResponse)
def get_database_schema():
    """
    Get database schema information
    """
    try:
        from app.services.database import get_table_info

        db = get_db_connection()
        schema_info = get_table_info()

        sample_data = {}
        for table in schema_info["tables"]:
            try:
                result = db.run(f"SELECT * FROM {table} LIMIT 3")
                sample_data[table] = result
            except Exception as e:
                logger.warning(
                    f"Could not get sample data for table {table}: {e}")
                sample_data[table] = f"Error: {str(e)}"

        return schemas.SchemaResponse(
            tables=schema_info["tables"],
            schema=str(schema_info["schema"]),
            sample_data=sample_data,
            success=True
        )
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        return schemas.SchemaResponse(
            tables=[],
            schema=f"Error retrieving schema: {str(e)}",
            sample_data={},
            success=False
        )


@router.get("/graph-visualization")
def get_chain_graph_visualization():
    """
    Get mermaid visualization of the chain graph
    """
    try:
        chain_qa = get_chain_qa()
        graph_png = chain_qa.get_graph_visualization()

        if graph_png:
            return StreamingResponse(
                io.BytesIO(graph_png),
                media_type="image/png"
            )
        else:
            raise HTTPException(
                status_code=500, detail="Could not generate graph visualization")

    except Exception as e:
        logger.error(f"Error getting graph visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/compare", response_model=schemas.ComparisonResponse)
def compare_approaches(request: schemas.QuestionRequest):
    """
    Compare Chain vs Agent approaches for the same question
    """
    try:
        chain_qa = get_chain_qa()
        agent_qa = get_agent_qa()

        chain_result = chain_qa.run(request.question)

        agent_result = agent_qa.run(request.question)

        return schemas.ComparisonResponse(
            question=request.question,
            chain_result={
                "query": chain_result.get("query"),
                "result": chain_result.get("result"),
                "answer": chain_result.get("answer"),
                "success": True
            },
            agent_result={
                "answer": agent_result.get("answer"),
                "success": agent_result.get("success"),
                "tools_used": agent_qa.get_available_tools()
            },
            success=True
        )
    except Exception as e:
        logger.error(f"Error comparing approaches: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/agent/describe-table", response_model=schemas.TableDescriptionResponse)
def describe_table(request: schemas.TableDescriptionRequest):
    """
    Use agent to describe a specific table
    """
    try:
        agent_qa = get_agent_qa()
        result = agent_qa.describe_table(request.table_name)

        return schemas.TableDescriptionResponse(
            table_name=request.table_name,
            description=result.get("answer"),
            success=result.get("success"),
            error=result.get("error")
        )
    except Exception as e:
        logger.error(f"Error describing table: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/health")
def health_check():
    """
    Health check endpoint
    """
    try:

        db = get_db_connection()
        db.run("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected",
            "chain_qa": "available",
            "agent_qa": "available"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
