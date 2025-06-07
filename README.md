# LangChain SQL QA API

This is a Question/Answering (QA) system built with FastAPI and LangChain. It allows you to ask natural language questions about a SQL database and get answers.

The system uses a Chinook-like music store database as its data source.

## Getting Started

### Prerequisites

* Python 3.11+
* `uv` package installer

### 1. Set Up a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies. Assuming you are in the project directory:

```bash
uv venv
```

### 2. Install Dependencies

Install all the required Python packages

```bash
uv sync
```

### 3. Run the API Server

Start the application using Uvicorn.

```bash
uv run -- uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The server is now running and accessible at `http://127.0.0.1:8000`. The `--reload` flag will automatically restart the server when you make code changes.

## How to Use the API

Once the server is running, you can interact with the API endpoints.

### 1. Interactive API Docs (Recommended)

The easiest way to explore and test the API is through the interactive Swagger documentation. Open your browser and go to:

`http://127.0.0.1:8000/docs`

Here you can see all available endpoints, their parameters, and execute them directly from the web interface.

### 2. Using `curl` from the Terminal

You can also interact with the API using a command-line tool like `curl`.

#### Get Example Questions

To see a list of questions you can try, send a GET request to the `/examples` endpoint.

```bash
curl http://127.0.0.1:8000/api/v1/examples
```

#### Ask a Simple Question (Chain)

For straightforward questions, use the `/chain/ask` endpoint. This endpoint expects a `POST` request with a JSON body.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chain/ask \
-H "Content-Type: application/json" \
-d '{"question": "How many employees are there?"}'
```

#### Ask a Complex Question (Agent)

For more complex questions that might require multiple steps, use the `/agent/ask` endpoint.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/agent/ask \
-H "Content-Type: application/json" \
-d '{"question": "Show me the top 5 artists by total sales revenue"}'
```

#### Ask a Question with a Proper Noun (Agent with Vector Search)

For questions containing specific names, use the `/agent/ask-with-vector-search` endpoint for better accuracy.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/agent/ask-with-vector-search \
-H "Content-Type: application/json" \
-d '{"question": "How many albums does Alice in Chains have?"}'
```