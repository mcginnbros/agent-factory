# Base Image for All Agents
# Build once, reuse for all agents for 10x faster deployments
# Contains: Python runtime + common dependencies + system packages

FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright and tools
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    && rm -rf /var/lib/apt/lists/*

# Install common Python dependencies (shared across all agents)
RUN pip install --no-cache-dir \
    strands-agents[a2a]>=0.1.0 \
    strands-agents-tools[a2a_client]>=0.1.0 \
    a2a-sdk>=0.3.0 \
    bedrock-agentcore>=0.1.0 \
    boto3>=1.28.0 \
    botocore>=1.31.0 \
    httpx>=0.24.0 \
    playwright>=1.40.0 \
    fastapi>=0.104.0 \
    uvicorn>=0.24.0 \
    nest-asyncio \
    python-dotenv

# Install Playwright browsers (large download, cache it)
RUN playwright install chromium

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default CMD (overridden by agent-specific images)
CMD ["python", "-m", "bedrock_agentcore.runtime"]
