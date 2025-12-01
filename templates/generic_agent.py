"""
Generic Agent - Configurable via Environment Variables

Supports:
- Custom system prompts
- AgentCore Gateway integration
- Built-in tools (Code Interpreter, Browser)
- A2A Server (exposes endpoint on port 9000)
- A2A Client (calls other agents)
- AgentCore Memory (always enabled)
"""

import os
import logging
from strands import Agent
from strands.models import BedrockModel
from strands.multiagent.a2a import A2AServer
from bedrock_agentcore.memory import MemoryClient
from services.memory_hooks import AgentCoreMemoryHook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment
REGION = os.getenv('AWS_REGION', 'us-west-2')
MODEL_ID = os.getenv('MODEL_ID', 'us.anthropic.claude-haiku-4-5-20251001-v1:0')
SYSTEM_PROMPT = os.getenv('SYSTEM_PROMPT', 'You are a helpful AI assistant.')
AGENT_NAME = os.getenv('AGENT_NAME', 'Generic Agent')
AGENT_PURPOSE = os.getenv('AGENT_PURPOSE', 'General assistance')
GATEWAY_ID = os.getenv('GATEWAY_ID')
ENABLE_CODE_INTERPRETER = os.getenv('ENABLE_CODE_INTERPRETER', 'false').lower() == 'true'
ENABLE_BROWSER = os.getenv('ENABLE_BROWSER', 'false').lower() == 'true'
AGENT_MODE = os.getenv('AGENT_MODE', 'server')  # 'server' or 'client'
KNOWN_AGENT_IDS = os.getenv('KNOWN_AGENT_IDS', '')  # Comma-separated agent IDs
MEMORY_ID = os.getenv('BEDROCK_AGENTCORE_MEMORY_ID')

logger.info(f"Initializing {AGENT_NAME}")
logger.info(f"Mode: {AGENT_MODE.upper()}")
logger.info(f"Model: {MODEL_ID}")
logger.info(f"Memory: {'Enabled' if MEMORY_ID else 'Disabled'}")
if GATEWAY_ID:
    logger.info(f"Gateway: {GATEWAY_ID}")
if ENABLE_CODE_INTERPRETER:
    logger.info("Code Interpreter: Enabled")
if ENABLE_BROWSER:
    logger.info("Browser: Enabled")
if AGENT_MODE == 'client' and KNOWN_AGENT_IDS:
    agent_ids = [aid.strip() for aid in KNOWN_AGENT_IDS.split(',') if aid.strip()]
    logger.info(f"Known agents: {len(agent_ids)}")


def _construct_a2a_url(agent_id: str) -> str:
    """Construct A2A URL from agent ID"""
    import boto3
    from urllib.parse import quote
    
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    response = client.get_agent_runtime(agentRuntimeId=agent_id)
    agent_arn = response['agentRuntimeArn']
    escaped_arn = quote(agent_arn, safe='')
    return f"https://bedrock-agentcore.{REGION}.amazonaws.com/runtimes/{escaped_arn}/invocations/"


