class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_step(role, msg):
    print(f"\n{Color.BOLD}{Color.BLUE}[{role}]{Color.RESET} {msg}")

def print_success(msg):
    print(f"\n{Color.GREEN}✅ {msg}{Color.RESET}")

def print_fail(msg):
    print(f"\n{Color.RED}❌ {msg}{Color.RESET}")