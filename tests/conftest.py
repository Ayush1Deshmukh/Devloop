import pytest
from fastapi.testclient import TestClient
from app.main import app

# Create a "Fixture"
# This allows every test to use a fresh client without repeating code
@pytest.fixture(scope="module")
def client():
    # TestClient acts like a web browser, but runs inside Python (super fast)
    with TestClient(app) as c:
        yield c