def create_agent(session_id="default-session", actor_id="default-user"):
    """Create and configure the agent"""
    logger.info(f"Creating agent (session={session_id}, actor={actor_id})...")
    
    model = BedrockModel(model_id=MODEL_ID, region_name=REGION)
    
    # Built-in tools
    builtin_tools = []
    
    if ENABLE_CODE_INTERPRETER:
        try:
            from strands_tools.code_interpreter import AgentCoreCodeInterpreter
            code_interpreter = AgentCoreCodeInterpreter(region=REGION)
            builtin_tools.append(code_interpreter.code_interpreter)
            logger.info("Added Code Interpreter")
        except Exception as e:
            logger.warning(f"Code Interpreter failed: {e}")
    
    if ENABLE_BROWSER:
        try:
            from strands_tools.browser import AgentCoreBrowser
            browser = AgentCoreBrowser(region=REGION)
            builtin_tools.append(browser.browser)
            logger.info("Added Browser")
        except Exception as e:
            logger.warning(f"Browser failed: {e}")
    
    # A2A client tools (for CLIENT mode)
    a2a_tools = []
    if AGENT_MODE == 'client' and KNOWN_AGENT_IDS:
        try:
            from strands_tools.a2a_client import A2AClientToolProvider
            from utils.sigv4_transport import SigV4HTTPXAuth
            import boto3
            
            agent_ids = [aid.strip() for aid in KNOWN_AGENT_IDS.split(',') if aid.strip()]
            if agent_ids:
                # Construct URLs from agent IDs
                known_urls = [_construct_a2a_url(aid) for aid in agent_ids]
                
                session = boto3.Session()
                credentials = session.get_credentials()
                
                a2a_provider = A2AClientToolProvider(
                    known_agent_urls=known_urls,
                    httpx_client_args={
                        'auth': SigV4HTTPXAuth(credentials, 'bedrock-agentcore', REGION),
                        'timeout': 60.0
                    }
                )
                a2a_tools = a2a_provider.tools
                logger.info(f"Added {len(a2a_tools)} A2A client tools")
        except Exception as e:
            logger.warning(f"A2A client failed: {e}")
    
    # Gateway tools (for SERVER mode)
    gateway_tools = []
    if GATEWAY_ID:
        try:
            from strands.tools.mcp.mcp_client import MCPClient
            from utils.sigv4_transport import streamablehttp_client_with_sigv4
            import boto3
            
            gateway_url = f"https://{GATEWAY_ID}.gateway.bedrock-agentcore.{REGION}.amazonaws.com/mcp"
            session = boto3.Session()
            credentials = session.get_credentials()
            
            # Keep MCP client session alive
            global _mcp_client_global
            _mcp_client_global = MCPClient(
                lambda: streamablehttp_client_with_sigv4(
                    url=gateway_url,
                    credentials=credentials,
                    service="bedrock-agentcore",
                    region=REGION
                )
            )
            _mcp_client_global.start()
            gateway_tools = _mcp_client_global.list_tools_sync()
            logger.info(f"Gateway: {len(gateway_tools)} tools")
        except Exception as e:
            logger.error(f"Gateway failed: {e}", exc_info=True)
    
    # Combine tools
    all_tools = builtin_tools + a2a_tools + gateway_tools
    logger.info(f"Total tools: {len(all_tools)}")
    
    # Memory hook (always enabled)
    hooks = []
    if MEMORY_ID:
        memory_client = MemoryClient(region_name=REGION)
        memory_hook = AgentCoreMemoryHook(
            memory_client=memory_client,
            memory_id=MEMORY_ID,
            session_id=session_id,
            actor_id=actor_id,
            history_turns=5
        )
        hooks.append(memory_hook)
    
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=all_tools,
        hooks=hooks,
        callback_handler=None,
        name=AGENT_NAME,
        description=AGENT_PURPOSE
    )


if __name__ == "__main__":
    if AGENT_MODE == 'server':
        # SERVER MODE: Exposes A2A endpoint on port 9000
        logger.info("=" * 80)
        logger.info(f"Starting {AGENT_NAME} - SERVER MODE")
        logger.info("=" * 80)
        
        agent = create_agent(session_id=AGENT_NAME, actor_id="user001")
        
        # Construct runtime URL from agent's own ARN
        import boto3
        from urllib.parse import quote
        
        # Get own agent ID from environment or metadata
        # For now, use a placeholder - the A2A server will use the invocation URL
        runtime_url = os.getenv('AGENTCORE_RUNTIME_URL')
        if not runtime_url:
            # Fallback: try to get from metadata or use local
            runtime_url = 'http://127.0.0.1:9000/'
            logger.warning(f"Using fallback runtime URL: {runtime_url}")
        
        a2a_server = A2AServer(
            agent=agent,
            host="0.0.0.0",
            port=9000,
            http_url=runtime_url,
            serve_at_root=True,
            version="1.0.0"
        )
        
        from fastapi import FastAPI
        import uvicorn
        
        app = FastAPI()
        
        @app.get("/health")
        def health():
            return {"status": "healthy", "agent": AGENT_NAME, "mode": "server"}
        
        app.mount("/", a2a_server.to_fastapi_app())
        
        logger.info("Server ready on port 9000")
        logger.info("=" * 80)
        
        uvicorn.run(app, host="0.0.0.0", port=9000)
        
    else:
        # CLIENT MODE: Uses AgentCore Runtime invocation
        logger.info("=" * 80)
        logger.info(f"Starting {AGENT_NAME} - CLIENT MODE")
        logger.info("=" * 80)
        
        from bedrock_agentcore.runtime import BedrockAgentCoreApp
        
        app = BedrockAgentCoreApp()
        
        @app.entrypoint
        def invoke_agent(payload, context):
            try:
                user_input = payload.get("prompt", "")
                session_id = payload.get("session_id", "default-session")
                actor_id = payload.get("actor_id", "default-user")
                
                if not user_input:
                    return {"result": "Please provide a message or question."}
                
                agent = create_agent(session_id=session_id, actor_id=actor_id)
                response_message = agent(user_input)
                
                return {"result": str(response_message)}
                
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
                return {"result": f"Error: {str(e)}"}
        
        logger.info("Client ready")
        logger.info("=" * 80)
        
        app.run()
