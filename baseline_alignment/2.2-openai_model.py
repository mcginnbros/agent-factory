"""
2.2: Using OpenAI Models Directly
==================================
This example demonstrates how to use OpenAI's GPT models with Strands agents.
"""

# ============================================================================
# STEP 1: Import Required Libraries
# ============================================================================
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from strands import Agent
from strands.models.openai import OpenAIModel


# ============================================================================
# STEP 2: Load Environment Variables
# ============================================================================
# Load API keys from .env file
load_dotenv()

# Retrieve OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")

# Get model ID from environment (defaults to GPT-5)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")


# ============================================================================
# STEP 3: Configure OpenAI Model
# ============================================================================
# Configure the OpenAI model with your preferred settings
# Note: Requires OPENAI_API_KEY environment variable to be set
openai_model = OpenAIModel(
    model_id=OPENAI_MODEL,      # Specify which GPT model to use
                                # Options: gpt-4, gpt-4-turbo, gpt-5, etc.
    
    temperature=0.8,            # Control creativity (0.0-2.0)
                                # Higher = more creative responses
    
    max_tokens=150              # Limit response length
                                # Helps control costs and response size
)


# ============================================================================
# STEP 4: Create Agent with OpenAI Model
# ============================================================================
# Create an agent using the configured OpenAI model
agent = Agent(model=openai_model)


# ============================================================================
# STEP 5: Use Structured Output
# ============================================================================
# The structured_output method ensures responses follow a specific format
# This is useful when you need consistent, parseable responses
response = agent.structured_output(
    "What model are you and who is your creator? Answer in one sentence."
)


# ============================================================================
# Why Use OpenAI Models?
# ============================================================================
# - Strong general-purpose reasoning capabilities
# - Excellent for creative tasks and content generation
# - Wide community support and documentation
# - Structured output support for consistent responses
# - Regular updates and improvements from OpenAI