"""
2.3: Using Ollama for Local Models
============================================
This example shows how to run AI models locally using Ollama.
Perfect for development, testing, or compliance reasons.
"""

# ============================================================================
# STEP 1: Import Required Libraries
# ============================================================================
import os
from dotenv import load_dotenv

from strands import Agent
from strands.models.ollama import OllamaModel


# ============================================================================
# STEP 2: Load Configuration
# ============================================================================
# Load environment variables from .env file
load_dotenv()

# Get Ollama server configuration
# Default: http://localhost:11434 (standard Ollama installation)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Get model ID from environment
# Default: llama3.2:3b (a lightweight, fast model)
# See all available models: https://ollama.com/docs/models
OLLAMA_MODEL_ID = os.getenv("OLLAMA_MODEL_ID", "llama3.2:3b")


# ============================================================================
# STEP 3: Configure Ollama Model
# ============================================================================
# Create an Ollama model instance with custom configuration
# Ollama allows you to run open-source models locally on your machine
ollama_model = OllamaModel(
    host=OLLAMA_HOST,                    # Ollama server address
                                         # Usually localhost for local development
    
    model_id=OLLAMA_MODEL_ID,            # Which model to use
                                         # Popular options: llama3.2, mistral, phi3
    
    temperature=0.7,                     # Control randomness (0.0-1.0)
    
    keep_alive="10m",                    # Keep model loaded in memory
                                         # Improves response time for follow-up queries
    
    stop_sequences=["###", "END"],       # Tokens that signal end of response
                                         # Useful for controlling output format
    
    options={"top_k": 40}                # Additional model parameters
                                         # top_k limits token selection pool
)


# ============================================================================
# STEP 4: Create Agent with Ollama Model
# ============================================================================
# Create an agent using the locally-running Ollama model
agent = Agent(model=ollama_model)


# ============================================================================
# STEP 5: Test Your Local Agent
# ============================================================================
# Ask a question to verify the model is working
result = agent("What model are you and who is your creator? Answer in one sentence.")


# ============================================================================
# Benefits of Using Ollama:
# ============================================================================
# - Run models completely offline (no API calls)
# - No per-token costs (free after initial setup)
# - Full data privacy (everything stays on your machine)
# - Great for development and testing
# - Access to many open-source models
#
# Prerequisites:
# - Install Ollama: https://ollama.com/download
# - Pull a model: ollama pull llama3.2:3b
# - Run Ollama model: ollama run llama3.2:3b