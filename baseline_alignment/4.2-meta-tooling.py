"""
4.2: Meta-Tooling - Self-Extending Agents
===================================================
This advanced example demonstrates "meta-tooling" - agents that can create
their own tools on-the-fly and immediately use them!

This is a powerful pattern where the agent:
1. Recognizes it needs a new capability
2. Writes Python code to create that tool
3. Immediately uses the newly created tool

Think of it as an agent that can "learn" new skills during execution!
"""

# ============================================================================
# STEP 1: Import Required Components
# ============================================================================
import os
from dotenv import load_dotenv

from strands import Agent
from strands_tools import editor  # Allows the agent to create/edit files
from strands.models import BedrockModel


# ============================================================================
# STEP 2: Configure the Model
# ============================================================================
# Use Claude Sonnet for strong code generation capabilities
model = BedrockModel(
    model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    streaming=True
)


# ============================================================================
# STEP 3: Create Self-Extending Agent
# ============================================================================
# This agent has special capabilities:
# - Can write Python files using the 'editor' tool
# - Can automatically load and use tools from the tools/ directory
agent = Agent(
    model=model,
    
    # System prompt teaches the agent how to create new tools
    system_prompt="""
    Goal:
    - Create a python tool under cwd()/tools/*.py using given python tool decorator.
    - I have hot-reloading abilities, after writing the file, I can use it immediately.

    Building tools:

    from strands import tool

    @tool
    def name(name: str, description: str) -> str:
        '''
        Create a tool under cwd()/tools/*.py.
        '''
        return ""
        
    """,
    
    # Provide the editor tool so the agent can create new files
    tools=[editor],
    
    # CRITICAL: Enable hot-reloading of tools from the tools/ directory
    # This allows the agent to immediately use tools it just created!
    load_tools_from_directory=True
)


# ============================================================================
# STEP 4: Example Usage (Optional)
# ============================================================================
# Example prompt showing the agent creating and using multiple tools
prompt = """
Create a tool to add two numbers and then use it to add 5 and 7.
Then create a tool to calculate compound interest and use it to find the value of $1000 at 5% annual interest for 3 years.
"""


# ============================================================================
# STEP 5: Interactive Demo Loop
# ============================================================================
# Run an interactive session where you can ask the agent to create tools
print("\n" + "="*70)
print("Welcome to the Self-Extending Agent Demo!")
print("="*70)
print("\nThis agent can create new tools on-the-fly and immediately use them!")
print("\nType 'exit' or 'quit' to end the session.")
print("\nExample queries:")
print("  - Create a tool to add two numbers")
print("  - Create a tool to fetch weather data")
print("  - Create a tool to send a message")
print("  - Create a tool to calculate compound interest")
print("="*70 + "\n")

# Interactive loop
while True:
    # Get user input
    query = input("\nUser> ").strip()
    
    # Skip empty inputs
    if query == "":
        continue
    
    # Exit condition
    if query.lower() in ["exit", "quit"]:
        print("\nGoodbye!")
        break
    
    # Process the query
    # The agent will:
    # 1. Determine if it needs a new tool
    # 2. Create the tool using the editor
    # 3. Load the tool automatically
    # 4. Use the tool to answer your question
    agent(query)


# ============================================================================
# How Meta-Tooling Works:
# ============================================================================
# 1. User asks for something the agent can't do yet
# 2. Agent recognizes it needs a new capability
# 3. Agent uses 'editor' tool to write a new Python tool file
# 4. Strands automatically detects the new file (hot-reload)
# 5. Agent can now use the newly created tool
# 6. Tool persists for future use!
#
# Real-World Applications:
# - Rapidly prototyping new capabilities
# - Adapting to unexpected requirements
# - Building domain-specific tool libraries
# - Creating custom integrations on-demand
#
# Safety Considerations:
# - Review generated tools before production use
# - Consider sandboxing tool execution
# - Implement code review workflows
# - Monitor tool creation and usage
