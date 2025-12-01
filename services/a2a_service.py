"""
A2A Connection Service for AgentCore Factory

This module handles Agent-to-Agent (A2A) communication setup and management.
It provides functionality for connecting agents, managing A2A URLs, and
enabling agent discovery for inter-agent communication.

Phase Usage:
- Phase 6: Uncomment to enable A2A protocol support
- Phase 7: Used to demonstrate multi-agent communication

PHASE 6: This entire module is commented/inactive until Phase 6
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

from agent_registry import get_agent_registry
from utils.aws_helpers import AWSHelperError, get_boto3_client

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# EXCEPTIONS
# ============================================================================


class A2AServiceError(Exception):
    """Base exception for A2A service errors"""
    pass


class A2AConnectionError(A2AServiceError):
    """Raised when A2A connection setup fails"""
    pass


class A2ADiscoveryError(A2AServiceError):
    """Raised when agent discovery fails"""
    pass


class A2AValidationError(A2AServiceError):
    """Raised when A2A URL or configuration validation fails"""
    pass


# ============================================================================
# DATA CLASSES
# ============================================================================


@dataclass
class A2AConnection:
    """
    Represents an A2A connection between two agents.
    
    This dataclass defines the connection from a source agent to a target agent,
    including the target's A2A endpoint URL and identifying information.
    
    Attributes:
        source_agent_id: ID of the agent initiating the connection
        target_agent_id: ID of the target agent
        target_a2a_url: A2A protocol endpoint URL of the target agent
        target_agent_name: Human-readable name of the target agent
    
    Example:
        connection = A2AConnection(
            source_agent_id="builder-agent-abc123",
            target_agent_id="support-agent-xyz789",
            target_a2a_url="https://bedrock-agentcore.us-west-2.amazonaws.com/runtimes/...",
            target_agent_name="Customer Support Agent"
        )
    """
    source_agent_id: str
    target_agent_id: str
    target_a2a_url: str
    target_agent_name: str
    
    def __post_init__(self):
        """Validate connection data after initialization"""
        # Validate agent IDs are not empty
        if not self.source_agent_id or not self.source_agent_id.strip():
            raise A2AValidationError("source_agent_id cannot be empty")
        
        if not self.target_agent_id or not self.target_agent_id.strip():
            raise A2AValidationError("target_agent_id cannot be empty")
        
        # Validate A2A URL
        self._validate_a2a_url(self.target_a2a_url)
        
        # Validate agent name
        if not self.target_agent_name or not self.target_agent_name.strip():
            raise A2AValidationError("target_agent_name cannot be empty")
    
    def _validate_a2a_url(self, url: str) -> None:
        """
        Validate A2A URL format.
        
        Args:
            url: A2A URL to validate
        
        Raises:
            A2AValidationError: If URL is invalid
        """
        if not url or not url.strip():
            raise A2AValidationError("A2A URL cannot be empty")
        
        try:
            parsed = urlparse(url)
            
            # Check scheme is HTTPS
            if parsed.scheme != 'https':
                raise A2AValidationError(
                    f"A2A URL must use HTTPS protocol, got: {parsed.scheme}"
                )
            
            # Check hostname is present
            if not parsed.netloc:
                raise A2AValidationError("A2A URL must have a valid hostname")
            
            # Check it looks like an AWS AgentCore URL
            if 'bedrock-agentcore' not in parsed.netloc and 'amazonaws.com' not in parsed.netloc:
                logger.warning(
                    f"A2A URL does not appear to be an AWS AgentCore endpoint: {url}"
                )
            
        except Exception as e:
            if isinstance(e, A2AValidationError):
                raise
            raise A2AValidationError(f"Invalid A2A URL format: {str(e)}") from e
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert connection to dictionary for serialization"""
        return {
            "source_agent_id": self.source_agent_id,
            "target_agent_id": self.target_agent_id,
            "target_a2a_url": self.target_a2a_url,
            "target_agent_name": self.target_agent_name
        }


# ============================================================================
# A2A CONNECTION SERVICE
# ============================================================================


