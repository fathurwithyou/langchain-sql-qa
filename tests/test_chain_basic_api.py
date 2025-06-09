import time

from fastapi import status


class TestChainBasicAPI:
    """Test basic chain API functionality"""

    def test_chain_ask_basic_question(self, client, sample_questions):
        """Test basic chain ask endpoint"""
        question = sample_questions["simple"][0]

        response = client.post(
            "/api/v1/chain/ask",
            json={"question": question}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "question" in data
        assert "query" in data
        assert "result" in data
        assert "answer" in data
        assert "success" in data
        assert "approach" in data

        assert data["question"] == question
        assert data["success"] is True
        assert data["approach"] == "chain"
        assert data["query"] is not None
        assert "SELECT" in data["query"].upper()
        assert "employee" in data["query"].lower()

        time.sleep(2)

    def test_chain_ask_multiple_questions(self, client, sample_questions):
        """Test chain ask with multiple different questions"""
        for _, questions in sample_questions.items():
            for i, question in enumerate(questions[:2]):
                response = client.post(
                    "/api/v1/chain/ask",
                    json={"question": question}
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["success"] is True
                assert data["question"] == question
                assert data["query"] is not None

                time.sleep(2 + i * 0.5)

    def test_chain_ask_invalid_input(self, client):
        """Test chain ask with invalid input"""

        response = client.post(
            "/api/v1/chain/ask",
            json={"question": ""}
        )

        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_500_INTERNAL_SERVER_ERROR]

        response = client.post(
            "/api/v1/chain/ask",
            json={}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        response = client.post(
            "/api/v1/chain/ask",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_chain_ask_sql_injection_prevention(self, client):
        """Test that chain approach prevents SQL injection"""
        malicious_questions = [
            "'; DROP TABLE Artist; --",
            "How many employees'; DELETE FROM Employee; --",
            "Show me users WHERE 1=1; UPDATE Customer SET Email='hacked@test.com'; --"
        ]

        for _, question in enumerate(malicious_questions):
            response = client.post(
                "/api/v1/chain/ask",
                json={"question": question}
            )

            if response.status_code == status.HTTP_200_OK:
                data = response.json()

                if data.get("query"):
                    query_upper = data["query"].upper()
                    assert "DROP" not in query_upper
                    assert "DELETE" not in query_upper
                    assert "UPDATE" not in query_upper

            time.sleep(3)
