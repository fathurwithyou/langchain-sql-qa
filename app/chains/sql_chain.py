import logging
from collections.abc import Generator
from typing import Any

from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph

from app.chains.models import QueryOutput, State
from app.core.config import settings
from app.core.exceptions import QueryProcessingError

logger = logging.getLogger(__name__)


class SQLChainQA:
    """
    Chain-based SQL QA system following LangChain tutorial
    Uses a predictable sequence: question -> SQL -> execute -> answer
    """

    def __init__(self, database: SQLDatabase, llm: ChatGoogleGenerativeAI = None):
        self.db = database
        self.llm = llm or ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            api_key=settings.GEMINI_API_KEY,
        )
        self._setup_prompts()
        self._setup_graph()

    def _setup_prompts(self):
        """Setup prompts for the chain"""

        system_message = """
        Given an input question, create a syntactically correct {dialect} query to
        run to help find the answer. Unless the user specifies in his question a
        specific number of examples they wish to obtain, always limit your query to
        at most {top_k} results. You can order the results by a relevant column to
        return the most interesting examples in the database.

        Never query for all the columns from a specific table, only ask for a the
        few relevant columns given the question.

        Pay attention to use only the column names that you can see in the schema
        description. Be careful to not query for columns that do not exist. Also,
        pay attention to which column is in which table.

        Only use the following tables:
        {table_info}
        """

        user_prompt = "Question: {input}"

        self.query_prompt_template = ChatPromptTemplate(
            [("system", system_message), ("user", user_prompt)]
        )

    def write_query(self, state: State) -> dict[str, str]:
        """Generate SQL query to fetch information."""
        try:
            prompt = self.query_prompt_template.invoke(
                {
                    "dialect": self.db.dialect,
                    "top_k": 10,
                    "table_info": self.db.get_table_info(),
                    "input": state["question"],
                }
            )

            structured_llm = self.llm.with_structured_output(QueryOutput)
            result = structured_llm.invoke(prompt)

            logger.info(f"Generated SQL query: {result['query']}")
            return {"query": result["query"]}

        except Exception as e:
            logger.error(f"Error generating SQL query: {e}")
            raise QueryProcessingError(f"Failed to generate SQL query: {str(e)}") from e

    def execute_query(self, state: State) -> dict[str, str]:
        """Execute SQL query."""
        try:
            execute_query_tool = QuerySQLDatabaseTool(db=self.db)
            result = execute_query_tool.invoke(state["query"])

            logger.info(
                f"Query executed successfully. Result length: {len(str(result))}"
            )
            return {"result": result}

        except Exception as e:
            logger.error(f"Error executing SQL query: {e}")
            raise QueryProcessingError(f"Failed to execute SQL query: {str(e)}") from e

    def generate_answer(self, state: State) -> dict[str, str]:
        """Answer question using retrieved information as context."""
        try:
            prompt = (
                "Given the following user question, corresponding SQL query, "
                "and SQL result, answer the user question.\n\n"
                f"Question: {state['question']}\n"
                f"SQL Query: {state['query']}\n"
                f"SQL Result: {state['result']}"
            )

            response = self.llm.invoke(prompt)

            logger.info("Answer generated successfully")
            return {"answer": response.content}

        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise QueryProcessingError(f"Failed to generate answer: {str(e)}") from e

    def _setup_graph(self):
        """Setup LangGraph for orchestrating the chain"""

        graph_builder = StateGraph(State).add_sequence(
            [self.write_query, self.execute_query, self.generate_answer]
        )
        graph_builder.add_edge(START, "write_query")

        self.graph = graph_builder.compile()

        memory = MemorySaver()
        self.graph_with_approval = graph_builder.compile(
            checkpointer=memory, interrupt_before=["execute_query"]
        )

    def run(self, question: str, stream: bool = False) -> dict[str, Any]:
        """
        Run the complete chain

        Args:
            question: User question
            stream: Whether to stream intermediate results

        Returns:
            Final state with question, query, result, and answer
        """
        try:
            if stream:
                steps = []
                for step in self.graph.stream(
                    {"question": question}, stream_mode="updates"
                ):
                    steps.append(step)
                    logger.info(f"Chain step: {step}")

                final_state = self.graph.get_state(
                    self.graph.stream({"question": question}).__next__()
                )
                return final_state.values
            else:
                result = self.graph.invoke({"question": question})
                return result

        except Exception as e:
            logger.error(f"Error running chain: {e}")
            raise QueryProcessingError(f"Chain execution failed: {str(e)}") from e

    def run_with_approval(
        self, question: str, thread_id: str = "1"
    ) -> Generator[Any, None, None]:
        """
        Run chain with human-in-the-loop approval before query execution

        Args:
            question: User question
            thread_id: Thread ID for state persistence

        Returns:
            Generator that yields steps and waits for approval
        """
        config = {"configurable": {"thread_id": thread_id}}

        try:
            for step in self.graph_with_approval.stream(
                {"question": question},
                config,
                stream_mode="updates",
            ):
                logger.info(f"Approval workflow step: {step}")
                yield step

            try:
                current_state = self.graph_with_approval.get_state(config)
                if current_state and hasattr(current_state, "values"):
                    state_values = current_state.values
                    logger.info(f"Current state values: {state_values}")

                    yield {
                        "approval_required": True,
                        "query": state_values.get("query"),
                        "state": "awaiting_approval",
                        "message": "Query generated and ready for approval",
                    }
                else:
                    logger.warning("Could not get current state for approval")
                    yield {
                        "approval_required": True,
                        "query": None,
                        "error": "Could not retrieve generated query",
                    }
            except Exception as state_error:
                logger.error(f"Error getting state for approval: {state_error}")
                yield {
                    "approval_required": True,
                    "query": None,
                    "error": f"State retrieval failed: {str(state_error)}",
                }

        except Exception as e:
            logger.error(f"Error in approval workflow: {e}")
            yield {
                "error": str(e),
                "status": "failed",
                "message": "Approval workflow failed",
            }

    def continue_after_approval(self, thread_id: str = "1") -> dict[str, Any]:
        """Continue execution after approval"""
        config = {"configurable": {"thread_id": thread_id}}

        try:
            steps = []
            for step in self.graph_with_approval.stream(
                None, config, stream_mode="updates"
            ):
                steps.append(step)
                logger.info(f"Post-approval step: {step}")

            return steps

        except Exception as e:
            logger.error(f"Error continuing after approval: {e}")
            raise QueryProcessingError(
                f"Post-approval execution failed: {str(e)}"
            ) from e

    def get_graph_visualization(self) -> bytes:
        """Get mermaid visualization of the graph"""
        try:
            return self.graph.get_graph().draw_mermaid_png()
        except Exception as e:
            logger.warning(f"Could not generate graph visualization: {e}")
            return None
