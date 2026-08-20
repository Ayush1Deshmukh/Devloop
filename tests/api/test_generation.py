from unittest.mock import patch


def test_generate_code_mocked(client):
    """Test the /generate endpoint WITHOUT calling the real AI."""

    # The shape the LangGraph agent actually returns on a clean run.
    fake_ai_response = {
        "objective": "Write a palindrome checker",
        "code_content": "def is_palindrome(s):\n    return s == s[::-1]\n",
        "test_output": "Passed",
        "security_report": "Clear",
        "status": "completed",
        "iterations": 1,
        "logs": ["Iteration 1"],
    }

    with patch("app.api.routes.generation.agent_app.invoke", return_value=fake_ai_response):
        payload = {
            "objective": "Write a palindrome checker",
            "security_level": "high",
        }

        response = client.post("/api/v1/generate", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["message"] == "Success"
        assert data["iterations"] == 1
        assert "is_palindrome" in data["code"]
        assert "task_id" in data


def test_generate_tolerates_partial_agent_state(client):
    """A short-circuited agent omits keys; the route must not 500 on KeyError."""

    partial_response = {"status": "error", "logs": ["AI call failed"]}

    with patch("app.api.routes.generation.agent_app.invoke", return_value=partial_response):
        response = client.post(
            "/api/v1/generate",
            json={"objective": "Write a palindrome checker"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["code"] is None
    assert data["security_report"] == "Not scanned"


def test_generate_rejects_short_objective(client):
    """min_length validation on the request model is actually enforced."""
    response = client.post("/api/v1/generate", json={"objective": "hi"})
    assert response.status_code == 422


def test_generate_returns_502_when_agent_raises(client):
    """An agent crash becomes a clean 502, not an unhandled 500."""
    with patch(
        "app.api.routes.generation.agent_app.invoke",
        side_effect=RuntimeError("recursion limit reached"),
    ):
        response = client.post(
            "/api/v1/generate",
            json={"objective": "Write a palindrome checker"},
        )

    assert response.status_code == 502
    assert "recursion limit reached" in response.json()["detail"]
