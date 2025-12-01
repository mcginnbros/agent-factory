"""
Builder Agent - An AI agent that can create and deploy other agents.
"""

import logging
import os
from typing import Any, Dict, List, Optional

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Strands framework
from strands import Agent, tool
from strands.models import BedrockModel

# Strands tools
from strands_tools.browser import AgentCoreBrowser

# Builder Agent tools
from tools import list_available_tools, deploy_agent, create_gateway, create_lambda_tools, list_deployed_agents

# Prompts
from prompts.builder_agent_prompts import BUILDER_AGENT_SYSTEM_PROMPT

# Services
from services.memory_hooks import AgentCoreMemoryHook
from bedrock_agentcore.memory import MemoryClient

# AWS SDK
import boto3

# Utilities
from utils.logging_config import get_logger

from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Setup logging
logger = get_logger(__name__)

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke_agent(payload, context):
    try:
        # Reset deployment trackers at the start of each invocation
        # This prevents duplicate creations within a single request
        from tools.deploy_agent import _deployment_tracker
        from tools.create_gateway import _gateway_tracker
        _deployment_tracker['deployed'] = False
        _deployment_tracker['agent_name'] = None
        _gateway_tracker['created'] = False
        _gateway_tracker['gateway_id'] = None
        _gateway_tracker['gateway_name'] = None
        logger.info("🔄 Reset deployment trackers for new invocation")
        
        # Extract parameters from payload
        user_input = payload.get("prompt", "")
        session_id = payload.get("session_id", "default-session")
        actor_id = payload.get("actor_id", "default-user")
        
        # Validate input
        if not user_input:
            logger.warning("Empty prompt received")
            return "Please provide a message or question."
                
        # Get configuration
        region = os.getenv('AWS_REGION', 'us-west-2')
        model_id = os.getenv('MODEL_ID', 'us.anthropic.claude-sonnet-4-5-20250929-v1:0')
        
        # Initialize tools
        browser = AgentCoreBrowser(region=region)
        
        # Initialize model
        model = BedrockModel(model_id=model_id, region_name=region)
        
        # Create memory hook
        memory_hook = AgentCoreMemoryHook(
            memory_client=MemoryClient(region_name=region),
            memory_id=os.getenv('BEDROCK_AGENTCORE_MEMORY_ID'),
            session_id=session_id,
            actor_id=actor_id,
            history_turns=5
        )
        
        # Create agent
        agent = Agent(
            model=model,
            tools=[
                list_available_tools,
                browser.browser,
                deploy_agent,
                create_gateway,
                create_lambda_tools,
                list_deployed_agents
            ],
            system_prompt=BUILDER_AGENT_SYSTEM_PROMPT,
            hooks=[memory_hook],  # Enable AgentCore Memory
            callback_handler=None  # Disable to prevent duplicate output
        )
                
        # Process the message
        response_message = agent(user_input)
        
        # Return response as dict with 'result' key (AgentCore requirement)
        return {"result": str(response_message)}
        
    except Exception as e:
        error_msg = f"AgentCore Runtime invocation failed: {e}"
        logger.error(error_msg, exc_info=True)
        
        # Return user-friendly error message as dict
        error_response = f"""I encountered an error while processing your request.

Error: {str(e)}

Please try again or contact support if the issue persists."""
        
        return {"result": error_response}


if __name__ == "__main__":
    app.run()
