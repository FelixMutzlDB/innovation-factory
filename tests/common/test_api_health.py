"""Test common API endpoints."""
import pytest


class TestHealthEndpoints:
    def test_version_endpoint(self, client):
        resp = client.get("/api/version")
        assert resp.status_code == 200
        data = resp.json()
        assert "app_name" in data or "version" in data

    def test_projects_list(self, client):
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_docs_list(self, client):
        resp = client.get("/api/docs/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert "slugs" in data

    def test_docs_get_nonexistent(self, client):
        resp = client.get("/api/docs/projects/nonexistent")
        assert resp.status_code == 404


class TestIdeaEndpoints:
    def test_create_idea_session(self, client):
        resp = client.post("/api/ideas/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "collecting_name"
        assert data["id"] is not None

    def test_idea_session_flow(self, client):
        # Create session
        resp = client.post("/api/ideas/sessions")
        session_id = resp.json()["id"]

        # Send company name
        resp = client.post(
            f"/api/ideas/sessions/{session_id}/chat",
            json={"content": "TestCorp"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "collecting_description"

        # Send description (uses fallback since no real endpoint in tests)
        resp = client.post(
            f"/api/ideas/sessions/{session_id}/chat",
            json={"content": "A test application"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert "generated_prompt" in data
        assert len(data["generated_prompt"]) > 50

    def test_get_idea_messages(self, client):
        resp = client.post("/api/ideas/sessions")
        session_id = resp.json()["id"]
        resp = client.get(f"/api/ideas/sessions/{session_id}/messages")
        assert resp.status_code == 200
        messages = resp.json()
        assert len(messages) >= 1  # Welcome message
