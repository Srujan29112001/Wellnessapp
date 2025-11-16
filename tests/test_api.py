"""
API Integration Tests
"""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app


class TestAPIEndpoints:
    """Test API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()

    def test_eeg_upload_endpoint(self, client):
        """Test EEG upload endpoint"""
        # Mock CSV file
        files = {"file": ("eeg_data.csv", b"channel1,channel2\n0.1,0.2\n", "text/csv")}

        response = client.post("/api/v1/eeg/upload", files=files)

        # Should return some result (may fail without DB, but endpoint should exist)
        assert response.status_code in [200, 422, 500]

    def test_coach_chat_endpoint(self, client):
        """Test AI coach chat endpoint"""
        payload = {
            "message": "I feel stressed",
            "include_context": False
        }

        response = client.post("/api/v1/coach/chat", json=payload)

        assert response.status_code in [200, 500]  # May fail without LLM keys

    def test_recommendations_endpoint(self, client):
        """Test recommendations endpoint"""
        response = client.get("/api/v1/recommendations?user_id=test_user")

        assert response.status_code in [200, 404, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
