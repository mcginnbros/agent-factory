"""Input validation functions for AgentCore Factory.

This module provides validation functions for agent names, system prompts,
environment variables, and other inputs following AWS naming rules.
"""

import logging
import os
import re
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Base exception for validation errors."""
    pass


def sanitize_aws_name(name: str, max_length: int = 63) -> str:
    """
    Sanitize a name to comply with AWS naming rules.
    
    AWS resource names typically must:
    - Start with a letter
    - Contain only alphanumeric characters and hyphens
    - Not end with a hyphen
    - Be between 1 and max_length characters
    
    Args:
        name: Original name to sanitize
        max_length: Maximum allowed length (default: 63)
        
    Returns:
        Sanitized name that complies with AWS naming rules
        
    Example:
        >>> sanitize_aws_name("My Agent Name!")
        'my-agent-name'
        >>> sanitize_aws_name("123-agent")
        'a-123-agent'
    """
    # Convert to lowercase
    sanitized = name.lower()
    
    # Replace spaces and underscores with hyphens
    sanitized = sanitized.replace(' ', '-').replace('_', '-')
    
    # Remove any characters that aren't alphanumeric or hyphens
    sanitized = re.sub(r'[^a-z0-9-]', '', sanitized)
    
    # Remove consecutive hyphens
    sanitized = re.sub(r'-+', '-', sanitized)
    
    # Ensure it starts with a letter
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'a-' + sanitized
    
    # Remove leading/trailing hyphens
    sanitized = sanitized.strip('-')
    
    # Truncate to max_length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('-')
    
    # Ensure we have a valid name
    if not sanitized:
        sanitized = 'agent'
    
    logger.debug(f"Sanitized '{name}' to '{sanitized}'")
    return sanitized


def sanitize_memory_name(name: str, max_length: int = 48) -> str:
    """
    Sanitize a name for AgentCore Memory resources.
    
    AgentCore Memory names must match: [a-zA-Z][a-zA-Z0-9_]{0,47}
    - Start with a letter
    - Contain only alphanumeric characters and underscores (no hyphens)
    - Be between 1 and 48 characters
    
    Args:
        name: Original name to sanitize
        max_length: Maximum allowed length (default: 48)
        
    Returns:
        Sanitized name that complies with AgentCore Memory naming rules
        
    Example:
        >>> sanitize_memory_name("test-agent-memory")
        'test_agent_memory'
        >>> sanitize_memory_name("123-agent")
        'a_123_agent'
    """
    # Convert to lowercase
    sanitized = name.lower()
    
    # Replace spaces and hyphens with underscores
    sanitized = sanitized.replace(' ', '_').replace('-', '_')
    
    # Remove any characters that aren't alphanumeric or underscores
    sanitized = re.sub(r'[^a-z0-9_]', '', sanitized)
    
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Ensure it starts with a letter
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'a_' + sanitized
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Truncate to max_length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('_')
    
    # Ensure we have a valid name
    if not sanitized:
        sanitized = 'agent_memory'
    
    logger.debug(f"Sanitized memory name '{name}' to '{sanitized}'")
    return sanitized


def sanitize_runtime_name(name: str, max_length: int = 48) -> str:
    """
    Sanitize a name for AgentCore Runtime resources.
    
    AgentCore Runtime names must match: [a-zA-Z][a-zA-Z0-9_]{0,47}
    - Start with a letter
    - Contain only alphanumeric characters and underscores (no hyphens)
    - Be between 1 and 48 characters
    
    Args:
        name: Original name to sanitize
        max_length: Maximum allowed length (default: 48)
        
    Returns:
        Sanitized name that complies with AgentCore Runtime naming rules
        
    Example:
        >>> sanitize_runtime_name("My Agent Name!")
        'My_Agent_Name'
        >>> sanitize_runtime_name("123-agent")
        'agent_123_agent'
    """
    # Replace non-alphanumeric with underscore
    sanitized = re.sub(r'[^a-zA-Z0-9]', '_', name)
    
    # Collapse multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Ensure it starts with a letter
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'agent_' + sanitized
    
    # Truncate to max_length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('_')
    
    # Ensure we have a valid name
    if not sanitized:
        sanitized = 'agent'
    
    logger.debug(f"Sanitized runtime name '{name}' to '{sanitized}'")
    return sanitized


def sanitize_gateway_name(name: str, max_length: int = 48) -> str:
    """
    Sanitize a name for AgentCore Gateway resources.
    
    Gateway names must:
    - Start with an alphanumeric character
    - Contain only alphanumeric characters and hyphens
    - Not have consecutive hyphens
    - Be between 1 and 48 characters
    
    Args:
        name: Original name to sanitize
        max_length: Maximum allowed length (default: 48)
        
    Returns:
        Sanitized name that complies with Gateway naming rules
        
    Example:
        >>> sanitize_gateway_name("Order Management Gateway")
        'Order-Management-Gateway'
        >>> sanitize_gateway_name("123-gateway")
        'gw-123-gateway'
    """
    # Replace non-alphanumeric (except hyphens) with hyphens
    sanitized = re.sub(r'[^a-zA-Z0-9\-]', '-', name)
    
    # Collapse multiple hyphens
    sanitized = re.sub(r'-+', '-', sanitized)
    
    # Remove leading/trailing hyphens
    sanitized = sanitized.strip('-')
    
    # Ensure it starts with alphanumeric
    if sanitized and not sanitized[0].isalnum():
        sanitized = 'gw-' + sanitized.lstrip('-')
    
    # Truncate to max_length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('-')
    
    # Ensure we have a valid name
    if not sanitized:
        sanitized = 'gateway'
    
    logger.debug(f"Sanitized gateway name '{name}' to '{sanitized}'")
    return sanitized


def sanitize_gateway_target_name(name: str, max_length: int = 100) -> str:
    """
    Sanitize a name for Gateway Target resources (Lambda tool names).
    
    Gateway target names must:
    - Contain only alphanumeric characters and hyphens
    - Not have consecutive hyphens
    - Be between 1 and 100 characters
    
    Args:
        name: Original name to sanitize
        max_length: Maximum allowed length (default: 100)
        
    Returns:
        Sanitized name that complies with Gateway Target naming rules
        
    Example:
        >>> sanitize_gateway_target_name("check_inventory")
        'check-inventory'
        >>> sanitize_gateway_target_name("Get User Info!")
        'Get-User-Info'
    """
    # Replace non-alphanumeric (except hyphens) with hyphens
    sanitized = re.sub(r'[^a-zA-Z0-9\-]', '-', name)
    
    # Collapse multiple hyphens
    sanitized = re.sub(r'-+', '-', sanitized)
    
    # Remove leading/trailing hyphens
    sanitized = sanitized.strip('-')
    
    # Truncate to max_length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('-')
    
    # Ensure we have a valid name
    if not sanitized:
        sanitized = 'tool'
    
    logger.debug(f"Sanitized gateway target name '{name}' to '{sanitized}'")
    return sanitized


def validate_agent_name(name: str, min_length: int = 1, max_length: int = 63) -> bool:
    """
    Validate an agent name according to AWS naming rules.
    
    AWS AgentCore agent names must:
    - Be between min_length and max_length characters
    - Start with a letter
    - Contain only alphanumeric characters and hyphens
    - Not end with a hyphen
    - Not contain consecutive hyphens
    
    Args:
        name: Agent name to validate
        min_length: Minimum allowed length (default: 1)
        max_length: Maximum allowed length (default: 63)
        
    Returns:
        True if name is valid
        
    Raises:
        ValidationError: If name is invalid with detailed reason
        
    Example:
        >>> validate_agent_name("customer-support-agent")
        True
        >>> validate_agent_name("123-agent")  # Starts with number
        ValidationError: Agent name must start with a letter
    """
    logger.info(f"Validating agent name: {name}")
    
    # Check if name is empty
    if not name:
        raise ValidationError("Agent name cannot be empty")
    
    # Check length
    if len(name) < min_length:
        raise ValidationError(
            f"Agent name must be at least {min_length} characters long, got {len(name)}"
        )
    
    if len(name) > max_length:
        raise ValidationError(
            f"Agent name must be at most {max_length} characters long, got {len(name)}"
        )
    
    # Check if starts with a letter
    if not name[0].isalpha():
        raise ValidationError(
            f"Agent name must start with a letter, got '{name[0]}'"
        )
    
    # Check if ends with a hyphen
    if name.endswith('-'):
        raise ValidationError("Agent name cannot end with a hyphen")
    
    # Check for valid characters (alphanumeric and hyphens only)
    if not re.match(r'^[a-zA-Z0-9-]+$', name):
        invalid_chars = set(re.findall(r'[^a-zA-Z0-9-]', name))
        raise ValidationError(
            f"Agent name contains invalid characters: {', '.join(invalid_chars)}. "
            f"Only alphanumeric characters and hyphens are allowed."
        )
    
    # Check for consecutive hyphens
    if '--' in name:
        raise ValidationError("Agent name cannot contain consecutive hyphens")
    
    logger.info(f"Agent name '{name}' is valid")
    return True


def validate_system_prompt(prompt: str, min_length: int = 10, max_length: int = 10000) -> bool:
    """
    Validate a system prompt for an agent.
    
    System prompts should:
    - Not be empty
    - Be between min_length and max_length characters
    - Contain meaningful content (not just whitespace)
    
    Args:
        prompt: System prompt to validate
        min_length: Minimum allowed length (default: 10)
        max_length: Maximum allowed length (default: 10000)
        
    Returns:
        True if prompt is valid
        
    Raises:
        ValidationError: If prompt is invalid with detailed reason
        
    Example:
        >>> validate_system_prompt("You are a helpful assistant.")
        True
        >>> validate_system_prompt("   ")
        ValidationError: System prompt cannot be empty or only whitespace
    """
    logger.info("Validating system prompt")
    
    # Check if prompt is empty
    if not prompt:
        raise ValidationError("System prompt cannot be empty")
    
    # Check if prompt is only whitespace
    if not prompt.strip():
        raise ValidationError("System prompt cannot be empty or only whitespace")
    
    # Check length
    prompt_length = len(prompt.strip())
    
    if prompt_length < min_length:
        raise ValidationError(
            f"System prompt must be at least {min_length} characters long, got {prompt_length}"
        )
    
    if prompt_length > max_length:
        raise ValidationError(
            f"System prompt must be at most {max_length} characters long, got {prompt_length}"
        )
    
    logger.info(f"System prompt is valid ({prompt_length} characters)")
    return True

def validate_model_id(model_id: str) -> bool:
    """
    Validate a Bedrock model ID format.
    
    Args:
        model_id: Bedrock model ID to validate
        
    Returns:
        True if model ID appears valid
        
    Raises:
        ValidationError: If model ID format is invalid
        
    Example:
        >>> validate_model_id("global.anthropic.claude-haiku-4-5-20251001-v1:0")
        True
        >>> validate_model_id("")
        ValidationError: Model ID cannot be empty
    """
    logger.info(f"Validating model ID: {model_id}")
    
    if not model_id:
        raise ValidationError("Model ID cannot be empty")
    
    if not model_id.strip():
        raise ValidationError("Model ID cannot be only whitespace")
    
    # Basic format check - should contain provider and model name
    # Examples: 
    # - global.anthropic.claude-haiku-4-5-20251001-v1:0
    # - anthropic.claude-3-sonnet-20240229-v1:0
    if '.' not in model_id:
        raise ValidationError(
            f"Model ID appears invalid: {model_id}. "
            f"Expected format: provider.model-name or global.provider.model-name"
        )
    
    logger.info(f"Model ID '{model_id}' appears valid")
    return True


def validate_capabilities(capabilities: List[str]) -> bool:
    """
    Validate agent capabilities list.
    
    Args:
        capabilities: List of capability strings
        
    Returns:
        True if capabilities are valid
        
    Raises:
        ValidationError: If capabilities are invalid
        
    Example:
        >>> validate_capabilities(["Answer questions", "Search knowledge base"])
        True
        >>> validate_capabilities([])
        ValidationError: Agent must have at least one capability
    """
    logger.info(f"Validating {len(capabilities)} capabilities")
    
    if not capabilities:
        raise ValidationError("Agent must have at least one capability")
    
    if not isinstance(capabilities, list):
        raise ValidationError("Capabilities must be a list")
    
    for i, capability in enumerate(capabilities):
        if not isinstance(capability, str):
            raise ValidationError(f"Capability at index {i} must be a string")
        
        if not capability.strip():
            raise ValidationError(f"Capability at index {i} cannot be empty")
    
    logger.info(f"All {len(capabilities)} capabilities are valid")
    return True


def validate_arn(arn: str, resource_type: Optional[str] = None) -> bool:
    """
    Validate an AWS ARN format.
    
    Args:
        arn: AWS ARN to validate
        resource_type: Optional resource type to check (e.g., 'role', 'lambda')
        
    Returns:
        True if ARN is valid
        
    Raises:
        ValidationError: If ARN format is invalid
        
    Example:
        >>> validate_arn("arn:aws:iam::123456789012:role/MyRole", "role")
        True
        >>> validate_arn("invalid-arn")
        ValidationError: Invalid ARN format
    """
    logger.info(f"Validating ARN: {arn}")
    
    if not arn:
        raise ValidationError("ARN cannot be empty")
    
    # Basic ARN format: arn:partition:service:region:account-id:resource
    arn_pattern = r'^arn:aws[a-z-]*:[a-z0-9-]+:[a-z0-9-]*:\d{12}:.+$'
    
    if not re.match(arn_pattern, arn):
        raise ValidationError(
            f"Invalid ARN format: {arn}. "
            f"Expected format: arn:aws:service:region:account-id:resource"
        )
    
    # Check resource type if specified
    if resource_type:
        if f':{resource_type}/' not in arn and not arn.endswith(f':{resource_type}'):
            raise ValidationError(
                f"ARN does not appear to be for resource type '{resource_type}': {arn}"
            )
    
    logger.info(f"ARN is valid")
    return True



def validate_a2a_url(url: str) -> bool:
    """
    Validate an A2A (Agent-to-Agent) protocol URL.
    
    A2A URLs must:
    - Use HTTPS protocol
    - Have a valid hostname
    - Preferably be an AWS AgentCore endpoint
    
    Args:
        url: A2A URL to validate
        
    Returns:
        True if URL is valid
        
    Raises:
        ValidationError: If URL format is invalid
        
    Example:
        >>> validate_a2a_url("https://bedrock-agentcore.us-west-2.amazonaws.com/runtimes/...")
        True
        >>> validate_a2a_url("http://insecure.com")
        ValidationError: A2A URL must use HTTPS protocol
    """
    from urllib.parse import urlparse
    
    logger.info(f"Validating A2A URL: {url}")
    
    if not url:
        raise ValidationError("A2A URL cannot be empty")
    
    if not url.strip():
        raise ValidationError("A2A URL cannot be only whitespace")
    
    try:
        parsed = urlparse(url)
        
        # Check scheme is HTTPS
        if parsed.scheme != 'https':
            raise ValidationError(
                f"A2A URL must use HTTPS protocol, got: {parsed.scheme}"
            )
        
        # Check hostname is present
        if not parsed.netloc:
            raise ValidationError("A2A URL must have a valid hostname")
        
        # Warn if it doesn't look like an AWS AgentCore URL
        if 'bedrock-agentcore' not in parsed.netloc and 'amazonaws.com' not in parsed.netloc:
            logger.warning(
                f"A2A URL does not appear to be an AWS AgentCore endpoint: {url}"
            )
        
        logger.info("A2A URL is valid")
        return True
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Invalid A2A URL format: {str(e)}") from e


def validate_agent_spec(spec_dict: Dict[str, Any]) -> bool:
    """
    Validate an agent specification dictionary before deployment.
    
    Checks that all required fields are present and valid according to
    AWS AgentCore requirements.
    
    Args:
        spec_dict: Dictionary containing agent specification
        
    Returns:
        True if specification is valid
        
    Raises:
        ValidationError: If specification is invalid
        
    Example:
        >>> spec = {
        ...     'name': 'my-agent',
        ...     'purpose': 'Handle customer support',
        ...     'capabilities': ['answer_questions'],
        ...     'system_prompt': 'You are a helpful assistant.'
        ... }
        >>> validate_agent_spec(spec)
        True
    """
    logger.info("Validating agent specification")
    
    # Check required fields
    required_fields = ['name', 'purpose', 'capabilities', 'system_prompt']
    missing_fields = [field for field in required_fields if field not in spec_dict]
    
    if missing_fields:
        raise ValidationError(
            f"Agent specification missing required fields: {', '.join(missing_fields)}"
        )
    
    # Validate name
    validate_agent_name(spec_dict['name'])
    
    # Validate purpose
    if not spec_dict['purpose'] or not spec_dict['purpose'].strip():
        raise ValidationError("Agent purpose cannot be empty")
    
    if len(spec_dict['purpose'].strip()) < 10:
        raise ValidationError(
            f"Agent purpose too short (minimum 10 characters): {len(spec_dict['purpose'].strip())}"
        )
    
    # Validate capabilities
    validate_capabilities(spec_dict['capabilities'])
    
    # Validate system prompt
    validate_system_prompt(spec_dict['system_prompt'])
    
    # Validate optional model_id if present
    if 'model_id' in spec_dict and spec_dict['model_id']:
        validate_model_id(spec_dict['model_id'])
    
    # Validate optional gateway_id if gateway_enabled
    if spec_dict.get('gateway_enabled') and not spec_dict.get('gateway_id'):
        raise ValidationError(
            "gateway_id must be provided when gateway_enabled is True"
        )
    
    # Validate optional execution_role_arn if present
    if 'execution_role_arn' in spec_dict and spec_dict['execution_role_arn']:
        validate_arn(spec_dict['execution_role_arn'], 'role')
    
    logger.info("Agent specification is valid")
    return True


def validate_tool_schema(schema: Dict[str, Any]) -> bool:
    """
    Validate a tool input schema for Lambda function creation.
    
    Tool schemas must follow JSON Schema specification and contain
    all required fields for tool definition.
    
    Args:
        schema: Tool input schema dictionary
        
    Returns:
        True if schema is valid
        
    Raises:
        ValidationError: If schema is invalid
        
    Example:
        >>> schema = {
        ...     'type': 'object',
        ...     'properties': {
        ...         'query': {'type': 'string', 'description': 'Search query'}
        ...     },
        ...     'required': ['query']
        ... }
        >>> validate_tool_schema(schema)
        True
    """
    logger.info("Validating tool schema")
    
    # Check required top-level fields
    if not isinstance(schema, dict):
        raise ValidationError("Tool schema must be a dictionary")
    
    if "type" not in schema:
        raise ValidationError("Tool schema must have 'type' field")
    
    if schema["type"] != "object":
        raise ValidationError(
            f"Tool schema type must be 'object', got: {schema['type']}"
        )
    
    if "properties" not in schema:
        raise ValidationError("Tool schema must have 'properties' field")
    
    if not isinstance(schema["properties"], dict):
        raise ValidationError("Tool schema 'properties' must be a dictionary")
    
    if not schema["properties"]:
        raise ValidationError("Tool schema 'properties' cannot be empty")
    
    # Validate each property
    valid_types = ["string", "number", "integer", "boolean", "array", "object", "null"]
    
    for prop_name, prop_schema in schema["properties"].items():
        if not isinstance(prop_schema, dict):
            raise ValidationError(
                f"Property '{prop_name}' schema must be a dictionary"
            )
        
        if "type" not in prop_schema:
            raise ValidationError(
                f"Property '{prop_name}' must have 'type' field"
            )
        
        if prop_schema["type"] not in valid_types:
            raise ValidationError(
                f"Property '{prop_name}' has invalid type: {prop_schema['type']}. "
                f"Valid types: {', '.join(valid_types)}"
            )
        
        # Validate description is present (recommended for tool clarity)
        if "description" not in prop_schema:
            logger.warning(
                f"Property '{prop_name}' missing 'description' field (recommended)"
            )
    
    # Validate required field if present
    if "required" in schema:
        if not isinstance(schema["required"], list):
            raise ValidationError("Tool schema 'required' must be a list")
        
        # Check that all required properties exist
        for req_prop in schema["required"]:
            if req_prop not in schema["properties"]:
                raise ValidationError(
                    f"Required property '{req_prop}' not found in properties"
                )
    
    logger.info("Tool schema is valid")
    return True


def validate_lambda_tool_config(config: Dict[str, Any]) -> bool:
    """
    Validate a Lambda tool configuration before deployment.
    
    Checks that all required fields are present and valid for creating
    a Lambda function as an agent tool.
    
    Args:
        config: Dictionary containing Lambda tool configuration
        
    Returns:
        True if configuration is valid
        
    Raises:
        ValidationError: If configuration is invalid
        
    Example:
        >>> config = {
        ...     'name': 'search_tickets',
        ...     'description': 'Search support tickets',
        ...     'input_schema': {...},
        ...     'handler_code': 'def handler(event, context): ...'
        ... }
        >>> validate_lambda_tool_config(config)
        True
    """
    logger.info("Validating Lambda tool configuration")
    
    # Check required fields
    required_fields = ['name', 'description', 'input_schema', 'handler_code']
    missing_fields = [field for field in required_fields if field not in config]
    
    if missing_fields:
        raise ValidationError(
            f"Lambda tool configuration missing required fields: {', '.join(missing_fields)}"
        )
    
    # Validate tool name (must be valid Python identifier)
    tool_name = config['name']
    if not tool_name.isidentifier():
        raise ValidationError(
            f"Tool name must be a valid Python identifier: {tool_name}"
        )
    
    # Validate description
    if not config['description'] or not config['description'].strip():
        raise ValidationError("Tool description cannot be empty")
    
    if len(config['description'].strip()) < 10:
        raise ValidationError(
            f"Tool description too short (minimum 10 characters): {len(config['description'].strip())}"
        )
    
    # Validate input schema
    validate_tool_schema(config['input_schema'])
    
    # Validate handler code
    if not config['handler_code'] or not config['handler_code'].strip():
        raise ValidationError("Tool handler_code cannot be empty")
    
    # Try to validate Python syntax of handler code
    try:
        import ast
        ast.parse(config['handler_code'])
    except SyntaxError as e:
        raise ValidationError(
            f"Tool handler_code has syntax error at line {e.lineno}: {e.msg}"
        )
    
    logger.info(f"Lambda tool configuration is valid: {tool_name}")
    return True
