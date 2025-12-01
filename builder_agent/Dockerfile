# Builder Agent Dockerfile
# Uses shared base image for faster builds
# Build context: agent_factory/code_talk (parent directory)

ARG AWS_ACCOUNT_ID
ARG AWS_REGION=us-west-2
ARG ECR_REPOSITORY_PREFIX=reinvent/agents

FROM ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_PREFIX}:base

WORKDIR /app

# Copy builder agent requirements (if any additional deps needed)
COPY builder_agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY utils/ ./utils/
COPY prompts/ ./prompts/
COPY templates/ ./templates/
COPY services/ ./services/

# Copy Builder Agent code
COPY builder_agent/builder_agent.py .
COPY builder_agent/tools/ ./tools/

# Remove any Python cache files to ensure fresh code
RUN find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
RUN find /app -type f -name "*.pyc" -delete 2>/dev/null || true

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run builder_agent.py which calls app.run() in __main__
CMD ["python", "builder_agent.py"]
