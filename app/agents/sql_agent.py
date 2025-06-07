import ast
import logging
import re
from typing import Any

from langchain.tools.retriever import create_retriever_tool
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import OpenAIEmbeddings
from langgraph.prebuilt import create_react_agent

from app.core.config import settings
from app.core.exceptions import QueryProcessingError

logger = logging.getLogger(__name__)


def query_as_list(db: SQLDatabase, query: str) -> list[str]:
    """
    Parse SQL query result into a list of unique elements
    Used for extracting proper nouns from database
    """
    try:
        res = db.run(query)
        res = [el for sub in ast.literal_eval(res) for el in sub if el]
        res = [re.sub(r"\b\d+\b", "", string).strip() for string in res]
        return list(set(res))
    except Exception as e:
        logger.warning(f"Error parsing query result: {e}")
        return []


class SQLAgentQA:
    """
    Agent-based SQL QA system with advanced capabilities:
    - Can query database multiple times
    - Can recover from errors
    - Can handle high-cardinality columns with vector search
    - Can describe schema and table contents
    """

    def __init__(self,
                 database: SQLDatabase,
                 llm: ChatGoogleGenerativeAI = None,
                 enable_vector_search: bool = True,
                 openai_api_key: str | None = None):
        self.db = database
        self.llm = llm or ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            api_key=settings.GEMINI_API_KEY,
        )
        self.enable_vector_search = enable_vector_search
        self.openai_api_key = openai_api_key

        self._setup_tools()
        self._setup_system_prompt()
        self._setup_agent()

    def _setup_tools(self):
        """Setup SQL database tools and optional vector search"""

        toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.tools = toolkit.get_tools()

        if self.enable_vector_search and self.openai_api_key:
            try:
                self._setup_vector_search()
            except Exception as e:
                logger.warning(f"Could not setup vector search: {e}")
                self.enable_vector_search = False

    def _setup_vector_search(self):
        """Setup vector search for proper nouns (high-cardinality columns)"""
        try:

            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-large",
                api_key=self.openai_api_key
            )

            vector_store = InMemoryVectorStore(embeddings)

            artists = query_as_list(self.db, "SELECT Name FROM Artist")
            albums = query_as_list(self.db, "SELECT Title FROM Album")

            proper_nouns = artists + albums

            if proper_nouns:

                vector_store.add_texts(proper_nouns)

                retriever = vector_store.as_retriever(search_kwargs={"k": 5})

                description = (
                    "Use to look up values to filter on. Input is an approximate spelling "
                    "of the proper noun, output is valid proper nouns. Use the noun most "
                    "similar to the search."
                )

                retriever_tool = create_retriever_tool(
                    retriever,
                    name="search_proper_nouns",
                    description=description,
                )

                self.tools.append(retriever_tool)
                logger.info(
                    f"Vector search enabled with {len(proper_nouns)} proper nouns")
            else:
                logger.warning("No proper nouns found for vector search")
                self.enable_vector_search = False

        except Exception as e:
            logger.error(f"Error setting up vector search: {e}")
            self.enable_vector_search = False

    def _setup_system_prompt(self):
        """Setup system prompt for the agent"""
        base_system_message = """
        You are an agent designed to interact with a SQL database.
        Given an input question, create a syntactically correct {dialect} query to run,
        then look at the results of the query and return the answer. Unless the user
        specifies a specific number of examples they wish to obtain, always limit your
        query to at most {top_k} results.

        You can order the results by a relevant column to return the most interesting
        examples in the database. Never query for all the columns from a specific table,
        only ask for the relevant columns given the question.

        You MUST double check your query before executing it. If you get an error while
        executing a query, rewrite the query and try again.

        DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
        database.

        To start you should ALWAYS look at the tables in the database to see what you
        can query. Do NOT skip this step.

        Then you should query the schema of the most relevant tables.
        """.format(  # noqa: UP032
            dialect=self.db.dialect,
            top_k=5,
        )

        if self.enable_vector_search:
            vector_search_suffix = (
                "\n\nIf you need to filter on a proper noun like a Name, you must ALWAYS first look up "
                "the filter value using the 'search_proper_nouns' tool! Do not try to "
                "guess at the proper name - use this function to find similar ones."
            )
            self.system_message = base_system_message + vector_search_suffix
        else:
            self.system_message = base_system_message

    def _setup_agent(self):
        """Setup the ReAct agent"""
        try:
            self.agent = create_react_agent(
                self.llm,
                self.tools,
                prompt=self.system_message
            )
            logger.info("SQL Agent initialized successfully")
        except Exception as e:
            logger.error(f"Error setting up agent: {e}")
            raise QueryProcessingError(f"Failed to setup agent: {str(e)}") from e

    def run(self, question: str, stream: bool = False) -> dict[str, Any]:
        """
        Run the agent to answer a question

        Args:
            question: User question
            stream: Whether to stream intermediate steps

        Returns:
            Dictionary with the answer and metadata
        """
        try:
            if stream:
                steps = []
                for step in self.agent.stream(
                    {"messages": [{"role": "user", "content": question}]},
                    stream_mode="values",
                ):
                    steps.append(step)
                    if "messages" in step and len(step["messages"]) > 0:
                        last_message = step["messages"][-1]
                        logger.info(
                            f"Agent step: {last_message.type if hasattr(last_message, 'type') else 'message'}")

                final_answer = steps[-1]["messages"][-1].content if steps else "No answer generated"

                return {
                    "question": question,
                    "answer": final_answer,
                    "steps": steps,
                    "success": True
                }
            else:

                result = self.agent.invoke(
                    {"messages": [{"role": "user", "content": question}]}
                )

                final_answer = result["messages"][-1].content

                return {
                    "question": question,
                    "answer": final_answer,
                    "success": True
                }

        except Exception as e:
            logger.error(f"Error running agent: {e}")
            return {
                "question": question,
                "answer": f"I encountered an error: {str(e)}",
                "success": False,
                "error": str(e)
            }

    def run_streaming(self, question: str):
        """
        Generator that yields streaming steps from the agent

        Args:
            question: User question

        Yields:
            Individual steps from the agent execution
        """
        try:
            yield from self.agent.stream(
                {"messages": [{"role": "user", "content": question}]},
                stream_mode="values",
            )

        except Exception as e:
            logger.error(f"Error in streaming execution: {e}")
            yield {
                "error": str(e),
                "success": False
            }

    def describe_table(self, table_name: str) -> dict[str, Any]:
        """
        Use the agent to describe a specific table

        Args:
            table_name: Name of the table to describe

        Returns:
            Dictionary with table description
        """
        question = f"Describe the {table_name} table"
        return self.run(question)

    def get_available_tools(self) -> list[str]:
        """Get list of available tools"""
        return [tool.name for tool in self.tools]

    def test_vector_search(self, query: str) -> list[str]:
        """
        Test vector search functionality

        Args:
            query: Search query

        Returns:
            List of similar proper nouns
        """
        if not self.enable_vector_search:
            return ["Vector search not enabled"]

        try:

            retriever_tool = None
            for tool in self.tools:
                if hasattr(tool, 'name') and tool.name == "search_proper_nouns":
                    retriever_tool = tool
                    break

            if retriever_tool:
                result = retriever_tool.invoke(query)
                return result.split('\n') if isinstance(result, str) else [str(result)]
            else:
                return ["Retriever tool not found"]

        except Exception as e:
            logger.error(f"Error testing vector search: {e}")
            return [f"Error: {str(e)}"]
