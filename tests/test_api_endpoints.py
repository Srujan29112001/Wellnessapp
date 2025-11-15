"""
Tests for API Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import io

from backend.api.main import app


client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_check(self):
        """Test /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_login_success(self):
        """Test successful login"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "demo@wellnessai.com",
                "password": "demo123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_failure(self):
        """Test login with wrong credentials"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "wrong@example.com",
                "password": "wrongpass"
            }
        )

        assert response.status_code == 401

    def test_register(self):
        """Test user registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "name": "New User"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data


class TestCoachEndpoints:
    """Test AI coach endpoints"""

    def test_chat_with_coach(self):
        """Test chat endpoint"""
        response = client.post(
            "/api/coach/chat",
            json={
                "message": "I'm feeling stressed",
                "include_context": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert isinstance(data["message"], str)
        assert len(data["message"]) > 0

    def test_guided_session(self):
        """Test guided session endpoint"""
        response = client.post(
            "/api/coach/session/start",
            json={
                "session_type": "breathing",
                "duration_minutes": 5
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "instructions" in data
        assert isinstance(data["instructions"], list)


class TestUserEndpoints:
    """Test user management endpoints"""

    def test_get_current_user(self):
        """Test getting current user profile"""
        response = client.get("/api/users/me")

        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "name" in data

    def test_get_user_preferences(self):
        """Test getting user preferences"""
        response = client.get("/api/users/preferences")

        assert response.status_code == 200
        data = response.json()
        assert "notification_preferences" in data


class TestVoiceEndpoints:
    """Test voice analysis endpoints"""

    def test_voice_analysis_with_file(self):
        """Test voice analysis with audio file"""
        # Create a dummy audio file (would need a real WAV file for full test)
        # For now, just test the endpoint structure

        # This would be a real audio file in production tests
        # files = {"file": ("test.wav", audio_bytes, "audio/wav")}
        # response = client.post("/api/voice/analyze", files=files)

        # For demo, skip if no test file
        pytest.skip("Audio file needed for full test")


class TestFoodEndpoints:
    """Test food recognition endpoints"""

    def test_food_recognition(self):
        """Test food recognition endpoint structure"""
        # Would need a real image file for full test
        pytest.skip("Image file needed for full test")


class TestEEGEndpoints:
    """Test EEG analysis endpoints"""

    def test_eeg_analysis_with_file(self):
        """Test EEG analysis with CSV file"""
        # Check if sample file exists
        sample_file = Path("/home/user/Wellnessapp/data/sample_eeg/eeg_sample_relaxed.csv")

        if not sample_file.exists():
            pytest.skip("Sample EEG file not found")

        with open(sample_file, "rb") as f:
            files = {"file": ("eeg_sample.csv", f, "text/csv")}
            response = client.post("/api/eeg/analyze", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "mental_state" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
