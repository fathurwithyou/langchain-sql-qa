from unittest.mock import patch
import time
from fastapi import status

class TestChainErrorHandling:
    """Test chain API error handling"""

    @patch('app.chains.sql_chain.SQLChainQA.run')
    def test_chain_ask_internal_error(self, mock_run, client):
        """Test handling of internal errors in chain"""

        mock_run.side_effect = Exception("Simulated internal error")

        response = client.post(
            "/api/v1/chain/ask",
            json={"question": "How many artists are there?"}
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data

    def test_chain_ask_very_long_question(self, client):
        """Test handling of very long questions"""
        long_question = "How many " + "very " * 100 + "long question about employees?"

        response = client.post(
            "/api/v1/chain/ask",
            json={"question": long_question}
        )

        assert response.status_code in [
            status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

        time.sleep(3)