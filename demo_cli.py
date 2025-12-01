#!/usr/bin/env python3
"""
AgentCore Factory - Interactive Demo CLI

Beautiful terminal interface for demonstrating:
- Building agents with the Builder Agent
- Invoking deployed agents with JSON-RPC
- Viewing agent list and memory stats
"""

import boto3
import json
import time
import uuid
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.markdown import Markdown
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.theme import Theme

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    # dotenv not installed, try to load manually
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

# Custom theme for white background - removes background from inline code
custom_theme = Theme({
    "markdown.code": "bold blue",  # No background color
})

console = Console(theme=custom_theme)

REGION = os.getenv('AWS_REGION', 'us-west-2')
BUILDER_ARN = os.getenv('BUILDER_AGENT_ARN', '').strip()

if not BUILDER_ARN:
    console.print("[bold red]Error: BUILDER_AGENT_ARN environment variable not set[/bold red]")
    console.print("[yellow]Please set it in your .env file after deploying the builder agent[/yellow]")
    console.print()
    sys.exit(1)


class AgentCoreDemo:
    def __init__(self):
        self.client = boto3.client('bedrock-agentcore', region_name=REGION)
        self.control_client = boto3.client('bedrock-agentcore-control', region_name=REGION)
        self.current_agent = None
        self.session_id = None
        
    def show_banner(self):
        """Display welcome banner"""
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           🤖 AgentCore Factory - Interactive Demo            ║
║                                                               ║
║  Build and deploy AI agents with natural language            ║
║  Powered by AWS Bedrock AgentCore Runtime                    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
        """
        console.print(banner, style="bold blue")
        console.print()
    
    def list_agents(self) -> List[Dict]:
        """List all deployed agents with their invocation mode"""
        try:
            response = self.control_client.list_agent_runtimes()
            agents = []
            for runtime in response.get('agentRuntimes', []):
                if runtime.get('status') == 'READY':
                    agent_id = runtime['agentRuntimeId']
                    
                    # Get agent details to check mode
                    try:
                        details = self.control_client.get_agent_runtime(agentRuntimeId=agent_id)
                        env_vars = details.get('environmentVariables', {})
                        agent_mode = env_vars.get('AGENT_MODE', 'server')  # Default to server
                        protocol_config = details.get('protocolConfiguration', {})
                        has_a2a_protocol = protocol_config.get('serverProtocol') == 'A2A'
                    except:
                        # If we can't get details, assume server mode
                        agent_mode = 'server'
                        has_a2a_protocol = False
                    
                    agents.append({
                        'id': agent_id,
                        'name': runtime.get('agentRuntimeName', 'unknown'),
                        'arn': runtime['agentRuntimeArn'],
                        'status': runtime['status'],
                        'mode': agent_mode,
                        'use_jsonrpc': has_a2a_protocol  # Use JSON-RPC for A2A server agents
                    })
            return agents
        except Exception as e:
            console.print(f"[red]Error listing agents: {e}[/red]")
            return []
    
    def show_agent_list(self, show_a2a_urls=False):
        """Display table of available agents"""
        agents = self.list_agents()
        
        table = Table(title="🤖 Available Agents", box=box.ROUNDED, title_style="bold blue")
        table.add_column("#", style="bold blue", width=3)
        table.add_column("Name", style="bold green")
        table.add_column("Mode", style="bold cyan", width=8)
        table.add_column("Status", style="bold magenta")
        table.add_column("ID", style="blue")
        
        if show_a2a_urls:
            table.add_column("A2A URL", style="dark_blue", overflow="fold")
        
        for idx, agent in enumerate(agents, 1):
            status_icon = "✅" if agent['status'] == 'READY' else "⏳"
            mode_icon = "🔄" if agent['mode'] == 'client' else "🌐"
            
            row = [
                str(idx),
                agent['name'],
                f"{mode_icon} {agent['mode']}",
                f"{status_icon} {agent['status']}",
                agent['id']
            ]
            
            if show_a2a_urls:
                from urllib.parse import quote
                escaped_arn = quote(agent['arn'], safe='')
                a2a_url = f"https://bedrock-agentcore.{REGION}.amazonaws.com/runtimes/{escaped_arn}/invocations/"
                row.append(a2a_url)
            
            table.add_row(*row)
        
        console.print(table)
        console.print()
        return agents
    
    def send_to_builder(self, message: str) -> str:
        """Send message to builder agent"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[bold blue]Builder Agent is thinking...", total=None)
            
            # Prepare payload
            payload = {'prompt': message}
            # Session ID must be 33+ characters
            session_id = f'builder-session-{int(time.time())}-{uuid.uuid4().hex[:12]}'
            
            # Invoke builder
            response = self.client.invoke_agent_runtime(
                agentRuntimeArn=BUILDER_ARN,
                runtimeSessionId=session_id,
                payload=json.dumps(payload),
                qualifier='DEFAULT'
            )
            
            # Parse response
            response_body = response['response'].read().decode('utf-8')
            try:
                response_data = json.loads(response_body)
                result = response_data.get('result', response_body)
            except:
                result = response_body
            
            progress.update(task, completed=True)
        
        return result
    
    def send_to_agent(self, agent_arn: str, message: str, session_id: str, use_jsonrpc: bool = True) -> str:
        """Send message to deployed agent using appropriate format"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[bold blue]Agent is processing...", total=None)
            
            if use_jsonrpc:
                # JSON-RPC 2.0 format (for A2A server agents)
                message_id = f'msg-{uuid.uuid4().hex[:8]}'
                payload = {
                    'jsonrpc': '2.0',
                    'method': 'message/send',
                    'params': {
                        'message': {
                            'kind': 'message',
                            'role': 'user',
                            'parts': [{'kind': 'text', 'text': message}],
                            'messageId': message_id
                        }
                    },
                    'id': message_id
                }
            else:
                # Simple format (for AgentCore Runtime client agents)
                payload = {'prompt': message}
            
            # Invoke agent
            response = self.client.invoke_agent_runtime(
                agentRuntimeArn=agent_arn,
                runtimeSessionId=session_id,
                payload=json.dumps(payload),
                qualifier='DEFAULT'
            )
            
            # Parse response
            response_body = response['response'].read().decode('utf-8')
            response_data = json.loads(response_body)
            
            # Extract text based on format
            text = ""
            if use_jsonrpc:
                # JSON-RPC response format
                if 'result' in response_data and 'artifacts' in response_data['result']:
                    for artifact in response_data['result']['artifacts']:
                        if 'parts' in artifact:
                            for part in artifact['parts']:
                                if 'text' in part:
                                    text += part['text']
                
                # Check for JSON-RPC errors
                if 'error' in response_data:
                    error = response_data['error']
                    text = f"❌ Error: {error.get('message', 'Unknown error')}\n\nDetails: {json.dumps(error, indent=2)}"
            else:
                # Simple response format
                text = response_data.get('result', '')
            
            progress.update(task, completed=True)
        
        return text or "⚠️ No response received from agent (possible timeout or error)"
    
    def chat_with_builder(self):
        """Interactive chat with builder agent"""
        console.print(Panel.fit(
            "[bold blue]Builder Agent Chat[/bold blue]\n\n"
            "Ask the builder to create agents for you!\n"
            "Type 'back' to return to main menu",
            border_style="blue"
        ))
        console.print()
        
        while True:
            user_input = Prompt.ask("[bold dark_green]You[/bold dark_green]")
            
            if user_input.lower() in ['back', 'exit', 'quit']:
                break
            
            if not user_input.strip():
                continue
            
            # Send to builder
            response = self.send_to_builder(user_input)
            
            # Display response
            console.print()
            console.print(Panel(
                Markdown(response),
                title="[bold blue]🤖 Builder Agent[/bold blue]",
                border_style="dark_blue",
                padding=(1, 2)
            ))
            console.print()
    
    def chat_with_agent(self, agent: Dict):
        """Interactive chat with deployed agent"""
        mode_label = f"{agent['mode'].upper()} mode"
        invocation_type = "JSON-RPC (A2A)" if agent['use_jsonrpc'] else "AgentCore Runtime"
        
        console.print(Panel.fit(
            f"[bold blue]Chatting with: {agent['name']}[/bold blue]\n\n"
            f"[bold blue]Agent ID: {agent['id']}[/bold blue]\n"
            f"[bold cyan]Mode: {mode_label}[/bold cyan]\n"
            f"[bold cyan]Invocation: {invocation_type}[/bold cyan]\n"
            f"Memory: Enabled (session-based)\n\n"
            "Type 'back' to return to agent selection",
            border_style="blue"
        ))
        console.print()
        
        # Create session for this conversation (must be 33+ characters)
        session_id = f"demo-session-{int(time.time())}-{uuid.uuid4().hex[:12]}"
        
        while True:
            user_input = Prompt.ask("[bold dark_green]You[/bold dark_green]")
            
            if user_input.lower() in ['back', 'exit', 'quit']:
                break
            
            if not user_input.strip():
                continue
            
            # Send to agent using appropriate format
            response = self.send_to_agent(agent['arn'], user_input, session_id, agent['use_jsonrpc'])
            
            # Display response
            console.print()
            console.print(Panel(
                response,
                title=f"[bold blue]🤖 {agent['name']}[/bold blue]",
                border_style="dark_blue",
                padding=(1, 2)
            ))
            console.print()
    
    def select_agent(self):
        """Select an agent to chat with"""
        agents = self.show_agent_list()
        
        if not agents:
            console.print("[bold red]No agents available. Use the builder to create one![/bold red]")
            console.print()
            return
        
        choice = Prompt.ask(
            "[bold blue]Select agent number (or 'back')[/bold blue]",
            default="back"
        )
        
        if choice.lower() == 'back':
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(agents):
                self.chat_with_agent(agents[idx])
            else:
                console.print("[red]Invalid selection[/red]")
        except ValueError:
            console.print("[red]Please enter a number[/red]")
    
    def main_menu(self):
        """Display main menu"""
        while True:
            console.print()
            menu = Table(show_header=False, box=box.SIMPLE)
            menu.add_column(style="bold blue", width=3)
            menu.add_column(style="black")
            
            menu.add_row("1", "💬 Chat with Builder Agent (create new agents)")
            menu.add_row("2", "🤖 Chat with Deployed Agent")
            menu.add_row("3", "📋 List All Agents")
            menu.add_row("4", "🔗 Show A2A URLs (for agent connections)")
            menu.add_row("5", "🚪 Exit")
            
            console.print(Panel(menu, title="[bold blue]Main Menu[/bold blue]", border_style="blue"))
            
            choice = Prompt.ask("[bold blue]Select option[/bold blue]", choices=["1", "2", "3", "4", "5"])
            
            if choice == "1":
                self.chat_with_builder()
            elif choice == "2":
                self.select_agent()
            elif choice == "3":
                self.show_agent_list()
            elif choice == "4":
                self.show_agent_list(show_a2a_urls=True)
                console.print("[bold blue]💡 Tip: Copy these URLs to configure A2A connections between agents[/bold blue]")
                console.print()
            elif choice == "5":
                console.print("\n[bold blue]Thanks for using AgentCore Factory! 👋[/bold blue]\n")
                break
    
    def run(self):
        """Run the demo"""
        self.show_banner()
        self.main_menu()


if __name__ == "__main__":
    try:
        demo = AgentCoreDemo()
        demo.run()
    except KeyboardInterrupt:
        console.print("\n\n[bold blue]Demo interrupted. Goodbye! 👋[/bold blue]\n")
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]\n")
