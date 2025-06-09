import time

import pytest
from fastapi import status


class TestChainPerformance:
    """Test chain API performance"""

    def test_chain_ask_response_time(self, client):
        """Test that chain responses are reasonably fast"""
        question = "How many tracks are there?"

        start_time = time.time()
        response = client.post(
            "/api/v1/chain/ask",
            json={"question": question}
        )
        end_time = time.time()

        assert response.status_code == status.HTTP_200_OK
        response_time = end_time - start_time

        assert response_time < 60.0

        time.sleep(3)

    @pytest.mark.slow
    def test_chain_concurrent_requests(self, client, sample_questions):
        """Test handling of concurrent requests - marked as slow test"""
        import queue
        import threading

        results = queue.Queue()
        questions = sample_questions["simple"][:2]

        def make_request(question, delay_before=0):

            time.sleep(delay_before)
            response = client.post(
                "/api/v1/chain/ask",
                json={"question": question}
            )
            results.put((question, response.status_code, response.json()))

        threads = []
        for i, question in enumerate(questions):

            thread = threading.Thread(
                target=make_request, args=(question, i * 2))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert results.qsize() == len(questions)
        while not results.empty():
            question, status_code, data = results.get()
            assert status_code == status.HTTP_200_OK
            assert data["success"] is True

        time.sleep(5)
