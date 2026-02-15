import os

def calculate_expression(user_input):
    # SECURITY FLAW: Using eval() allows code injection
    # LOGIC BUG: Division by zero is not handled
    result = eval(user_input)
    return result

def run_backup():
    # SECURITY FLAW: Using os.system is unsafe
    os.system("tar -czf backup.tar.gz /data")

# Test run
print(calculate_expression("10 + 5"))
