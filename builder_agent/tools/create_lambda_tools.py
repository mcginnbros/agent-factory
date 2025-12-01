"""
Create Lambda Tools for Builder Agent
"""

import os
import logging
import boto3
import json
import sys
from pathlib import Path
from strands import tool

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from services.lambda_service import LambdaService, LambdaToolSpec
from utils.response_formatter import format_deployment_error
from utils.validation import sanitize_gateway_target_name

logger = logging.getLogger(__name__)


@tool
def create_lambda_tools(gateway_id: str, tools_spec: str) -> str:
    """
    Create Lambda functions as tools and register with gateway.
    
    Args:
        gateway_id: Gateway ID to register tools with
        tools_spec: JSON string with array of tool specifications
    
    Tool spec format:
    [
        {
            "name": "check_inventory",
            "description": "Check product inventory levels",
            "input_schema": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"}
                },
                "required": ["product_id"]
            },
            "handler_code": "return {'in_stock': True, 'quantity': 42}"
        }
    ]
    
    Returns:
        Formatted success message with created tools
    """
    try:
        region = os.getenv('AWS_REGION', 'us-west-2')
        # Prefer LAMBDA_EXECUTION_ROLE_ARN, fall back to AGENTCORE_EXECUTION_ROLE_ARN
        execution_role = os.getenv('LAMBDA_EXECUTION_ROLE_ARN') or os.getenv('AGENTCORE_EXECUTION_ROLE_ARN')
        
        if not execution_role:
            return format_deployment_error(
                error_type="Configuration Error",
                error_message="Lambda execution role not configured",
                suggestions=[
                    "Set LAMBDA_EXECUTION_ROLE_ARN in .env file",
                    "Or ensure AGENTCORE_EXECUTION_ROLE_ARN has Lambda trust policy",
                    "Role must allow lambda.amazonaws.com to assume it"
                ]
            )
        
        # Parse tools spec
        try:
            tools = json.loads(tools_spec)
        except json.JSONDecodeError as e:
            return format_deployment_error(
                error_type="Invalid JSON",
                error_message=f"Failed to parse tools_spec: {e}",
                suggestions=["Ensure tools_spec is valid JSON array"]
            )
        
        if not isinstance(tools, list):
            return format_deployment_error(
                error_type="Invalid Format",
                error_message="tools_spec must be a JSON array",
                suggestions=["Wrap tool definitions in []"]
            )
        
        # Initialize services
        lambda_service = LambdaService(region_name=region)
        agentcore = boto3.client('bedrock-agentcore-control', region_name=region)
        
        # Create Lambda functions
        created_tools = []
        failed_tools = []
        
        for tool_def in tools:
            tool_name = tool_def.get('name', 'unknown')
            logger.info(f"Creating tool: {tool_name}")
            
            try:
                # Validate tool definition
                if not all(k in tool_def for k in ['name', 'description', 'input_schema', 'handler_code']):
                    raise ValueError("Tool missing required fields")
                
                # Create Lambda function
                tool_spec = LambdaToolSpec(
                    name=tool_def['name'],
                    description=tool_def['description'],
                    input_schema=tool_def['input_schema'],
                    handler_code=tool_def['handler_code']
                )
                
                lambda_result = lambda_service.create_tool_function(
                    tool_spec=tool_spec,
                    execution_role_arn=execution_role,
                    function_prefix=f"gateway-{gateway_id}"
                )
                
                # Register with gateway as a target
                # Sanitize target name using centralized validation
                target_name = sanitize_gateway_target_name(tool_def['name'])
                
                agentcore.create_gateway_target(
                    gatewayIdentifier=gateway_id,
                    name=target_name,
                    description=tool_def['description'],
                    targetConfiguration={
                        'mcp': {
                            'lambda': {
                                'lambdaArn': lambda_result['function_arn'],
                                'toolSchema': {
                                    'inlinePayload': [
                                        {
                                            'name': tool_def['name'],
                                            'description': tool_def['description'],
                                            'inputSchema': tool_def['input_schema']
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    credentialProviderConfigurations=[
                        {
                            'credentialProviderType': 'GATEWAY_IAM_ROLE'
                        }
                    ]
                )
                
                # Add Lambda invoke permission for the gateway
                lambda_client = boto3.client('lambda', region_name=region)
                sts = boto3.client('sts')
                account_id = sts.get_caller_identity()['Account']
                
                try:
                    lambda_client.add_permission(
                        FunctionName=lambda_result['function_name'],
                        StatementId=f'AllowGatewayInvoke-{gateway_id}',
                        Action='lambda:InvokeFunction',
                        Principal='bedrock-agentcore.amazonaws.com',
                        SourceArn=f'arn:aws:bedrock-agentcore:{region}:{account_id}:gateway/{gateway_id}'
                    )
                    logger.info(f'Added Lambda invoke permission for gateway')
                except lambda_client.exceptions.ResourceConflictException:
                    logger.info(f'Lambda invoke permission already exists')
                except Exception as e:
                    logger.warning(f'Failed to add Lambda permission (may already exist): {e}')
                
                created_tools.append({
                    'name': tool_name,
                    'function_arn': lambda_result['function_arn'],
                    'description': tool_def['description']
                })
                
                logger.info(f"✓ Tool created: {tool_name}")
                
            except Exception as e:
                logger.error(f"Failed to create tool {tool_name}: {e}")
                failed_tools.append({'name': tool_name, 'error': str(e)})
        
        # Format response
        if created_tools and not failed_tools:
            tools_list = '\n'.join([f"  • {t['name']}: {t['description']}" for t in created_tools])
            return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      ✅ LAMBDA TOOLS CREATED SUCCESSFULLY                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

🌐 Gateway ID: {gateway_id}
🛠️  Tools Created: {len(created_tools)}

{tools_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Next Step:
  Deploy an agent with gateway_id='{gateway_id}' to use these tools

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()
        
        elif failed_tools:
            errors = '\n'.join([f"  • {t['name']}: {t['error']}" for t in failed_tools])
            return format_deployment_error(
                error_type="Partial Failure",
                error_message=f"Created {len(created_tools)} tools, {len(failed_tools)} failed\n\nFailed:\n{errors}",
                suggestions=["Check tool definitions", "Verify IAM permissions"]
            )
        
        else:
            return format_deployment_error(
                error_type="All Tools Failed",
                error_message="No tools were created successfully",
                suggestions=["Check tool definitions", "Verify Lambda permissions", "Check CloudWatch logs"]
            )
        
    except Exception as e:
        logger.error(f"Lambda tools creation failed: {e}", exc_info=True)
        return format_deployment_error(
            error_type="Lambda Tools Creation Failed",
            error_message=str(e),
            suggestions=[
                "Verify gateway exists",
                "Check Lambda permissions",
                "Ensure execution role is valid"
            ]
        )
