import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chatbot_suggestions():
    res = client.get("/api/chatbot/suggestions")
    assert res.status_code == 200
    suggestions = res.json()
    assert isinstance(suggestions, list)
    assert len(suggestions) >= 5
    assert "How does AI resume matching work?" in suggestions
    assert "How is the candidate score calculated?" in suggestions


def test_chatbot_scoring_question():
    res = client.post("/api/chatbot/chat", json={
        "message": "How is the candidate score calculated?"
    })
    assert res.status_code == 200
    data = res.json()
    assert "assistant_message" in data
    assert "conversation_id" in data
    msg = data["assistant_message"]
    assert "40%" in msg or "Technical" in msg
    assert "Semantic" in msg or "30%" in msg
    assert "Experience" in msg or "20%" in msg
    assert "Education" in msg or "10%" in msg


def test_chatbot_top_candidates():
    res = client.post("/api/chatbot/chat", json={
        "message": "Show me the top-ranked candidates."
    })
    assert res.status_code == 200
    data = res.json()
    assert "assistant_message" in data
    assert data["relevant_data"] is not None
    assert "top_candidates" in data["relevant_data"]


def test_chatbot_dashboard_overview():
    res = client.post("/api/chatbot/chat", json={
        "message": "Explain the recruitment dashboard."
    })
    assert res.status_code == 200
    data = res.json()
    msg = data["assistant_message"]
    assert "Active Job" in msg or "Jobs" in msg or "Resumes" in msg or "Dashboard" in msg


def test_chatbot_missing_skills():
    res = client.post("/api/chatbot/chat", json={
        "message": "What are the missing skills for a candidate?"
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["assistant_message"]) > 20


def test_chatbot_clear_conversation():
    cid = "test-conv-1234"
    client.post("/api/chatbot/chat", json={
        "message": "Hello",
        "conversation_id": cid
    })
    clear_res = client.post(f"/api/chatbot/clear/{cid}")
    assert clear_res.status_code == 200
    assert clear_res.json()["status"] == "cleared"


def test_chatbot_validation_empty_message():
    res = client.post("/api/chatbot/chat", json={
        "message": "   "
    })
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_chatbot_validation_oversized_message():
    long_msg = "A" * 2500
    res = client.post("/api/chatbot/chat", json={
        "message": long_msg
    })
    assert res.status_code in (400, 422)


def test_chatbot_dynamic_welcome_unauthenticated():
    res = client.get("/api/chatbot/welcome?page_context=/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "welcome_message" in data
    assert "mode" in data and data["mode"] == "dynamic"
    assert "stats" in data
    assert "total_jobs" in data["stats"]
    assert "total_candidates" in data["stats"]
    msg = data["welcome_message"]
    assert "Good" in msg or "Hello" in msg


def test_chatbot_dynamic_welcome_context_adaptation():
    # Context adaptation on /candidates
    res = client.get("/api/chatbot/welcome?page_context=/candidates")
    assert res.status_code == 200
    msg = res.json()["welcome_message"]
    assert "candidate" in msg.lower() or "profiles" in msg.lower()

