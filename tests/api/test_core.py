def test_health_check(client):
    """Ensure the API is alive."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_metrics_endpoint(client):
    """Ensure Prometheus metrics are exposed."""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Check if our custom metric exists in the text output
    assert "devloop_http_requests_total" in response.text