"""
2.1: Using Anthropic Models Directly
==============================================
This example shows how to use Anthropic's Claude models directly via their API
(instead of through AWS Bedrock). This demonstrates the flexibility of Strands
to support any model and platform.
"""

# ============================================================================
# STEP 1: Import Required Libraries
# ============================================================================
import os
from dotenv import load_dotenv

from strands import Agent
from strands.models.anthropic import AnthropicModel


# ============================================================================
# STEP 2: Load Environment Variables
# ============================================================================
# Load API keys and configuration from .env file
# This keeps sensitive credentials out of your code
load_dotenv()

# Retrieve Anthropic API key from environment
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("Please set the ANTHROPIC_API_KEY environment variable.")

# Get model ID from environment (with sensible default)
ANTHROPIC_MODEL_ID = os.getenv("ANTHROPIC_CLAUDE_4", "claude-sonnet-4-20250514")


# ============================================================================
# STEP 3: Configure Anthropic Model with Advanced Features
# ============================================================================
# Configure the Anthropic model with extended thinking capabilities
# Extended thinking allows the model to "think" before responding,
# improving reasoning quality for complex tasks
anthropic_model = AnthropicModel(
    # Authentication configuration
    client_args={
        "api_key": ANTHROPIC_API_KEY
    },
    
    # Token budget configuration
    # Max tokens is set to 4096 to allow for extended thinking tokens
    # This includes both thinking tokens and response tokens
    max_tokens=4096,
    
    # Specify which Claude model to use
    model_id=ANTHROPIC_MODEL_ID,
    
    # Model parameters
    params={
        # Temperature controls randomness
        # With thinking enabled, we need to set temperature to 1
        # This allows the model to explore different reasoning paths
        "temperature": 1,
        
        # Extended thinking configuration
        # This enables the model to use internal reasoning before responding
        "thinking": {
            "type": "enabled",
            "budget_tokens": 1028  # Tokens allocated for thinking process
        }
    }
)


# ============================================================================
# STEP 4: Create Agent with Anthropic Model
# ============================================================================
# Create an agent using the configured Anthropic model
agent = Agent(model=anthropic_model)


# ============================================================================
# STEP 5: Test the Agent
# ============================================================================
# Invoke the agent with a prompt
# With extended thinking enabled, the model will reason before responding
response = agent("What model are you and who is your creator? Answer in one sentence.")


# ============================================================================
# Key Differences from Bedrock:
# ============================================================================
# - Direct API access to Anthropic (requires ANTHROPIC_API_KEY)
# - Different pricing model (pay Anthropic directly)
# - May have different rate limits and quotas
