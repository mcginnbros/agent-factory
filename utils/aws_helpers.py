"""AWS SDK wrapper functions for AgentCore Factory.

This module provides helper functions for interacting with AWS services,
including ECR authentication, boto3 client creation, and resource validation.
"""

import base64
import logging
import subprocess
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class AWSHelperError(Exception):
    """Base exception for AWS helper errors."""
    pass


def get_boto3_client(service_name: str, region_name: Optional[str] = None) -> Any:
    """
    Create a boto3 client with error handling.
    
    Args:
        service_name: AWS service name (e.g., 'ecr', 'sts', 'bedrock-agent-runtime')
        region_name: AWS region name (defaults to environment or config)
        
    Returns:
        Configured boto3 client
        
    Raises:
        AWSHelperError: If client creation fails
        
    Example:
        >>> ecr_client = get_boto3_client('ecr', 'us-west-2')
        >>> sts_client = get_boto3_client('sts')
    """
    try:
        logger.info(f"Creating boto3 client for service: {service_name}, region: {region_name or 'default'}")
        
        if region_name:
            client = boto3.client(service_name, region_name=region_name)
        else:
            client = boto3.client(service_name)
            
        logger.debug(f"Successfully created {service_name} client")
        return client
        
    except NoCredentialsError as e:
        error_msg = (
            f"AWS credentials not found. Please configure credentials using "
            f"AWS CLI, environment variables, or IAM role."
        )
        logger.error(error_msg)
        raise AWSHelperError(error_msg) from e
        
    except ClientError as e:
        error_msg = f"Failed to create boto3 client for {service_name}: {e}"
        logger.error(error_msg)
        raise AWSHelperError(error_msg) from e
        
    except Exception as e:
        error_msg = f"Unexpected error creating boto3 client for {service_name}: {e}"
        logger.error(error_msg)
        raise AWSHelperError(error_msg) from e


def get_account_id() -> str:
    """
    Get the AWS account ID using STS.
    
    Returns:
        AWS account ID as string
        
    Raises:
        AWSHelperError: If unable to retrieve account ID
        
    Example:
        >>> account_id = get_account_id()
        >>> print(f"Account: {account_id}")
    """
    try:
        logger.info("Retrieving AWS account ID")
        sts_client = get_boto3_client('sts')
        response = sts_client.get_caller_identity()
        account_id = response['Account']
        logger.info(f"AWS Account ID: {account_id}")
        return account_id
        
    except Exception as e:
        error_msg = f"Failed to retrieve AWS account ID: {e}"
        logger.error(error_msg)
        raise AWSHelperError(error_msg) from e


