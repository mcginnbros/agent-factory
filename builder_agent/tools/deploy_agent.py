"""
Simplified Agent Deployment Tool (No Docker Build Required)

Deploys agents using a pre-built generic agent container.
The agent behavior is configured via environment variables.
"""

import os
import logging
import boto3
import sys
from pathlib import Path
from strands import tool

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.response_formatter import format_deployment_success, format_deployment_error, format_agent_update
from utils.validation import sanitize_runtime_name

logger = logging.getLogger(__name__)

# Global state to prevent duplicate deployments in the same session
_deployment_tracker = {
    'deployed': False,
    'agent_name': None
}


@tool
def deploy_agent(
    name: str,
    purpose: str,
    capabilities: list[str],
    system_prompt: str,
    gateway_id: str = None,
    enable_code_interpreter: bool = False,
    enable_browser: bool = False,
    known_agent_ids: list[str] = None
) -> str:
    """
    Deploy an agent to AWS Bedrock AgentCore Runtime.
    
    All agents have memory enabled. Server agents (with gateway) expose A2A endpoints.
    Client agents (with known_agent_ids) can call other agents.
    
    Args:
        name: Agent name
        purpose: Agent's purpose
        capabilities: List of capabilities
        system_prompt: System prompt
        gateway_id: Gateway ID (makes this a SERVER agent)
        enable_code_interpreter: Enable Code Interpreter
        enable_browser: Enable Browser
        known_agent_ids: List of agent IDs to connect to (makes this a CLIENT agent)
    
    Returns:
        str: Deployment result
    """
    # Check if we've already deployed an agent in this session
    if _deployment_tracker['deployed']:
        logger.warning(f"⚠️  Attempted duplicate deployment blocked. Already deployed: {_deployment_tracker['agent_name']}")
        return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      ⚠️  DUPLICATE DEPLOYMENT BLOCKED                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

An agent has already been deployed in this session: {_deployment_tracker['agent_name']}

