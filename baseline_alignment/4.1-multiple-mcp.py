"""
4.1: Using Multiple MCP Servers
=========================================
This advanced example shows how to connect to multiple MCP servers simultaneously,
combining their capabilities into a single powerful agent.

Use Case: AWS Solutions Architect Agent
This agent can access both AWS documentation and pricing information to provide
comprehensive answers about AWS services and their costs.
"""

# ============================================================================
# STEP 1: Import Required Libraries
# ============================================================================
import os
from dotenv import load_dotenv

from strands.models import BedrockModel
from strands import Agent
from strands.tools.mcp import MCPClient
from strands_tools import file_read, file_write
from mcp import stdio_client, StdioServerParameters


# ============================================================================
# STEP 2: Load Environment Variables
# ============================================================================
# Load AWS credentials and configuration from .env file
load_dotenv()

# AWS credentials are required to access pricing data via the pricing MCP server
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")

# Validate that required credentials are present
if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]):
    raise ValueError("AWS credentials are required to access pricing data.")


# ============================================================================
# STEP 3: Configure the Model
# ============================================================================
# Use Claude Sonnet for strong reasoning capabilities
model = BedrockModel(
    model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    streaming=True
)

# ============================================================================
# STEP 4: Define Agent System Prompt
# ============================================================================
# This comprehensive prompt guides the agent on how to use multiple tool sources
SYSTEM_PROMPT = """
You are an AWS Solutions Architect with expertise in AWS services and solutions.

You have access to the following tools:

FILE OPERATIONS:
  - file_read: Read the contents of a file
  - file_write: Write content to a file

AWS DOCUMENTATION TOOLS (from aws-documentation-mcp-server):
  - search_documentation: Find relevant AWS docs
  - read_documentation: Get full content of specific docs
  - recommend: Get related documentation

AWS PRICING TOOLS (from aws-pricing-mcp-server):
  - get_pricing_service_codes: List all available AWS service codes
  - get_pricing_service_attributes: Find filterable attributes for a service
  - get_pricing_attribute_values: Get valid values for attributes
  - get_pricing: Get actual pricing data using the service code, region, and filters
  - get_bedrock_patterns: Get architecture patterns for Bedrock
  - generate_cost_report: Generate detailed cost analysis reports

IMPORTANT PRICING WORKFLOW - FOLLOW EXACTLY:
  1. Use get_pricing_service_codes() to get service codes "AmazonS3" and "AmazonCloudFront"
  2. For each service (S3 and CloudFront), use get_pricing_service_attributes() to find attributes
  3. Use get_pricing("AmazonS3", "us-east-1") for S3 pricing
  4. Use get_pricing("AmazonCloudFront", "us-east-1") for CloudFront pricing
  5. Include all pricing details in your summary

When answering questions, always use the available tools to gather accurate information. Cite
documentation URLs when providing information.
"""

# ============================================================================
# STEP 5: Create Multiple MCP Client Connections
# ============================================================================

# MCP Client #1: AWS Documentation Server
# Provides access to the complete AWS documentation library
aws_docs_mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx",
            args=["awslabs.aws-documentation-mcp-server@latest"]
        ),
    )
)

# MCP Client #2: AWS Pricing Server
# Provides real-time AWS pricing information
# NOTE: Requires AWS credentials to access pricing data
aws_pricing_mcp_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx",
            args=["awslabs.aws-pricing-mcp-server@latest"],
            
            # Pass AWS credentials as environment variables to the MCP server
            env={
                "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,
                "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
                "AWS_REGION": AWS_REGION
            }
        ),
    )
)


# ============================================================================
# STEP 6: Define the Task
# ============================================================================
# Create a comprehensive prompt that requires both documentation and pricing info
prompt = """
Create a summary of hosting a static website on AWS using S3 and CloudFront.

Include:
  1. Direct links to the official AWS documentation for S3 static website hosting and CloudFront
     distribution setup
  2. Pricing for S3 storage (first 50GB) and CloudFront data transfer (first 10TB)

Save the summary to static_website_aws.md
"""


# ============================================================================
# STEP 7: Connect to Multiple MCP Servers and Create Agent
# ============================================================================
# Use context managers to handle multiple MCP connections
# Both servers will be connected simultaneously
with aws_docs_mcp_client, aws_pricing_mcp_client:
    
    # Combine tools from both MCP clients into a single tool list
    # This gives the agent access to all capabilities from both servers
    tools = aws_docs_mcp_client.list_tools_sync() + aws_pricing_mcp_client.list_tools_sync()
    
    # Display available tools for visibility
    print(f"\nAvailable tools from MCP servers ({len(tools)}):")
    for tool in tools:
        print(f"  - {tool.tool_name}")
    print()
    
    # Create an agent with access to:
    # - File operations (file_read, file_write)
    # - AWS documentation tools (from first MCP server)
    # - AWS pricing tools (from second MCP server)
    aws_agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[file_read, file_write, tools],  # Combine local and MCP tools
    )
    
    # Invoke the agent with our comprehensive task
    # The agent will automatically use the appropriate tools from both MCP servers
    aws_agent(prompt)


# ============================================================================
# Key Takeaways:
# ============================================================================
# - Multiple MCP servers can be used simultaneously
# - Tools from different servers are combined into a single tool list
# - The agent automatically selects the right tools for each subtask
# - Context managers ensure proper connection lifecycle for all servers
# - This pattern enables building highly capable, specialized agents
#
# Real-World Applications:
# - Solutions architects needing docs + pricing
# - DevOps engineers needing monitoring + deployment tools
# - Data engineers needing database + analytics tools
# - Any scenario requiring multiple specialized tool sources

