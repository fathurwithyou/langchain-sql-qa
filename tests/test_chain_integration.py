from fastapi import status
import time

class TestChainIntegration:
    """Integration tests for chain API"""

    def test_chain_ask_database_integration(self, client):
        """Test that chain actually queries the database"""
        question = "How many albums does AC/DC have?"

        response = client.post(
            "/api/v1/chain/ask",
            json={"question": question}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        query = data["query"].lower()
        assert "ac/dc" in query or "artist" in query

        answer = data["answer"].lower()
        assert any(word in answer for word in [
                   "album", "ac/dc", "number", "have"])

        time.sleep(3)

    def test_chain_ask_join_query_integration(self, client):
        """Test chain with join queries"""
        question = "Which country's customers spent the most?"

        response = client.post(
            "/api/v1/chain/ask",
            json={"question": question}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        query_upper = data["query"].upper()
        assert "JOIN" in query_upper or "INNER JOIN" in query_upper
        assert "CUSTOMER" in query_upper
        assert "INVOICE" in query_upper

        answer = data["answer"]
        assert len(answer) > 10

        time.sleep(3)

    def test_chain_ask_aggregation_integration(self, client):
        """Test chain with aggregation queries"""
        question = "What is the average price of tracks?"

        response = client.post(
            "/api/v1/chain/ask",
            json={"question": question}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        query_upper = data["query"].upper()
        assert "AVG" in query_upper or "AVERAGE" in query_upper
        assert "TRACK" in query_upper
        assert "PRICE" in query_upper or "UNITPRICE" in query_upper

        answer = data["answer"].lower()
        assert any(word in answer for word in [
                   "price", "cost", "average", "track"])

        time.sleep(3)