To create another agent, please start a new conversation.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()
    
    try:
        # Get configuration
        region = os.environ.get('AWS_REGION', 'us-west-2')
        execution_role = os.environ.get('AGENTCORE_EXECUTION_ROLE_ARN')
        model_id = os.environ.get('DEPLOYED_AGENT_MODEL_ID', 'us.anthropic.claude-haiku-4-5-20251001-v1:0')
        ecr_prefix = os.environ.get('ECR_REPOSITORY_PREFIX', 'reinvent/agents')
        
        if not execution_role:
            return "❌ Error: AGENTCORE_EXECUTION_ROLE_ARN not configured"
        
        # Get AWS account ID
        sts = boto3.client('sts', region_name=region)
        account_id = sts.get_caller_identity()['Account']
        
        # Sanitize name for runtime using centralized validation
        runtime_name = sanitize_runtime_name(name)
        
        # Use pre-built generic agent container with A2A support
        # A2A is always enabled for all agents
        generic_agent_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{ecr_prefix}:generic-agent-a2a"
        
        logger.info(f"📦 Using generic agent container: {generic_agent_uri}")
        logger.info(f"🏷️  Runtime name: {runtime_name}")
        
        # Create AgentCore Runtime
        logger.info("🚀 Creating AgentCore Runtime...")
        
        agentcore_client = boto3.client('bedrock-agentcore-control', region_name=region)
        
        # Determine agent mode:
        # - SERVER: Has gateway (provides tools)
        # - CLIENT: Has known_agent_ids (calls other agents)
        # - Default: SERVER
        logger.info(f"🔍 Debug - known_agent_ids type: {type(known_agent_ids)}, value: {known_agent_ids}")
        
        if gateway_id:
            agent_mode = 'server'
            logger.info(f"🎯 Mode: SERVER (has gateway)")
        elif known_agent_ids and len(known_agent_ids) > 0:
            agent_mode = 'client'
            logger.info(f"🎯 Mode: CLIENT ({len(known_agent_ids)} known agents: {known_agent_ids})")
        else:
            agent_mode = 'server'
            logger.info(f"🎯 Mode: SERVER (default)")
        
        # Prepare environment variables (memory always enabled)
        memory_id = os.environ.get('BEDROCK_AGENTCORE_MEMORY_ID', '')
        if not memory_id:
            logger.warning("⚠️  BEDROCK_AGENTCORE_MEMORY_ID not set")
        
        # Build KNOWN_AGENT_IDS env var
        known_agent_ids_str = ','.join(known_agent_ids) if known_agent_ids else ''
        logger.info(f"🔍 Debug - KNOWN_AGENT_IDS env var: '{known_agent_ids_str}'")
        
        env_vars = {
            'AWS_REGION': region,
            'MODEL_ID': model_id,
            'SYSTEM_PROMPT': system_prompt,
            'AGENT_NAME': name,
            'AGENT_PURPOSE': purpose,
            'AGENT_CAPABILITIES': ','.join(capabilities),
            'AGENT_MODE': agent_mode,
            'ENABLE_CODE_INTERPRETER': 'true' if enable_code_interpreter else 'false',
            'ENABLE_BROWSER': 'true' if enable_browser else 'false',
            'KNOWN_AGENT_IDS': known_agent_ids_str,
            'BEDROCK_AGENTCORE_MEMORY_ID': memory_id,
            'GATEWAY_ID': gateway_id or ''
        }
        
        # Server agents expose A2A endpoint, client agents use Runtime invocation
        protocol_config = {'serverProtocol': 'A2A'} if agent_mode == 'server' else None
        
        try:
            create_params = {
                'agentRuntimeName': runtime_name,
                'agentRuntimeArtifact': {
                    'containerConfiguration': {
                        'containerUri': generic_agent_uri
                    }
                },
                'roleArn': execution_role,
                'networkConfiguration': {
                    'networkMode': 'PUBLIC'
                },
                'environmentVariables': env_vars
            }
            
            # Add protocol configuration if A2A is enabled
            if protocol_config:
                create_params['protocolConfiguration'] = protocol_config
            
            response = agentcore_client.create_agent_runtime(**create_params)
            
            agent_id = response['agentRuntimeId']
            agent_arn = response['agentRuntimeArn']
            status = response.get('status', 'CREATING')
            
            # Mark as deployed to prevent duplicates
            _deployment_tracker['deployed'] = True
            _deployment_tracker['agent_name'] = name
            logger.info(f"✅ Deployment tracker updated: {name}")
            
            return format_deployment_success(
                agent_id=agent_id,
                agent_arn=agent_arn,
                name=name,
                purpose=purpose,
                capabilities=capabilities,
                status=status,
                enable_code_interpreter=enable_code_interpreter,
                enable_browser=enable_browser,
                gateway_id=gateway_id
            )
        
        except agentcore_client.exceptions.ConflictException:
            # Runtime already exists, try to update it
            logger.info(f"Runtime {runtime_name} already exists, updating...")
            
            # List runtimes to find the existing one
            list_response = agentcore_client.list_agent_runtimes()
            existing_runtime = None
            for runtime in list_response.get('agentRuntimeSummaries', []):
                if runtime['agentRuntimeName'] == runtime_name:
                    existing_runtime = runtime
                    break
            
            if existing_runtime:
                agent_id = existing_runtime['agentRuntimeId']
                
                # Update the runtime
                update_params = {
                    'agentRuntimeId': agent_id,
                    'agentRuntimeArtifact': {
                        'containerConfiguration': {
                            'containerUri': generic_agent_uri
                        }
                    },
                    'roleArn': execution_role,
                    'networkConfiguration': {
                        'networkMode': 'PUBLIC'
                    },
                    'environmentVariables': env_vars
                }
                
                if protocol_config:
                    update_params['protocolConfiguration'] = protocol_config
                
                update_response = agentcore_client.update_agent_runtime(**update_params)
                
                agent_arn = update_response['agentRuntimeArn']
                
                # Mark as deployed to prevent duplicates
                _deployment_tracker['deployed'] = True
                _deployment_tracker['agent_name'] = name
                logger.info(f"✅ Deployment tracker updated (update): {name}")
                
                return format_agent_update(
                    agent_id=agent_id,
                    name=name,
                    status="UPDATED"
                )
            else:
                return f"❌ Runtime {runtime_name} exists but couldn't be found. Try a different name."
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}", exc_info=True)
        error_msg = str(e)
        
        # Provide helpful error messages
        if "AccessDenied" in error_msg or "UnauthorizedOperation" in error_msg:
            return format_deployment_error(
                error_type="Permission Denied",
                error_message=error_msg,
                suggestions=[
                    "Run setup script: cd agent_factory/code_talk && ./setup-iam-permissions.sh",
                    "Manually attach policy from iam-policy-builder-agent.json to the execution role",
                    "Verify the execution role has AgentCore permissions"
                ]
            )
        
        elif "RepositoryNotFoundException" in error_msg or "ImageNotFoundException" in error_msg:
            return format_deployment_error(
                error_type="Container Not Found",
                error_message="The generic agent container doesn't exist in ECR yet.",
                suggestions=[
                    "Build the generic agent: docker build --platform linux/arm64 -f templates/generic_agent.dockerfile -t <uri>:generic-agent .",
                    "Push to ECR: docker push <uri>:generic-agent",
                    "Verify image exists: aws ecr list-images --repository-name reinvent/agents"
                ]
            )
        
        else:
            return format_deployment_error(
                error_type="Deployment Error",
                error_message=error_msg,
                suggestions=[
                    "Check AWS credentials are configured",
                    "Verify execution role has necessary permissions",
                    "Ensure generic agent container exists in ECR",
                    "Check CloudWatch logs for more details"
                ]
            )
