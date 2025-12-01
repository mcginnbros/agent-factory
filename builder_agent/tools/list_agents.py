"""
List Deployed Agents Tool

Allows the builder agent to discover existing agents and their A2A URLs.
"""

import os
import logging
import boto3
from urllib.parse import quote
from strands import tool

logger = logging.getLogger(__name__)


@tool
def list_deployed_agents() -> str:
    """
    List all deployed agents in AgentCore Runtime.
    
    Use this tool when you need to:
    - Find existing agents to connect to
    - Get agent IDs for orchestrator agents
    - Check what agents are available
    
    Returns:
        str: Formatted list of agents with names and IDs
    
    Example:
        When creating an orchestrator agent, use this tool first to get agent IDs.
    """
    try:
        region = os.environ.get('AWS_REGION', 'us-west-2')
        client = boto3.client('bedrock-agentcore-control', region_name=region)
        
        # List all agents
        response = client.list_agent_runtimes()
        agents = response.get('agentRuntimes', [])
        
        if not agents:
            return "No agents currently deployed."
        
        # Filter to only READY agents
        ready_agents = [a for a in agents if a.get('status') == 'READY']
        
        if not ready_agents:
            return "No READY agents found. Some agents may still be deploying."
        
        # Format output
        output = ["📋 Deployed Agents:\n"]
        
        for idx, agent in enumerate(ready_agents, 1):
            name = agent.get('agentRuntimeName', 'unknown')
            agent_id = agent['agentRuntimeId']
            
            output.append(f"{idx}. **{name}**")
            output.append(f"   - Agent ID: `{agent_id}`")
            output.append("")
        
        output.append("💡 **Tip**: Use these agent IDs in the `known_agent_ids` parameter when deploying orchestrator agents.")
        
        return "\n".join(output)
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        return f"❌ Error listing agents: {str(e)}"
