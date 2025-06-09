import os
import shutil
import tempfile

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.database import setup_database


@pytest.fixture(scope="session")
def test_database():
    """Create a temporary test database"""

    temp_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(temp_dir, "test_chinook_qa.db")

    original_uri = settings.DATABASE_URI
    settings.DATABASE_URI = f"sqlite:///./data/{test_db_path}"

    setup_database()

    yield test_db_path

    settings.DATABASE_URI = original_uri
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def client(test_database):
    """Create FastAPI test client with test database"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_questions():
    """Sample questions for testing"""
    return {
        "simple": [
            "How many employees are there?",
            "How many artists are in the database?",
            "What are the different genres available?"
        ],
        "join": [
            "Which country's customers spent the most?",
            "What are the names of all albums by AC/DC?",
            "Show me customers from Brazil"
        ],
        "aggregation": [
            "What is the average price of tracks?",
            "Which genre has the most tracks?",
            "What is the total revenue by country?"
        ],
        "complex": [
            "Show me the top 5 customers by total purchases",
            "List all tracks with their album and artist names",
            "Which employees support the most customers?"
        ],
        "schema": [
            "Describe the PlaylistTrack table",
            "What tables are available in the database?",
            "Show me the structure of the Invoice table"
        ]
    }


@pytest.fixture
def mock_api_keys(monkeypatch):
    """Mock API keys for testing"""
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key")


@pytest.fixture
def auth_headers():
    """Authentication headers for API requests"""
    return {"Content-Type": "application/json"}


@pytest.fixture(autouse=True)
def setup_test_config():
    """Setup test configuration"""

    settings.TESTING = True
    settings.LOG_LEVEL = "DEBUG"
    settings.RATE_LIMIT_ENABLED = False
