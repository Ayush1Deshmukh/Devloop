# Root Dockerfile == the FastAPI AI Engine, built for Hugging Face Spaces.
#
# Spaces (Docker SDK) only ever builds a Dockerfile at the repo root, so this
# file has to be the engine. It replaces a stale python:3.9 duplicate of
# docker/Dockerfile.sandbox that nothing referenced.
#
# Other targets:
#   docker/Dockerfile          -> docker-compose engine (has the Docker socket)
#   docker/Dockerfile.sandbox  -> compose sandbox container
#   docker/Dockerfile.hf-gateway -> Spring Boot gateway (Spaces/Render)
#
# There is no Docker socket on free hosting, so the agent falls back to the
# rlimit sandbox in tools.py automatically.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

# Spaces runs containers as this exact non-root UID.
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

USER user

EXPOSE 7860

# Single worker: free tiers are memory-constrained and each worker loads the
# whole LangGraph/LangChain stack. $PORT is honoured for Render compatibility.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860} --workers 1"]
