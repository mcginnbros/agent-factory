"""
SigV4 Transport for MCP Client

Provides AWS SigV4 authentication for MCP client connections to AgentCore Gateway.

Based on AWS sample: amazon-bedrock-agentcore-samples/01-tutorials/01-AgentCore-runtime/02-hosting-MCP-server/streamable_http_sigv4.py
"""

from typing import Generator
import httpx
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from mcp.client.streamable_http import streamablehttp_client


class SigV4HTTPXAuth(httpx.Auth):
    """
    HTTPX authentication class that signs requests with AWS SigV4.
    
    This ensures each request is signed individually with the correct timestamp
    and request-specific data, which is required for AWS IAM authentication.
    """
    
    def __init__(self, credentials, service: str, region: str):
        """
        Initialize SigV4 auth handler.
        
        Args:
            credentials: AWS credentials from boto3 session
            service: AWS service name (bedrock-agentcore-gateway)
            region: AWS region
        """
        self.credentials = credentials
        self.service = service
        self.region = region
        self.signer = SigV4Auth(credentials, service, region)
    
    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        """
        Sign the request with SigV4 before sending.
        
        This method is called by httpx for each request.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Create headers dict and remove 'connection' header
        # The 'connection' header is not used in calculating the request
        # signature on the server-side, and results in a signature mismatch if included
        headers = dict(request.headers)
        headers.pop("connection", None)  # Remove if present, ignore if not
        
        logger.info(f"Signing request: {request.method} {request.url}")
        logger.info(f"Headers before signing: {list(headers.keys())}")
        
        # Create AWS request for signing
        aws_request = AWSRequest(
            method=request.method,
            url=str(request.url),
            data=request.content,
            headers=headers
        )
        
        # Sign the request with SigV4
        self.signer.add_auth(aws_request)
        
        logger.info(f"Headers after signing: {list(aws_request.headers.keys())}")
        logger.info(f"Authorization header present: {'Authorization' in aws_request.headers}")
        
        # Update request headers with signed headers
        request.headers.update(dict(aws_request.headers))
        
        # Yield the request to continue the flow
        yield request


def streamablehttp_client_with_sigv4(url: str, credentials, service: str, region: str):
    """
    Create a streamable HTTP client with AWS SigV4 authentication.
    
    Args:
        url: Gateway MCP URL
        credentials: AWS credentials from boto3 session
        service: AWS service name (bedrock-agentcore-gateway)
        region: AWS region
    
    Returns:
        Streamable HTTP client transport with SigV4 auth
    """
    # Create SigV4 auth handler
    auth = SigV4HTTPXAuth(credentials, service, region)
    
    # Return the streamable HTTP client with SigV4 auth
    # The auth parameter will be used by httpx to sign each request
    return streamablehttp_client(url, auth=auth)
