"""
List Available Tools

This tool provides information about all tools available to the Builder Agent.
"""

from strands import tool


@tool
def list_available_tools() -> str:
    """
    List all tools currently available to the Builder Agent.
    
    Returns:
        str: Formatted list of available tools with descriptions and parameters
    """
    tools_list = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    BUILDER AGENT - AVAILABLE TOOLS                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

🔧 CORE TOOLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. list_available_tools()
   📋 List all available tools (this tool)
   
2. browser(url, action)
   🌐 Browse websites and extract information
   • Useful for research, data gathering, web scraping
   • Can navigate, click, extract text, take screenshots

🤖 AGENT DEPLOYMENT TOOLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3. deploy_agent(name, purpose, capabilities, system_prompt, gateway_id, 
                enable_code_interpreter, enable_browser, known_agent_urls)
   🚀 Deploy new agents to AgentCore Runtime
   
   Parameters:
   • name: Agent name (e.g., "joke-generator")
   • purpose: Brief description of agent's purpose
   • capabilities: List of agent capabilities
   • system_prompt: System prompt defining agent behavior
   • gateway_id: (Optional) Gateway ID to connect agent to Lambda tools
   • enable_code_interpreter: (Optional) Enable Code Interpreter tool
   • enable_browser: (Optional) Enable Browser tool
   • known_agent_urls: (Optional) List of agent URLs for A2A communication
   
   Note: Uses pre-built generic agent container - no Docker build required!

4. list_deployed_agents()
   📋 List all deployed agents with their A2A URLs
   
   Use this to:
   • Find existing agents to connect to
   • Get A2A URLs for agent-to-agent communication
   • Check what agents are available

🔌 GATEWAY & LAMBDA TOOLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5. create_gateway(name, description)
   🌐 Create AgentCore Gateway for hosting Lambda-based tools
   
   Parameters:
   • name: Gateway name (e.g., "Order Management Gateway")
   • description: Gateway description
   
   Returns: Gateway ID to use with create_lambda_tools

6. create_lambda_tools(gateway_id, tools_spec)
   ⚡ Create Lambda functions as tools and register with gateway
   
   Parameters:
   • gateway_id: Gateway ID from create_gateway
   • tools_spec: JSON string with array of tool specifications
   
   Tool spec format:
   [
     {
       "name": "tool_name",
       "description": "Tool description",
       "input_schema": {
         "type": "object",
         "properties": {
           "param_name": {"type": "string"}
         },
         "required": ["param_name"]
       },
       "handler_code": "result = parameters.get('param_name'); return {'result': result}"
     }
   ]
   
   IMPORTANT: handler_code should:
   • Access parameters using: parameters.get('param_name', default)
   • Return a dictionary with results
   • NOT include function definitions or imports
   • Only contain the actual processing logic

🗄️  AVAILABLE DYNAMODB TABLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Lambda functions can access these DynamoDB tables:

📋 reInvent_agent_factory-time-off
   Purpose: Time off requests for HR agent
   Keys: user_id (HASH), request_id (RANGE)
   Fields: start_date, end_date, days, type (vacation/sick), status (approved/pending/denied)
   
   Example handler_code for querying:
   import boto3
   import os
   dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-west-2'))
   table = dynamodb.Table('reInvent_agent_factory-time-off')
   response = table.query(
       KeyConditionExpression='user_id = :uid',
       ExpressionAttributeValues={':uid': parameters.get('user_id')}
   )
   return {'requests': response.get('Items', [])}

💰 reInvent_agent_factory-expenses
   Purpose: Expense records for Expense agent
   Keys: user_id (HASH), expense_id (RANGE)
   Fields: date, amount, category, description, status (approved/pending/denied)
   
   Example handler_code for creating:
   import boto3
   import os
   from datetime import datetime
   dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-west-2'))
   table = dynamodb.Table('reInvent_agent_factory-expenses')
   expense_id = f"exp-{datetime.now().strftime('%Y%m%d%H%M%S')}"
   table.put_item(Item={
       'user_id': parameters.get('user_id'),
       'expense_id': expense_id,
       'date': parameters.get('date'),
       'amount': parameters.get('amount'),
       'category': parameters.get('category'),
       'description': parameters.get('description'),
       'status': 'pending'
   })
   return {'success': True, 'expense_id': expense_id}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 WORKFLOW EXAMPLES:

Simple Agent (no tools):
  1. deploy_agent(name="GreeterBot", purpose="Greet users", ...)

Agent with Lambda Tools:
  1. create_gateway(name="Calculator Gateway", ...)
  2. create_lambda_tools(gateway_id="...", tools_spec="[...]")
  3. deploy_agent(name="CalcBot", gateway_id="...", ...)

Agent with A2A Communication:
  1. list_deployed_agents() to get existing agent URLs
  2. deploy_agent(name="CoordinatorBot", known_agent_urls=["url1", "url2"], ...)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    return tools_list.strip()
