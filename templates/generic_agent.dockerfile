# Generic Agent Dockerfile
# Single container that can be configured for any agent via environment variables

ARG AWS_ACCOUNT_ID
ARG AWS_REGION=us-west-2
ARG ECR_REPOSITORY_PREFIX=reinvent/agents

FROM ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_PREFIX}:base

WORKDIR /app

# Copy utils directory (includes sigv4_transport for gateway authentication)
COPY utils/ ./utils/

# Copy services directory (includes memory_hooks for AgentCore Memory)
COPY services/ ./services/

# Copy generic agent code
COPY templates/generic_agent.py agent.py

# Set environment variables (will be overridden by runtime)
ENV PYTHONUNBUFFERED=1
ENV AGENT_NAME="Generic Agent"
ENV AGENT_PURPOSE="General assistance"
ENV SYSTEM_PROMPT="You are a helpful AI assistant."

# Expose port 9000 for A2A protocol (official AgentCore A2A pattern)
# With protocolConfiguration.serverProtocol='A2A', AgentCore routes to this port
EXPOSE 9000

# Run agent - starts A2A server on port 9000
CMD ["python", "agent.py"]
