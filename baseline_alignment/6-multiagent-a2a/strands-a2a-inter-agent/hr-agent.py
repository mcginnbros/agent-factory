"""
HR Agent: User-Facing API with A2A Delegation
==============================================
This is the top-level agent in our A2A architecture.
It provides a REST API for users and delegates complex employee queries
to the Employee Agent using Agent-to-Agent (A2A) communication.

Architecture Role:
- Provides: REST API (Port 8000) for user queries
- Consumes: Employee Agent (Port 8001) via A2A protocol
- Purpose: User-facing interface with intelligent delegation
"""

# ============================================================================
# STEP 1: Import Required Components
# ============================================================================
import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from strands import Agent
from strands.models import BedrockModel
from strands_tools.a2a_client import A2AClientToolProvider


# ============================================================================
# STEP 2: Configure Service URLs
# ============================================================================
# URL of the Employee Agent that this agent will delegate to
EMPLOYEE_AGENT_URL = "http://localhost:8001/"


# ============================================================================
# STEP 3: Initialize FastAPI Application
# ============================================================================
# Create a REST API for receiving user queries
app = FastAPI(
    title="HR Agent API",
    description="User-facing HR assistant with A2A delegation capabilities"
)


# ============================================================================
# STEP 4: Define Request/Response Models
# ============================================================================
class QuestionRequest(BaseModel):
    """
    Request model for user questions.
    
    Attributes:
        question (str): The user's HR-related question
    """
    question: str


# ============================================================================
# STEP 5: Health Check Endpoint
# ============================================================================
@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        dict: Status indicating the service is healthy
    """
    return {"status": "healthy"}


# ============================================================================
# STEP 6: Configure the Model
# ============================================================================
# Use Claude Sonnet for strong reasoning and delegation decisions
model = BedrockModel(
    model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    streaming=True  # Enable streaming for real-time responses
)


# ============================================================================
# STEP 7: Main Query Endpoint with A2A Delegation
# ============================================================================
@app.post("/inquire")
async def ask_agent(request: QuestionRequest):
    """
    Main endpoint for processing user questions.
    
    This endpoint:
    1. Receives a user question
    2. Creates an agent with A2A capabilities
    3. The agent automatically delegates to Employee Agent when needed
    4. Streams the response back to the user
    
    Args:
        request (QuestionRequest): User's question
        
    Returns:
        StreamingResponse: Streamed text response from the agent
    """
    
    async def generate():
        """
        Generator function for streaming responses.
        
        This function:
        1. Sets up A2A client tools for the Employee Agent
        2. Creates an agent with those tools
        3. Streams the agent's response
        """
        
        # Create A2A client tool provider
        # This discovers and wraps the Employee Agent as a tool
        # The HR Agent can now call the Employee Agent like any other tool
        provider = A2AClientToolProvider(
            known_agent_urls=[EMPLOYEE_AGENT_URL]
        )
        
        # Create the HR Agent with A2A tools
        # The agent will automatically decide when to delegate to Employee Agent
        agent = Agent(
            model=model,
            tools=provider.tools  # A2A tools for calling Employee Agent
        )
        
        # Stream the agent's response
        # The agent may call the Employee Agent multiple times during processing
        stream_response = agent.stream_async(request.question)
        
        # Yield each chunk of the response as it's generated
        async for event in stream_response:
            if "data" in event:
                yield event["data"]
    
    # Return a streaming response to the client
    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )


# ============================================================================
# STEP 8: Start the Server
# ============================================================================
if __name__ == "__main__":
    print("🚀 Starting HR Agent API Server...")
    print(f"📍 Listening on: http://0.0.0.0:8000")
    print(f"🔗 Connected to Employee Agent: {EMPLOYEE_AGENT_URL}")
    print()
    print("📋 Available endpoints:")
    print("   GET  /health  - Health check")
    print("   POST /inquire - Ask HR questions")
    print()
    print("💡 Example request:")
    print('   curl -X POST http://localhost:8000/inquire \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"question": "List employees with Python skills"}\'')
    print()
    print("✅ Ready to receive requests")
    print()
    
    # Start the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ============================================================================
# How A2A Delegation Works:
# ============================================================================
# 1. User sends POST request to /inquire with a question
# 2. HR Agent receives the question
# 3. HR Agent determines it needs employee information
# 4. HR Agent automatically calls Employee Agent via A2A protocol
# 5. Employee Agent queries MCP Server for data
# 6. Employee Agent returns results to HR Agent
# 7. HR Agent synthesizes final response
# 8. Response is streamed back to user
#
# Benefits of This Architecture:
# - Separation of concerns (HR logic vs Employee data logic)
# - Reusability (Employee Agent can serve multiple clients)
# - Scalability (agents can be scaled independently)
# - Flexibility (easy to add more specialized agents)
# - Maintainability (each agent has a clear responsibility)
#
# Example Queries:
# - "List all employees with Python skills"
# - "Find employees who know AWS and Docker"
# - "What skills are available in the company?"
# - "Who has Machine Learning experience?"
#
# The HR Agent automatically determines when to delegate to the
# Employee Agent based on the nature of the question!