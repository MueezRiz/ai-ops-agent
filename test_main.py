import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_chat_returns_200():
    """Basic sanity check — endpoint is up and returns 200."""
    response = client.post("/chat", json={"message": "Hello"})
    assert response.status_code == 200


def test_chat_returns_reply_and_conversation_id():
    """Response contains both expected fields."""
    response = client.post("/chat", json={"message": "Hello"})
    data = response.json()
    assert "reply" in data
    assert "conversation_id" in data


def test_tool_call_triggers_for_order_status():
    """Asking about an order should trigger check_order_status and return order info."""
    response = client.post("/chat", json={"message": "What is the status of order 123?"})
    data = response.json()
    assert response.status_code == 200
    assert "reply" in data
    # The mock tool returns something about order 123 — check it surfaced in the reply
    assert "123" in data["reply"]


def test_memory_persists_across_two_calls():
    """Model should recall info from earlier in the same conversation."""
    # First message
    r1 = client.post("/chat", json={"message": "My name is TestUser"})
    conversation_id = r1.json()["conversation_id"]

    # Second message in same conversation
    r2 = client.post("/chat", json={
        "message": "What is my name?",
        "conversation_id": conversation_id
    })
    assert "TestUser" in r2.json()["reply"]


def test_new_conversation_has_no_memory_of_previous():
    """A brand new conversation should not remember a previous one."""
    # First conversation
    r1 = client.post("/chat", json={"message": "My name is TestUser"})
    
    # Second, separate conversation — no conversation_id passed
    r2 = client.post("/chat", json={"message": "What is my name?"})
    assert "TestUser" not in r2.json()["reply"]