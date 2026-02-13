from unittest.mock import patch

def test_generate_code_mocked(client):
    """
    Test the /generate endpoint WITHOUT calling the real AI.
    """
    
    # 1. Define the fake success response
    fake_ai_response = {
        "status": "success",
        "iterations": 1,
        "logs": ["Fake AI Log"]
    }

    # 2. Patch (Mock) the 'invoke' method of the agent
    # This prevents the real Google API call
    with patch("app.api.routes.generation.agent_app.invoke", return_value=fake_ai_response):
        
        payload = {
            "objective": "Write a unit test",
            "security_level": "high"
        }
        
        response = client.post(f"/api/v1/generate", json=payload)
        
        # 3. Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "task_id" in data