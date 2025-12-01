"""
7: Deploying to AWS Bedrock AgentCore
===============================================
This example shows how to deploy your Strands agent to AWS Bedrock AgentCore,
a fully managed serverless platform for running production AI agents.

What is AgentCore?
- Serverless runtime for AI agents (no infrastructure management)
- Auto-scaling based on demand
- Built-in monitoring and observability
- Integrated with AWS services (Knowledge Bases, S3, etc.)
- Pay only for what you use

This example deploys an HR assistant agent to AgentCore.
"""

# ============================================================================
# STEP 1: Import Required Components
# ============================================================================
from strands import Agent
from strands_tools import retrieve, http_request
from strands.models import BedrockModel
from bedrock_agentcore import BedrockAgentCoreApp


# ============================================================================
# STEP 2: Initialize Global Variables
# ============================================================================
# Global agent instance for reuse across invocations
# This implements a lazy loading pattern for better performance
# The agent is created once and reused for subsequent requests
agent = None

# Initialize the Bedrock AgentCore application
# This is the main application object that handles deployment
app = BedrockAgentCoreApp()


# ============================================================================
# STEP 3: Configure the Model
# ============================================================================
# Use Claude Haiku for fast, cost-effective responses
# Haiku is ideal for production workloads with high request volumes
model = BedrockModel(
    model_id="global.anthropic.claude-haiku-4-5-20251001-v1:0",
    streaming=True  # Enable streaming for better user experience
)


# ============================================================================
# STEP 4: Define Knowledge Base and System Prompt
# ============================================================================
# Knowledge Base ID containing HR policies
kb_id = "ESIT73MSXO"

# System prompt defines the agent's behavior
system_prompt = f"""You are a friendly HR Assistant helping employees find answers to HR questions. 

Use the retrieve tool to search the company's HR knowledge base (KB ID: {kb_id}) before answering any question. Provide clear, accurate answers based on the knowledge base content.

When answering:
- Be concise and helpful
- Reference the source policy or document
- If information isn't in the knowledge base, direct employees to contact HR directly at [hr@company.com]
- Never ask for or store personal employee information

Common topics: vacation policies, benefits, leave policies, company holidays, performance reviews, expenses, and workplace guidelines.
"""


# ============================================================================
# STEP 5: Implement Lazy Loading Pattern
# ============================================================================
def create_agent():
    """
    Create agent with lazy loading pattern for performance.
    
    This pattern ensures the agent is only created once and reused
    across multiple invocations, reducing cold start times and
    improving response latency.
    """
    global agent
    
    # Only create the agent if it doesn't exist yet
    if agent is None:
        agent = Agent(
            model=model,
            tools=[retrieve, http_request],
            system_prompt=system_prompt
        )
    
    return agent


# ============================================================================
# STEP 6: Define AgentCore Entry Point
# ============================================================================
@app.entrypoint
def invoke(payload):
    """
    AgentCore Runtime entry point.
    
    This function is called by AgentCore for each incoming request.
    It receives a payload containing the user's prompt and returns
    the agent's response.
    
    Args:
        payload (dict): Request payload containing:
            - prompt (str): User's question or request
            
    Returns:
        dict: Response containing:
            - response (str): Agent's answer
    """
    # Get or create the agent instance
    agent = create_agent()
    
    # Extract the prompt from the payload
    prompt = payload.get("prompt", "You are a helpful HR agent.")
    
    # Invoke the agent with the prompt
    result = agent(prompt)
    
    # Extract and return the response text
    return {
        "response": result.message.get('content', [{}])[0].get('text', str(result))
    }


# ============================================================================
# STEP 7: Local Testing Entry Point
# ============================================================================
if __name__ == "__main__":
    # Run the app locally for testing
    # This allows you to test your agent before deploying to AgentCore
    app.run()


# ============================================================================
# Deployment Instructions:
# ============================================================================
# 1. Install AgentCore CLI:
#    pip install bedrock-agentcore
#
# 2. Configure AWS credentials:
#    aws configure
#
# 3. Deploy to AgentCore:
#    agentcore deploy
#
# 4. Test your deployed agent:
#    agentcore invoke --prompt "What is the vacation policy?"
#
# 5. Monitor your agent:
#    agentcore logs
#    agentcore metrics
#
# ============================================================================
# Production Best Practices:
# ============================================================================
# - Use lazy loading pattern (as shown) for better performance
# - Implement proper error handling and logging
# - Set appropriate timeout values
# - Monitor costs and usage metrics
# - Use environment variables for configuration
# - Implement rate limiting if needed
# - Add authentication/authorization
# - Set up CloudWatch alarms for monitoring
# - Use VPC endpoints for private deployments
# - Implement proper IAM roles and policies
#
# ============================================================================
# Benefits of AgentCore Deployment:
# ============================================================================
# - No server management required
# - Automatic scaling (0 to thousands of requests)
# - Built-in monitoring and logging
# - Integrated with AWS services
# - Cost-effective (pay per use)
# - High availability and reliability
# - Easy updates and rollbacks
# - Built-in security features


