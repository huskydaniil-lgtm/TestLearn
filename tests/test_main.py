import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add the parent directory to sys.path so we can import main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from main import app

client = TestClient(app)


def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "TestLearn" in response.text


def test_api_categories():
    response = client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # We expect at least one category from the seed data
    assert len(data) > 0
    # Check structure of first category
    first = data[0]
    assert "id" in first
    assert "name" in first
    assert "description" in first


def test_api_quizzes():
    """Test quizzes endpoint."""
    response = client.get("/api/quizzes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_api_glossary():
    """Test glossary endpoint."""
    response = client.get("/api/glossary")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_api_feedback():
    """Test feedback endpoint."""
    response = client.post(
        "/api/feedback",
        data={"name": "Test User", "message": "Test message"}
    )
    assert response.status_code == 200


def test_auth_login_failure():
    """Test login with invalid credentials."""
    response = client.post(
        "/api/auth/login",
        json={"username": "invalid", "password": "invalid"}
    )
    assert response.status_code == 401


def test_gamification_leaderboard():
    """Test leaderboard endpoint."""
    response = client.get("/api/gamification/leaderboard")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_gamification_achievements():
    """Test achievements endpoint."""
    response = client.get("/api/gamification/achievements")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)