class A2AConnectionService:
    """
    Service for managing Agent-to-Agent (A2A) connections.
    
    This service provides functionality to:
    1. Add A2A connections between agents
    2. Retrieve connections for an agent
    3. Discover available A2A-enabled agents
    4. Update agent runtime environments with A2A configuration
    
    The service maintains connections and coordinates with the agent registry
    to enable agent discovery and communication.
    
    Usage:
        service = A2AConnectionService(region_name="us-west-2")
        
        # Add a connection from builder agent to support agent
        connection = service.add_connection(
            source_agent_id="builder-agent-abc",
            target_agent_id="support-agent-xyz",
            target_a2a_url="https://..."
        )
        
        # Get all connections for an agent
        connections = service.get_connections("builder-agent-abc")
        
        # Discover all A2A-enabled agents
        agents = service.discover_agents()
    """
    
    def __init__(self, region_name: str):
        """
        Initialize the A2A Connection Service.
        
        Args:
            region_name: AWS region for A2A operations
        
        Raises:
            A2AServiceError: If initialization fails
        """
        try:
            self.region_name = region_name
            
            logger.info(f"Initializing A2AConnectionService for region {region_name}")
            
            # Initialize boto3 clients
            # Note: AgentCore Runtime client for updating agent environments
            self.agentcore_client = get_boto3_client('bedrock-agent-runtime', region_name)
            
            # Get agent registry for discovery
            self.agent_registry = get_agent_registry()
            
            # In-memory storage for connections
            # In production, this could be backed by DynamoDB
            self._connections: Dict[str, List[A2AConnection]] = {}
            
            logger.info("A2AConnectionService initialized successfully")
            
        except AWSHelperError as e:
            logger.error(f"AWS initialization failed: {e}")
            raise A2AServiceError(f"Failed to initialize AWS clients: {str(e)}") from e
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise A2AServiceError(f"Service initialization failed: {str(e)}") from e
    
    # ========================================================================
    # PUBLIC API - CONNECTION MANAGEMENT
    # ========================================================================
    
    def add_connection(
        self,
        source_agent_id: str,
        target_agent_id: str,
        target_a2a_url: str
    ) -> A2AConnection:
        """
        Add an A2A connection from source agent to target agent.
        
        This method:
        1. Validates the connection parameters
        2. Retrieves target agent information from registry
        3. Creates the connection object
        4. Stores the connection
        5. Updates the source agent's runtime environment with the new connection
        
        Args:
            source_agent_id: ID of the agent initiating the connection
            target_agent_id: ID of the target agent
            target_a2a_url: A2A protocol endpoint URL of the target agent
        
        Returns:
            A2AConnection object representing the connection
        
        Raises:
            A2AConnectionError: If connection setup fails
            A2AValidationError: If parameters are invalid
        
        Example:
            connection = service.add_connection(
                source_agent_id="builder-agent-abc",
                target_agent_id="support-agent-xyz",
                target_a2a_url="https://bedrock-agentcore.us-west-2.amazonaws.com/..."
            )
            print(f"Connected to {connection.target_agent_name}")
        """
        try:
            logger.info(f"Adding A2A connection: {source_agent_id} -> {target_agent_id}")
            
            # Validate A2A URL before creating connection
            from utils.validation import validate_a2a_url, ValidationError as ValError
            try:
                validate_a2a_url(target_a2a_url)
                logger.info("A2A URL validated successfully")
            except ValError as e:
                logger.error(f"A2A URL validation failed: {e}")
                raise A2AValidationError(f"Invalid A2A URL: {str(e)}") from e
            
            # Get target agent from registry
            target_agent = self.agent_registry.get_agent(target_agent_id)
            if not target_agent:
                raise A2AConnectionError(
                    f"Target agent not found in registry: {target_agent_id}"
                )
            
            # Create connection object (validation happens in __post_init__)
            connection = A2AConnection(
                source_agent_id=source_agent_id,
                target_agent_id=target_agent_id,
                target_a2a_url=target_a2a_url,
                target_agent_name=target_agent.agent_name
            )
            
            # Store connection
            if source_agent_id not in self._connections:
                self._connections[source_agent_id] = []
            
            # Check if connection already exists
            existing = [
                c for c in self._connections[source_agent_id]
                if c.target_agent_id == target_agent_id
            ]
            
            if existing:
                logger.info(f"Connection already exists, updating: {target_agent_id}")
                # Remove old connection
                self._connections[source_agent_id] = [
                    c for c in self._connections[source_agent_id]
                    if c.target_agent_id != target_agent_id
                ]
            
            # Add new connection
            self._connections[source_agent_id].append(connection)
            
            logger.info(
                f"A2A connection added: {source_agent_id} -> "
                f"{target_agent.agent_name} ({target_agent_id})"
            )
            
            # Update source agent's runtime environment
            self._update_agent_environment(source_agent_id)
            
            return connection
            
        except A2AValidationError:
            raise
        except A2AConnectionError:
            raise
        except Exception as e:
            logger.error(f"Failed to add A2A connection: {e}")
            raise A2AConnectionError(
                f"Failed to add connection {source_agent_id} -> {target_agent_id}: {str(e)}"
            ) from e
    
    def get_connections(self, agent_id: str) -> List[A2AConnection]:
        """
        Get all A2A connections for an agent.
        
        Returns the list of connections where the specified agent is the source,
        i.e., the agents that this agent can communicate with.
        
        Args:
            agent_id: ID of the agent to get connections for
        
        Returns:
            List of A2AConnection objects
        
        Example:
            connections = service.get_connections("builder-agent-abc")
            for conn in connections:
                print(f"Can connect to: {conn.target_agent_name}")
        """
        connections = self._connections.get(agent_id, [])
        
        logger.info(
            f"Retrieved {len(connections)} A2A connection(s) for agent: {agent_id}"
        )
        
        return connections
    
    def discover_agents(self) -> List[Dict[str, Any]]:
        """
        Discover all available A2A-enabled agents.
        
        Queries the agent registry for all agents that have A2A URLs configured,
        making them available for inter-agent communication.
        
        Returns:
            List of dictionaries with agent information:
            [
                {
                    'agent_id': str,
                    'agent_name': str,
                    'agent_arn': str,
                    'a2a_url': str,
                    'capabilities': List[str]
                },
                ...
            ]
        
        Raises:
            A2ADiscoveryError: If discovery fails
        
        Example:
            agents = service.discover_agents()
            for agent in agents:
                print(f"Found: {agent['agent_name']} at {agent['a2a_url']}")
        """
        try:
            logger.info("Discovering A2A-enabled agents")
            
            # Get all agents with A2A URLs from registry
            a2a_agents = self.agent_registry.get_a2a_agents()
            
            # Convert to dictionary format
            agent_list = []
            for agent in a2a_agents:
                agent_info = {
                    'agent_id': agent.agent_id,
                    'agent_name': agent.agent_name,
                    'agent_arn': agent.agent_arn,
                    'a2a_url': agent.a2a_url,
                    'capabilities': agent.capabilities,
                    'status': agent.status
                }
                agent_list.append(agent_info)
            
            logger.info(f"Discovered {len(agent_list)} A2A-enabled agent(s)")
            
            for agent in agent_list:
                logger.debug(
                    f"  - {agent['agent_name']} ({agent['agent_id']}): "
                    f"{', '.join(agent['capabilities'])}"
                )
            
            return agent_list
            
        except Exception as e:
            logger.error(f"Agent discovery failed: {e}")
            raise A2ADiscoveryError(f"Failed to discover agents: {str(e)}") from e
    
    # ========================================================================
    # PRIVATE METHODS - RUNTIME ENVIRONMENT UPDATE
    # ========================================================================
    
    def _update_agent_environment(self, agent_id: str) -> None:
        """
        Update agent runtime environment variables with A2A configuration.
        
        This method updates the agent's runtime environment to include the
        KNOWN_AGENT_URLS variable with a comma-separated list of A2A URLs
        for all connected agents.
        
        Args:
            agent_id: ID of the agent to update
        
        Raises:
            A2AConnectionError: If environment update fails
        """
        try:
            logger.info(f"Updating runtime environment for agent: {agent_id}")
            
            # Get all connections for this agent
            connections = self.get_connections(agent_id)
            
            if not connections:
                logger.info("No connections to update")
                return
            
            # Build comma-separated list of A2A URLs
            known_agent_urls = ",".join([conn.target_a2a_url for conn in connections])
            
            logger.info(f"Setting KNOWN_AGENT_URLS with {len(connections)} URL(s)")
            logger.debug(f"KNOWN_AGENT_URLS: {known_agent_urls}")
            
            # Get agent from registry to get ARN
            agent = self.agent_registry.get_agent(agent_id)
            if not agent:
                raise A2AConnectionError(f"Agent not found in registry: {agent_id}")
            
            # PHASE 6: Actual implementation would call AgentCore Runtime API
            # to update the agent's environment variables
            # For code talk demo, we'll log the operation
            # In production, this would be:
            # response = self.agentcore_client.update_agent_runtime(
            #     runtimeArn=agent.agent_arn,
            #     environment={
            #         'KNOWN_AGENT_URLS': known_agent_urls
            #     },
            #     # Force :latest tag to use newest container
            #     containerImage=f"{container_uri}:latest"
            # )
            
            logger.info(f"Runtime environment updated successfully for agent: {agent_id}")
            logger.info(f"  Agent ARN: {agent.agent_arn}")
            logger.info(f"  Connected agents: {len(connections)}")
            
        except A2AConnectionError:
            raise
        except Exception as e:
            logger.error(f"Failed to update agent environment: {e}")
            raise A2AConnectionError(
                f"Failed to update environment for agent {agent_id}: {str(e)}"
            ) from e
    
    def _get_known_agent_urls(self, agent_id: str) -> List[str]:
        """
        Get list of known agent URLs for an agent.
        
        Helper method to retrieve the A2A URLs of all agents that
        the specified agent should be able to communicate with.
        
        Args:
            agent_id: ID of the agent
        
        Returns:
            List of A2A URL strings
        
        Example:
            urls = service._get_known_agent_urls("builder-agent-abc")
            # Returns: ["https://...", "https://..."]
        """
        connections = self.get_connections(agent_id)
        urls = [conn.target_a2a_url for conn in connections]
        
        logger.debug(f"Retrieved {len(urls)} known agent URL(s) for {agent_id}")
        
        return urls


