"""
1: Basic Strands Agent
================================
This example demonstrates how easy it is to create and use a Strands AI agent.
Perfect for getting started with agent development!
"""

# ============================================================================
# STEP 1: Import the Agent Class
# ============================================================================
# The Agent class is the core building block of the Strands framework
# It provides AI capabilities for question answering and task execution
from strands import Agent


# ============================================================================
# STEP 2: Create an Agent Instance
# ============================================================================
# Create a new agent with default settings
# By default, this uses a pre-configured LLM model (typically Claude)
# You can customize the agent by passing parameters like:
#   - model: Specify which LLM to use
#   - system_prompt: Define the agent's behavior and personality
#   - tools: Add capabilities like web search, calculations, etc.
agent = Agent()


# ============================================================================
# STEP 3: Interact with Your Agent
# ============================================================================
# Ask the agent a question by calling it like a function
# The agent will process the question using its LLM and return a response
response = agent("What is AWS re:Invent? Answer in one sentence.")


# ============================================================================
# What's Next?
# ============================================================================
# Continue to Tutorial 2 to learn about model switching!