from fastapi import status


class TestChainApprovalAPI:
    """Test chain human-in-the-loop approval functionality"""

    def test_chain_approval_start_workflow(self, client):
        """Test starting approval workflow"""
        question = "How many customers are from each country?"

        response = client.post(
            "/api/v1/chain/ask-with-approval",
            json={
                "question": question,
                "action": "start",
                "thread_id": "test_thread_1"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "thread_id" in data
        assert "status" in data
        assert "query" in data
        assert "message" in data
        assert "success" in data

        assert data["thread_id"] == "test_thread_1"
        assert data["status"] == "awaiting_approval"
        assert data["success"] is True
        assert data["query"] is not None

    def test_chain_approval_approve_workflow(self, client):
        """Test approving a query in workflow"""

        start_response = client.post(
            "/api/v1/chain/ask-with-approval",
            json={
                "question": "How many employees are there?",
                "action": "start",
                "thread_id": "test_thread_2"
            }
        )
        assert start_response.status_code == status.HTTP_200_OK

        approve_response = client.post(
            "/api/v1/chain/ask-with-approval",
            json={
                "question": "",
                "action": "approve",
                "thread_id": "test_thread_2"
            }
        )

        assert approve_response.status_code == status.HTTP_200_OK
        data = approve_response.json()

        assert data["status"] == "completed"
        assert data["success"] is True
        assert "answer" in data

    def test_chain_approval_reject_workflow(self, client):
        """Test rejecting a query in workflow"""

        start_response = client.post(
            "/api/v1/chain/ask-with-approval",
            json={
                "question": "Show me all customer data",
                "action": "start",
                "thread_id": "test_thread_3"
            }
        )
        assert start_response.status_code == status.HTTP_200_OK

        reject_response = client.post(
            "/api/v1/chain/ask-with-approval",
            json={
                "question": "",
                "action": "reject",
                "thread_id": "test_thread_3"
            }
        )

        assert reject_response.status_code == status.HTTP_200_OK
        data = reject_response.json()

        assert data["status"] == "rejected"
        assert data["success"] is True
        assert "rejected" in data["message"].lower()

    def test_chain_approval_invalid_action(self, client):
        """Test invalid action in approval workflow"""
        response = client.post(
            "/api/v1/chain/ask-with-approval",
            json={
                "question": "Test question",
                "action": "invalid_action",
                "thread_id": "test_thread_4"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_data = response.json()

        assert "detail" in response_data

        error_detail = str(response_data["detail"])
        assert "invalid_action" in error_detail or "start" in error_detail