def authenticate_ecr(region_name: str) -> Dict[str, str]:
    """
    Authenticate Docker with Amazon ECR.
    
    This function retrieves ECR authorization token and authenticates
    Docker CLI with the ECR registry.
    
    Args:
        region_name: AWS region for ECR
        
    Returns:
        Dictionary with 'registry', 'username', 'password'
        
    Raises:
        AWSHelperError: If ECR authentication fails
        
    Example:
        >>> auth = authenticate_ecr('us-west-2')
        >>> print(f"Authenticated with {auth['registry']}")
    """
    try:
        logger.info(f"Authenticating Docker with ECR in region: {region_name}")
        
        # Get ECR authorization token
        ecr_client = get_boto3_client('ecr', region_name)
        response = ecr_client.get_authorization_token()
        
        if not response.get('authorizationData'):
            raise AWSHelperError("No authorization data returned from ECR")
            
        auth_data = response['authorizationData'][0]
        auth_token = auth_data['authorizationToken']
        registry = auth_data['proxyEndpoint']
        
        # Decode the authorization token (it's base64 encoded username:password)
        decoded_token = base64.b64decode(auth_token).decode('utf-8')
        username, password = decoded_token.split(':', 1)
        
        logger.info(f"Retrieved ECR authorization token for registry: {registry}")
        
        # Authenticate Docker with ECR
        docker_login_cmd = [
            'docker', 'login',
            '--username', username,
            '--password-stdin',
            registry
        ]
        
        logger.debug("Executing Docker login command")
        result = subprocess.run(
            docker_login_cmd,
            input=password.encode('utf-8'),
            capture_output=True,
            check=True
        )
        
        logger.info(f"Successfully authenticated Docker with ECR: {registry}")
        
        return {
            'registry': registry.replace('https://', ''),
            'username': username,
            'password': password
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Docker login failed: {e.stderr.decode('utf-8') if e.stderr else str(e)}"
        logger.error(error_msg)
        raise AWSHelperError(error_msg) from e
        
    except ClientError as e:
        error_msg = f"ECR authentication failed: {e}"
        logger.error(error_msg)
        raise AWSHelperError(error_msg) from e
        
    except Exception as e:
        error_msg = f"Unexpected error during ECR authentication: {e}"
        logger.error(error_msg)
        raise AWSHelperError(error_msg) from e


def validate_execution_role(role_arn: str, region_name: Optional[str] = None) -> bool:
    """
    Validate that an IAM execution role exists and is accessible.
    
    Args:
        role_arn: IAM role ARN to validate
        region_name: AWS region (optional)
        
    Returns:
        True if role is valid and accessible
        
    Raises:
        AWSHelperError: If role validation fails
        
    Example:
        >>> role_arn = "arn:aws:iam::123456789012:role/AgentCoreExecutionRole"
        >>> if validate_execution_role(role_arn):
        ...     print("Role is valid")
    """
    try:
        logger.info(f"Validating execution role: {role_arn}")
        
        # Extract role name from ARN
        # Format: arn:aws:iam::account-id:role/role-name
        if not role_arn.startswith('arn:aws:iam::'):
            raise AWSHelperError(f"Invalid IAM role ARN format: {role_arn}")
            
        role_name = role_arn.split('/')[-1]
        
        # Get IAM client and check if role exists
        iam_client = get_boto3_client('iam', region_name)
        response = iam_client.get_role(RoleName=role_name)
        
        if response['Role']['Arn'] != role_arn:
            raise AWSHelperError(f"Role ARN mismatch: expected {role_arn}, got {response['Role']['Arn']}")
            
        logger.info(f"Execution role validated successfully: {role_name}")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            error_msg = f"Execution role not found: {role_arn}"
        else:
            error_msg = f"Failed to validate execution role: {e}"
        logger.error(error_msg)
        raise AWSHelperError(error_msg) from e
        
    except Exception as e:
        error_msg = f"Unexpected error validating execution role: {e}"
        logger.error(error_msg)
        raise AWSHelperError(error_msg) from e


def validate_ecr_repository(repository_name: str, region_name: str) -> bool:
    """
    Validate that an ECR repository exists, create if it doesn't.
    
    Args:
        repository_name: ECR repository name
        region_name: AWS region
        
    Returns:
        True if repository exists or was created
        
    Raises:
        AWSHelperError: If repository validation/creation fails
        
    Example:
        >>> if validate_ecr_repository('agentcore-agents/my-agent', 'us-west-2'):
        ...     print("Repository ready")
    """
    try:
        logger.info(f"Validating ECR repository: {repository_name} in {region_name}")
        
        ecr_client = get_boto3_client('ecr', region_name)
        
        # Try to describe the repository
        try:
            response = ecr_client.describe_repositories(
                repositoryNames=[repository_name]
            )
            logger.info(f"ECR repository exists: {repository_name}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'RepositoryNotFoundException':
                # Repository doesn't exist, create it
                logger.info(f"ECR repository not found, creating: {repository_name}")
                
                ecr_client.create_repository(
                    repositoryName=repository_name,
                    imageScanningConfiguration={'scanOnPush': True},
                    encryptionConfiguration={'encryptionType': 'AES256'}
                )
                
                logger.info(f"Successfully created ECR repository: {repository_name}")
                return True
            else:
                raise
                
    except ClientError as e:
        error_msg = f"Failed to validate/create ECR repository {repository_name}: {e}"
        logger.error(error_msg)
        raise AWSHelperError(error_msg) from e
        
    except Exception as e:
        error_msg = f"Unexpected error validating ECR repository: {e}"
        logger.error(error_msg)
        raise AWSHelperError(error_msg) from e


def ensure_ecr_repository(repository_name: str, region_name: str) -> str:
    """
    Ensure ECR repository exists and return its URI.
    
    Args:
        repository_name: ECR repository name
        region_name: AWS region
        
    Returns:
        ECR repository URI
        
    Raises:
        AWSHelperError: If repository operations fail
        
    Example:
        >>> uri = ensure_ecr_repository('agentcore-agents/my-agent', 'us-west-2')
        >>> print(f"Repository URI: {uri}")
    """
    try:
        validate_ecr_repository(repository_name, region_name)
        
        # Get repository URI
        ecr_client = get_boto3_client('ecr', region_name)
        response = ecr_client.describe_repositories(
            repositoryNames=[repository_name]
        )
        
        repository_uri = response['repositories'][0]['repositoryUri']
        logger.info(f"ECR repository URI: {repository_uri}")
        return repository_uri
        
    except Exception as e:
        error_msg = f"Failed to ensure ECR repository: {e}"
        logger.error(error_msg)
        raise AWSHelperError(error_msg) from e
