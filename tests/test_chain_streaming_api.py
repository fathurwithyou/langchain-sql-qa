from fastapi import status

class TestChainStreamingAPI:
    """Test chain streaming API functionality"""

    def test_chain_streaming_basic(self, client, sample_questions):
        """Test basic chain streaming"""
        question = sample_questions["simple"][1]

        response = client.post(
            "/api/v1/chain/ask-streaming",
            json={"question": question}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/event-stream"

        content = response.text
        assert "data:" in content
        assert "write_query" in content or "execute_query" in content or "generate_answer" in content

    def test_chain_streaming_contains_steps(self, client):
        """Test that streaming response contains expected steps"""
        question = "How many genres are there?"

        response = client.post(
            "/api/v1/chain/ask-streaming",
            json={"question": question}
        )

        assert response.status_code == status.HTTP_200_OK
        content = response.text

        expected_steps = ["write_query", "execute_query", "generate_answer"]
        for step in expected_steps:

            assert any(step in line for line in content.split('\n'))
