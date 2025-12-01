"""
Response Formatter for Builder Agent

Provides clean, readable formatting for agent responses in demos and presentations.
"""


def format_deployment_success(
    agent_id: str,
    agent_arn: str,
    name: str,
    purpose: str,
    capabilities: list[str],
    status: str = "CREATING",
    enable_code_interpreter: bool = False,
    enable_browser: bool = False,
    gateway_id: str = None
) -> str:
    """
    Format a successful agent deployment response for clean console output.
    
    Args:
        agent_id: The deployed agent's ID
        agent_arn: The deployed agent's ARN
        name: Agent name
        purpose: Agent purpose
        capabilities: List of capabilities
        status: Agent status
        enable_code_interpreter: Whether Code Interpreter is enabled
        enable_browser: Whether Browser is enabled
        gateway_id: Optional gateway ID
    
    Returns:
        Formatted success message
    """
    
    # Build tools list
    tools = []
    if enable_code_interpreter:
        tools.append("Code Interpreter")
    if enable_browser:
        tools.append("Browser")
    if gateway_id:
        tools.append(f"Gateway Tools ({gateway_id})")
    
    tools_str = ", ".join(tools) if tools else "None"
    
    # Format capabilities
    caps_str = ", ".join(capabilities) if capabilities else "General"
    
    return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        ✅ AGENT DEPLOYED SUCCESSFULLY                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

🤖 Agent: {name}
📋 Purpose: {purpose}
🆔 Agent ID: {agent_id}
⚡ Status: {status}

🎯 Capabilities: {caps_str}
🛠️  Tools: {tools_str}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The agent is ready to use! Invoke it with:

  Agent ARN: {agent_arn}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()


def format_deployment_error(error_type: str, error_message: str, suggestions: list[str] = None) -> str:
    """
    Format a deployment error message for clean console output.
    
    Args:
        error_type: Type of error (e.g., "Permission Denied", "Validation Error")
        error_message: The error message
        suggestions: Optional list of suggestions to fix the issue
    
    Returns:
        Formatted error message
    """
    
    result = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                          ❌ DEPLOYMENT FAILED                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Error: {error_type}

{error_message}
"""
    
    if suggestions:
        result += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        result += "\n💡 Suggestions:\n"
        for i, suggestion in enumerate(suggestions, 1):
            result += f"  {i}. {suggestion}\n"
    
    result += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    return result.strip()


def format_agent_update(agent_id: str, name: str, status: str = "UPDATED") -> str:
    """
    Format an agent update response.
    
    Args:
        agent_id: The agent's ID
        name: Agent name
        status: Update status
    
    Returns:
        Formatted update message
    """
    
    return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         ✅ AGENT UPDATED SUCCESSFULLY                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

🤖 Agent: {name}
🆔 Agent ID: {agent_id}
⚡ Status: {status}

The existing agent has been updated with the new configuration.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()
