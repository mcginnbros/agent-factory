"""
4: Model Context Protocol (MCP) Integration
=====================================================
This example demonstrates how to connect your agent to MCP servers.
MCP is a standardized protocol that allows agents to access external tools
and data sources in a consistent way.

What is MCP?
- Model Context Protocol: An open standard for connecting AI agents to tools
- Enables agents to access databases, APIs, file systems, and more
- Provides a consistent interface across different tool providers
"""

# ============================================================================
# STEP 1: Import Required Components
# ============================================================================
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient


# ============================================================================
# STEP 2: Configure Your Model
# ============================================================================
# Set up the Bedrock model that will power your agent
model = BedrockModel(
    model_id="global.anthropic.claude-haiku-4-5-20251001-v1:0",  # Fast, efficient model
    streaming=True                                                # Enable streaming responses
)


# ============================================================================
# STEP 3: Create MCP Client Connection
# ============================================================================
# Connect to an MCP server using stdio (standard input/output) transport
# This example connects to the AWS Bedrock AgentCore MCP server
#
# Note: The 'uvx' command is used to run Python packages without installation
# It's similar to 'npx' in the Node.js ecosystem
mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx",  # Command to run the MCP server
                           # Platform-specific: works on macOS, Linux, Windows
            
            args=["awslabs.amazon-bedrock-agentcore-mcp-server@latest"]
                           # MCP server package to run
                           # @latest ensures you get the newest version
        )
    )
)


# ============================================================================
# STEP 4: Use MCP Tools with Your Agent
# ============================================================================
# Manual lifecycle management using context manager
# This ensures proper connection and cleanup
with mcp_client:
    # Retrieve all available tools from the MCP server
    # The server exposes its capabilities as a list of tools
    tools = mcp_client.list_tools_sync()
    
    # Create an agent instance
    # Note: In production, you'd pass the model and tools to the agent
    agent = Agent()
    
    # Alternative: Create agent with model and MCP tools
    agent = Agent(model=model, tools=tools)
    
    # Invoke the agent with a question
    # The agent can now use tools from the MCP server to answer
    # IMPORTANT: Agent invocation must happen within the 'with' block
    # to maintain the MCP connection
    agent("What is AWS AgentCore?")


# ============================================================================
# Key Concepts:
# ============================================================================
# - MCP Server: A service that exposes tools via the MCP protocol
# - MCP Client: Connects to MCP servers and makes tools available to agents
# - stdio Transport: Communication method using standard input/output
# - Context Manager: Ensures proper connection lifecycle (connect/disconnect)
#
# Benefits of MCP:
# - Standardized way to add capabilities to agents
# - Easy to switch between different tool providers
# - Community-driven ecosystem of MCP servers
# - Secure, sandboxed tool execution
#
# Popular MCP Servers:
# - AWS Bedrock AgentCore: AWS service integration
# - Filesystem: File operations
# - Git: Version control operations
# - Database: SQL query execution
# - And many more from the community!