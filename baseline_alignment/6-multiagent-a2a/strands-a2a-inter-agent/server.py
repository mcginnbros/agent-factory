"""
MCP Server: Employee Data Provider
===================================
This MCP server exposes employee data through the Model Context Protocol.
It provides tools for querying employee skills and finding employees by skill.

Architecture Role:
This is the data layer of our A2A system. It doesn't contain any AI logic,
just pure data access functions exposed as MCP tools.
"""

# ============================================================================
# STEP 1: Import Required Components
# ============================================================================
from mcp.server.fastmcp import FastMCP
from employee_data import SKILLS, EMPLOYEES


# ============================================================================
# STEP 2: Initialize MCP Server
# ============================================================================
# Create a FastMCP server instance
# - stateless_http=True: Each request is independent (no session state)
# - host="0.0.0.0": Listen on all network interfaces
# - port=8002: The port for this MCP server
mcp = FastMCP("employee-server", stateless_http=True, host="0.0.0.0", port=8002)


# ============================================================================
# STEP 3: Define MCP Tools
# ============================================================================
# Tools are functions that agents can call to access data or functionality

@mcp.tool()
def get_skills() -> set[str]:
    """
    Get all available skills in the employee database.
    
    This tool returns the complete list of skills that employees may have.
    Useful for discovering what skills to search for or understanding
    the skill taxonomy.
    
    Returns:
        set[str]: Set of all unique skills in the database
    """
    print("🔍 Tool called: get_skills")
    return SKILLS


@mcp.tool()
def get_employees_with_skill(skill: str) -> list[dict]:
    """
    Find all employees who have a specific skill.
    
    This tool searches the employee database for anyone with the specified
    skill. The search is case-insensitive.
    
    Args:
        skill (str): The skill to search for (e.g., "Python", "AWS", "React")
    
    Returns:
        list[dict]: List of employees with the skill, each containing:
            - name: Full name (First Last)
            - skills: List of all skills the employee has
    
    Raises:
        ValueError: If no employees have the specified skill
    """
    print(f"🔍 Tool called: get_employees_with_skill(skill='{skill}')")
    
    # Perform case-insensitive skill search
    skill_lower = skill.lower()
    employees_with_skill = [
        employee for employee in EMPLOYEES 
        if any(s.lower() == skill_lower for s in employee["skills"])
    ]
    
    # Validate that we found at least one employee
    if not employees_with_skill:
        raise ValueError(f"No employees have the '{skill}' skill")
    
    return employees_with_skill


# ============================================================================
# STEP 4: Run the Server
# ============================================================================
if __name__ == "__main__":
    # Start the MCP server using streamable HTTP transport
    # This allows agents to connect and call our tools
    print("🚀 Starting Employee MCP Server on port 8002...")
    print("📋 Available tools:")
    print("   - get_skills(): Get all available skills")
    print("   - get_employees_with_skill(skill): Find employees by skill")
    print()
    
    mcp.run(transport="streamable-http")


# ============================================================================
# MCP Server Concepts:
# ============================================================================
# - Tools: Functions exposed to agents via MCP protocol
# - Stateless: Each request is independent (no session management)
# - HTTP Transport: Tools are called via HTTP requests
# - Type Hints: Python type hints define the tool interface
# - Docstrings: Tool descriptions help agents understand usage
#
# Why Use MCP for Data Access?
# - Standardized protocol for agent-to-service communication
# - Easy to add new tools without changing agent code
# - Can be used by multiple agents simultaneously
# - Clear separation between data and AI logic
# - Built-in error handling and validation