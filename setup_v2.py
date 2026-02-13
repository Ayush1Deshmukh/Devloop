import os

# The professional structure for a scalable API
structure = [
    "app",
    "app/api",
    "app/api/routes",
    "app/core",
    "app/core/agents",    # Where logic.py moves to
    "app/models",         # Pydantic models
    "app/services",       # Business logic
    "app/cache",          # Redis logic
    "app/middleware",     # Rate limiting
    "app/observability",  # Metrics
    "tests",
    "tests/api",
    "docker"
]

files = [
    "app/__init__.py",
    "app/main.py",          # Entry point
    "app/core/config.py",   # Settings
    "app/core/__init__.py",
    "app/api/__init__.py",
    ".env",                 # Secrets (ignored by git)
    ".env.example",         # Template for secrets
    "docker/Dockerfile",
    "docker-compose.yml"
]

print("🚀 Initializing DevLoop v2.0 Architecture...")

# Create Directories
for folder in structure:
    os.makedirs(folder, exist_ok=True)
    # Create __init__.py to make it a Python package
    with open(f"{folder}/__init__.py", "w") as f:
        pass
    print(f"✅ Created directory: {folder}")

# Create Files
for file in files:
    if not os.path.exists(file):
        with open(file, "w") as f:
            pass
        print(f"✅ Created file: {file}")
    else:
        print(f"ℹ️  File already exists: {file}")

print("\n🎉 Architecture setup complete!")