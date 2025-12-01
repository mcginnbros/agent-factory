"""
AgentCore Memory Hooks

Simple hooks for integrating Strands agents with AgentCore Memory.
Provides short-term memory (conversation history) persistence.
"""

import logging
from bedrock_agentcore.memory import MemoryClient
from strands.hooks import AgentInitializedEvent, MessageAddedEvent, HookProvider

logger = logging.getLogger(__name__)


class AgentCoreMemoryHook(HookProvider):
    """
    Hook for AgentCore Memory integration.
    
    Automatically loads recent conversation history and saves new messages.
    """
    
    def __init__(self, memory_client: MemoryClient, memory_id: str, 
                 session_id: str, actor_id: str, history_turns: int = 5):
        """
        Initialize memory hook.
        
        Args:
            memory_client: AgentCore Memory client
            memory_id: Memory resource ID
            session_id: Session identifier
            actor_id: Actor/user identifier
            history_turns: Number of conversation turns to load (default: 5)
        """
        self.memory_client = memory_client
        self.memory_id = memory_id
        self.session_id = session_id
        self.actor_id = actor_id
        self.history_turns = history_turns
    
    def on_agent_initialized(self, event):
        """Load recent conversation history when agent starts."""
        try:
            turns = self.memory_client.get_last_k_turns(
                memory_id=self.memory_id,
                actor_id=self.actor_id,
                session_id=self.session_id,
                k=self.history_turns
            )
            
            if turns:
                # Format conversation history
                context_lines = []
                for turn in turns:
                    for message in turn:
                        role = message.get('role', 'unknown')
                        content = message.get('content', {})
                        text = content.get('text', '') if isinstance(content, dict) else str(content)
                        context_lines.append(f"{role}: {text}")
                
                # Add to agent's system prompt
                context = "\n".join(context_lines)
                event.agent.system_prompt += f"\n\nPrevious conversation:\n{context}"
                
        except Exception as e:
            logger.warning(f"Failed to load conversation history: {e}")
    
    def on_message_added(self, event):
        """Save message to memory after it's added."""
        try:
            msg = event.agent.messages[-1]
            role = msg.get("role", "unknown")
            content = str(msg.get("content", ""))
            
            self.memory_client.create_event(
                memory_id=self.memory_id,
                actor_id=self.actor_id,
                session_id=self.session_id,
                messages=[(content, role)]
            )
                        
        except Exception as e:
            logger.warning(f"Failed to save message to memory: {e}")
    
    def register_hooks(self, registry):
        """Register event callbacks."""
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)
        registry.add_callback(MessageAddedEvent, self.on_message_added)