# ============================================================================
# SINGLETON PATTERN
# Ensures a single service instance is shared across all modules
# ============================================================================

_a2a_service_instance: Optional[A2AConnectionService] = None


def get_a2a_connection_service(region_name: Optional[str] = None) -> A2AConnectionService:
    """
    Get or create a singleton A2AConnectionService instance.
    
    This ensures that all modules share the same service instance,
    maintaining consistency across the application.
    
    Args:
        region_name: AWS region (required on first call)
    
    Returns:
        A2AConnectionService singleton instance
    
    Raises:
        A2AServiceError: If region_name not provided on first call
    
    Example:
        # First call - initialize with region
        service = get_a2a_connection_service(region_name="us-west-2")
        
        # Subsequent calls - reuse instance
        service = get_a2a_connection_service()
        
        # Add connection
        service.add_connection(
            source_agent_id="agent-a",
            target_agent_id="agent-b",
            target_a2a_url="https://..."
        )
    """
    global _a2a_service_instance
    
    if _a2a_service_instance is None:
        if region_name is None:
            raise A2AServiceError(
                "region_name required for first call to get_a2a_connection_service()"
            )
        _a2a_service_instance = A2AConnectionService(region_name=region_name)
        logger.info("Created singleton A2A connection service instance")
    
    return _a2a_service_instance


def reset_a2a_connection_service():
    """
    Reset the singleton service instance (useful for testing).
    
    Warning: This will clear all A2A connections!
    """
    global _a2a_service_instance
    _a2a_service_instance = None
    logger.warning("A2A connection service has been reset")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def create_a2a_connection_service(region_name: str) -> A2AConnectionService:
    """
    Create an A2AConnectionService instance.
    
    Convenience function for creating a service with standard configuration.
    
    Args:
        region_name: AWS region
    
    Returns:
        Configured A2AConnectionService instance
    
    Example:
        service = create_a2a_connection_service(region_name="us-west-2")
        
        # Discover agents
        agents = service.discover_agents()
        
        # Add connections
        for agent in agents:
            if agent['agent_id'] != 'my-agent-id':
                service.add_connection(
                    source_agent_id='my-agent-id',
                    target_agent_id=agent['agent_id'],
                    target_a2a_url=agent['a2a_url']
                )
    """
    return A2AConnectionService(region_name=region_name)
