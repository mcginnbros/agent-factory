"""
Employee Agent: Specialized Agent for Employee Queries
=======================================================
This agent is the middle layer in our A2A architecture.
It connects to the MCP Server to access employee data and exposes
itself as an A2A service that other agents can call.

Architecture Role:
- Consumes: MCP Server (Port 8002) for employee data
- Provides: A2A service (Port 8001) for employee queries
- Used by: HR Agent for complex employee lookups
"""

# ============================================================================
# STEP 1: Import Required Components
# ============================================================================
import os
from urllib.parse import urlparse

from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient
from strands.multiagent.a2a import A2AServer
from strands.models import BedrockModel


# ============================================================================
# STEP 2: Configure Service URLs
# ============================================================================
# URL of the MCP Server that provides employee data
EMPLOYEE_INFO_URL = "http://localhost:8002/mcp/"

# URL where this agent will be accessible (for A2A communication)
EMPLOYEE_AGENT_URL = "http://localhost:8001/"


# ============================================================================
# STEP 3: Create MCP Client Connection
# ============================================================================
# Connect to the MCP Server to access employee data tools
employee_mcp_client = MCPClient(
    lambda: streamablehttp_client(EMPLOYEE_INFO_URL)
)


# ============================================================================
# STEP 4: Configure the Model
# ============================================================================
# Use Claude Sonnet for strong reasoning about employee queries
model = BedrockModel(
    model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    streaming=True
)


# ============================================================================
# STEP 5: Create Agent with MCP Tools
# ============================================================================
# Use context manager to ensure proper MCP connection lifecycle
with employee_mcp_client:
    # Retrieve all tools from the MCP Server
    # These tools allow the agent to query employee data
    tools = employee_mcp_client.list_tools_sync()
    
    print("🔧 Available MCP tools:")
    for tool in tools:
        print(f"   - {tool.tool_name}")
    print()
    
    # Create the Employee Agent with MCP tools
    employee_agent = Agent(
        model=model,
        name="Employee Agent",
        description="Answers questions about employees",
        tools=tools,
        
        # System prompt defines how the agent should respond
        # This ensures consistent formatting across responses
        system_prompt="you must abbreviate employee first names and list all their skills"
    )
    
    # ========================================================================
    # STEP 6: Create A2A Server
    # ========================================================================
    # Wrap the agent in an A2A server so other agents can call it
    # This exposes the agent as a service that can be discovered and used
    # by other agents in the system
    a2a_server = A2AServer(
        agent=employee_agent,
        host=urlparse(EMPLOYEE_AGENT_URL).hostname,  # Extract hostname
        port=int(urlparse(EMPLOYEE_AGENT_URL).port)  # Extract port
    )
    
    # ========================================================================
    # STEP 7: Start the A2A Server
    # ========================================================================
    if __name__ == "__main__":
        print("🚀 Starting Employee Agent A2A Server...")
        print(f"📍 Listening on: {EMPLOYEE_AGENT_URL}")
        print(f"🔗 Connected to MCP Server: {EMPLOYEE_INFO_URL}")
        print("✅ Ready to receive queries from other agents")
        print()
        
        # Start serving A2A requests
        # This makes the agent available for other agents to call
        a2a_server.serve(host="0.0.0.0", port=8001)


# ============================================================================
# How This Agent Works:
# ============================================================================
# 1. Receives A2A request from HR Agent (or other agents)
# 2. Processes the natural language query
# 3. Determines which MCP tools to use (get_skills, get_employees_with_skill)
# 4. Calls the appropriate MCP Server tools
# 5. Synthesizes the results into a natural language response
# 6. Returns the response via A2A protocol
#
# Key Features:
# - Specialized for employee queries (domain expertise)
# - Reusable by multiple agents (not just HR Agent)
# - Maintains connection to MCP Server throughout its lifecycle
# - Provides consistent response formatting
# - Can handle complex multi-step queries
#
# Example Queries This Agent Can Handle:
# - "List all employees with Python skills"
# - "Find employees who know both AWS and Docker"
# - "What skills are available in the company?"
# - "Who has Machine Learning experience?"