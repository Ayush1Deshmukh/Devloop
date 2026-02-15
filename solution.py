
import sqlite3

def login(username, password):
    # SECURE: Using parameterized queries prevents SQL Injection
    query = "SELECT * FROM users WHERE username = ? AND password = ?"
    params = (username, password)
    
    # Simulation output
    print(f"🔒 SECURE EXECUTION: {query} with params {params}")
    return True
