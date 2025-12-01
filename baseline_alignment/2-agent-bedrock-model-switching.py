"""
2: AWS Bedrock Model Switching
========================================
Learn how to configure and switch between different LLM models available
through AWS Bedrock. This gives you flexibility to choose the right model
for your use case based on performance, cost, and capabilities.
"""

# ============================================================================
# STEP 1: Import Required Classes
# ============================================================================
from strands import Agent
from strands.models import BedrockModel


# ============================================================================
# STEP 2: Configure Your Bedrock Model
# ============================================================================
# AWS Bedrock provides access to multiple foundation models:
#
# Available Models (examples):
#   - Anthropic Claude Sonnet 4.5: global.anthropic.claude-sonnet-4-5-20250929-v1:0
#   - Meta Llama 4 Maverick 17B:   us.meta.llama4-maverick-17b-instruct-v1:0
#   - DeepSeek-R1:                 us.deepseek.r1-v1:0
#   - OpenAI GPT OSS 120B:         openai.gpt-oss-120b-1:0
#   - Amazon Nova Premier:         us.amazon.nova-premier-v1:0

model = BedrockModel(
    model_id="us.amazon.nova-premier-v1:0",  # Specify which model to use
    temperature=0.3,                          # Control randomness (0.0-1.0)
                                              # Lower = more focused/deterministic
                                              # Higher = more creative/random
    
    top_p=0.8,                                # Control diversity of token selection
                                              # Lower = more focused vocabulary
                                              # Higher = more diverse responses
    
    streaming=True                            # Enable real-time response streaming
                                              # Great for user experience!
)


# ============================================================================
# STEP 3: Create Agent with Custom Model
# ============================================================================
# Pass your configured model to the Agent constructor
agent = Agent(model=model)


# ============================================================================
# STEP 4: Test Your Model Configuration
# ============================================================================
# Ask a question that helps verify which model is being used
response = agent("What model are you and who is your creator? Answer in one sentence.")


# ============================================================================
# Pro Tips:
# ============================================================================
# - Try different models to compare responses and performance
# - Adjust temperature for different use cases (factual vs creative)
# - Use streaming=True for better user experience in interactive apps
# - Check AWS Bedrock documentation for the latest available models