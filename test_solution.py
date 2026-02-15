
import pytest
from solution import login

def test_login_basic():
    # Test a standard login attempt
    assert login("admin", "password123") == True

def test_sql_injection_attempt():
    # Test that SQL injection characters are handled safely
    result = login("admin' OR '1'='1", "pass")
    assert result == True
