import sqlite3

def login(username, password):
    # VULNERABLE: Direct string concatenation (SQL Injection Risk)
    query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
    
    # This is just a simulation stub
    print(f"Executing: {query}")
    return True