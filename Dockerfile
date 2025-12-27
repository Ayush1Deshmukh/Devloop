FROM python:3.9-slim

WORKDIR /app

# Install pytest (testing) and bandit (security scanning)
RUN pip install pytest bandit

# Keep alive
CMD ["tail", "-f", "/dev/null"]