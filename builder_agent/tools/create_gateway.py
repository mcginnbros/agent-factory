"""
Create Gateway Tool for Builder Agent
"""

import os
import logging
import boto3
import sys
from pathlib import Path
from strands import tool

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.response_formatter import format_deployment_success, format_deployment_error
from utils.validation import sanitize_gateway_name

logger = logging.getLogger(__name__)

# Global state to prevent duplicate gateway creation in the same session
_gateway_tracker = {
    'created': False,
    'gateway_id': None,
    'gateway_name': None
}


@tool
def create_gateway(name: str, description: str) -> str:
    """
    Create an AgentCore Gateway for hosting Lambda-based tools.
    
    Args:
        name: Gateway name (e.g., "Order Management Gateway")
        description: Gateway description
    
    Returns:
        Formatted success message with gateway ID
    """
    # Check if we've already created a gateway in this session
    if _gateway_tracker['created']:
        logger.warning(f"⚠️  Attempted duplicate gateway creation blocked. Already created: {_gateway_tracker['gateway_name']}")
        return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ⚠️  DUPLICATE GATEWAY CREATION BLOCKED                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

A gateway has already been created in this session: {_gateway_tracker['gateway_name']}
Gateway ID: {_gateway_tracker['gateway_id']}

Use this gateway_id for creating Lambda tools and deploying the agent.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()
    
    try:        
        region = os.getenv('AWS_REGION', 'us-west-2')
        execution_role = os.getenv('AGENTCORE_EXECUTION_ROLE_ARN')
        
        if not execution_role:
            return format_deployment_error(
                error_type="Configuration Error",
                error_message="AGENTCORE_EXECUTION_ROLE_ARN not configured",
                suggestions=["Set AGENTCORE_EXECUTION_ROLE_ARN in .env file"]
            )
        
        # Create gateway using AgentCore API
        agentcore = boto3.client('bedrock-agentcore-control', region_name=region)
        
        # Sanitize name using centralized validation
        safe_name = sanitize_gateway_name(name)
        
        response = agentcore.create_gateway(
            name=safe_name,
            description=description,
            roleArn=execution_role,
            protocolType='MCP',
            protocolConfiguration={
                'mcp': {
                    'supportedVersions': ['2025-03-26']
                }
            },
            authorizerType='AWS_IAM'
        )
        
        gateway_id = response['gatewayId']
        mcp_url = response.get('gatewayUrl', 'N/A')
        
        # Mark as created to prevent duplicates
        _gateway_tracker['created'] = True
        _gateway_tracker['gateway_id'] = gateway_id
        _gateway_tracker['gateway_name'] = name
        logger.info(f"✅ Gateway tracker updated: {name} ({gateway_id})")
                
        return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        ✅ GATEWAY CREATED SUCCESSFULLY                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

🌐 Gateway: {name}
🆔 Gateway ID: {gateway_id}
📋 Description: {description}
🔗 MCP URL: {mcp_url}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Next Steps:
  1. Create Lambda tools and register them with this gateway
  2. Deploy agents with gateway_id='{gateway_id}'
  3. Agents will have access to all tools in this gateway

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()
        
    except Exception as e:
        logger.error(f"Gateway creation failed: {e}", exc_info=True)
        return format_deployment_error(
            error_type="Gateway Creation Failed",
            error_message=str(e),
            suggestions=[
                "Verify IAM permissions for AgentCore Gateway",
                "Check AWS credentials are configured",
                "Ensure execution role has gateway permissions"
            ]
        )
