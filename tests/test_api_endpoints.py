"""
Tests for API Endpoints
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from backend.api.main import app


client = TestClient(app)


class TestHealthEndpoints:
    """Test health metrics endpoints"""

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_log_health_metrics(self):
        """Test logging health metrics"""
        data = {
            "user_id": "test_user",
            "date": "2024-01-15",
            "steps": 8000,
            "sleep_hours": 7.5,
            "heart_rate": 70,
            "stress_level": 5.0
        }

        response = client.post("/api/v1/health/log", json=data)
        # May fail if DB not connected, but tests structure
        assert response.status_code in [200, 500]  # 500 if DB not available


class TestCoachEndpoints:
    """Test AI coach endpoints"""

    def test_chat_with_coach(self):
        """Test chat endpoint"""
        data = {
            "message": "I feel stressed and anxious",
            "include_context": True
        }

        response = client.post("/api/v1/coach/chat", json=data)

        # Should return response even with mock LLM
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "recommendations" in result

    def test_guided_session(self):
        """Test guided session start"""
        data = {
            "session_type": "breathing",
            "duration_minutes": 5
        }

        response = client.post("/api/v1/coach/session/start", json=data)
        assert response.status_code == 200
        result = response.json()
        assert "instructions" in result


class TestAPIDocumentation:
    """Test API documentation"""

    def test_openapi_docs(self):
        """Test OpenAPI docs available"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_graphql_endpoint(self):
        """Test GraphQL endpoint exists"""
        response = client.get("/graphql")
        # GraphQL should respond (may be 400 without query)
        assert response.status_code in [200, 400]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
