#!/usr/bin/env python3
"""
AWS Resource Setup Script for AgentCore Factory

This script provisions all necessary AWS resources for running the AgentCore Factory:
- IAM roles (AgentCore execution role, Lambda execution role)
- AgentCore Memory instance
- ECR repository
- Validates AWS credentials and permissions

Run this script once when setting up the project in a new AWS account.
"""

import boto3
import json
import sys
import time
from botocore.exceptions import ClientError

# Configuration
REGION = 'us-west-2'
PROJECT_NAME = 'reInvent_agent_factory'
AGENTCORE_ROLE_NAME = 'AgentCoreExecutionRole'
LAMBDA_ROLE_NAME = 'AgentCoreLambdaExecutionRole'
ECR_REPOSITORY_NAME = 'reinvent/agents'

# Colors for output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.END}\n")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def get_account_id():
    """Get AWS account ID"""
    try:
        sts = boto3.client('sts', region_name=REGION)
        return sts.get_caller_identity()['Account']
    except Exception as e:
        print_error(f"Failed to get AWS account ID: {e}")
        sys.exit(1)

def create_agentcore_execution_role(account_id):
    """Create IAM role for AgentCore Runtime with granular policies"""
    print_header("Checking AgentCore Execution Role")
    
    iam = boto3.client('iam', region_name=REGION)
    role_name = AGENTCORE_ROLE_NAME
    
    # Trust policy for AgentCore
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock-agentcore.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Granular policies matching existing AWS setup
    policies = {
        'AgentCoreA2AAccess': {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["bedrock-agentcore:*"],
                    "Resource": "*"
                }
            ]
        },
        'AgentCoreA2APermissions': {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AgentCoreA2APermissions",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock-agentcore:GetAgentCard",
                        "bedrock-agentcore:InvokeAgentRuntime"
                    ],
                    "Resource": "*"
                }
            ]
        },
        'AgentCoreBedrockAccess': {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "BedrockMarketplaceAccess",
                    "Effect": "Allow",
                    "Action": [
                        "aws-marketplace:Subscribe",
                        "aws-marketplace:Unsubscribe",
                        "aws-marketplace:ViewSubscriptions"
                    ],
                    "Resource": "*"
                }
            ]
        },
        'AgentCoreECRAccess': {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "VisualEditor0",
                    "Effect": "Allow",
                    "Action": "ecr:*",
                    "Resource": "*"
                }
            ]
        },
        'AgentCoreGatewayAccess': {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock-agentcore:InvokeGateway",
                        "bedrock-agentcore:GetGateway",
                        "bedrock-agentcore:ListGatewayTargets"
                    ],
                    "Resource": "*"
                }
            ]
        },
        'AgentCoreLambdaInvoke': {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["lambda:InvokeFunction"],
                    "Resource": f"arn:aws:lambda:{REGION}:{account_id}:function:gateway-*"
                }
            ]
        },
        'AgentCoreLambdaManagement': {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:CreateFunction",
                        "lambda:UpdateFunctionCode",
                        "lambda:UpdateFunctionConfiguration",
                        "lambda:GetFunction",
                        "lambda:DeleteFunction",
                        "lambda:AddPermission",
                        "lambda:RemovePermission",
                        "lambda:GetPolicy"
                    ],
                    "Resource": f"arn:aws:lambda:{REGION}:{account_id}:function:gateway-*"
                },
                {
                    "Effect": "Allow",
                    "Action": ["iam:PassRole"],
                    "Resource": [
                        f"arn:aws:iam::{account_id}:role/AgentCoreLambdaExecutionRole",
                        f"arn:aws:iam::{account_id}:role/AgentCoreExecutionRole"
                    ]
                }
            ]
        },
        'AgentCoreGatewayManagement': {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock-agentcore:CreateGateway",
                        "bedrock-agentcore:UpdateGateway",
                        "bedrock-agentcore:DeleteGateway",
                        "bedrock-agentcore:GetGateway",
                        "bedrock-agentcore:ListGateways",
                        "bedrock-agentcore:CreateGatewayTarget",
                        "bedrock-agentcore:UpdateGatewayTarget",
                        "bedrock-agentcore:DeleteGatewayTarget",
                        "bedrock-agentcore:ListGatewayTargets"
                    ],
                    "Resource": "*"
                }
            ]
        },
        'AgentCoreRuntimeManagement': {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock-agentcore:CreateAgentRuntime",
                        "bedrock-agentcore:UpdateAgentRuntime",
                        "bedrock-agentcore:DeleteAgentRuntime",
                        "bedrock-agentcore:GetAgentRuntime",
                        "bedrock-agentcore:ListAgentRuntimes"
                    ],
                    "Resource": "*"
                }
            ]
        },
        'AgentCoreLogsAccess': {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": f"arn:aws:logs:{REGION}:{account_id}:log-group:/aws/bedrock-agentcore/*"
                }
            ]
        },
        'AgentCoreMemoryAccess': {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock-agentcore:GetMemory",
                        "bedrock-agentcore:ListMemories",
                        "bedrock-agentcore:CreateMemory",
                        "bedrock-agentcore:DeleteMemory",
                        "bedrock-agentcore:UpdateMemory",
                        "bedrock-agentcore:InvokeAgent"
                    ],
                    "Resource": "*"
                }
            ]
        }
    }
    
    try:
        # Check if role exists
        try:
            role = iam.get_role(RoleName=role_name)
            print_info(f"Role {role_name} already exists")
            role_arn = role['Role']['Arn']
        except iam.exceptions.NoSuchEntityException:
            # Create role
            print_info(f"Creating role: {role_name}")
            role = iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Execution role for AgentCore Runtime agents'
            )
            role_arn = role['Role']['Arn']
            print_success(f"Created role: {role_name}")
        
        # Attach all granular policies
        for policy_name, policy_doc in policies.items():
            iam.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_doc)
            )
            print_success(f"Attached/Updated policy: {policy_name}")
        
        print_success(f"AgentCore Execution Role ARN: {role_arn}")
        return role_arn
        
    except Exception as e:
        print_error(f"Failed to create AgentCore execution role: {e}")
        sys.exit(1)

def create_lambda_execution_role(account_id):
    """Create IAM role for Lambda functions"""
    print_header("Checking Lambda Execution Role")
    
    iam = boto3.client('iam', region_name=REGION)
    role_name = LAMBDA_ROLE_NAME
    
    # Trust policy for Lambda
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Permissions policy matching existing AWS setup + DynamoDB access
    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                "Resource": f"arn:aws:dynamodb:{REGION}:{account_id}:table/{PROJECT_NAME}-*"
            }
        ]
    }
    
    try:
        # Check if role exists
        try:
            role = iam.get_role(RoleName=role_name)
            print_info(f"Role {role_name} already exists")
            role_arn = role['Role']['Arn']
        except iam.exceptions.NoSuchEntityException:
            # Create role
            print_info(f"Creating role: {role_name}")
            role = iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Execution role for Lambda functions used as agent tools'
            )
            role_arn = role['Role']['Arn']
            print_success(f"Created role: {role_name}")
        
        # Attach inline policy
        policy_name = 'LambdaExecutionPolicy'
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(permissions_policy)
        )
        print_success(f"Attached/Updated policy: {policy_name}")
        
        print_success(f"Lambda Execution Role ARN: {role_arn}")
        return role_arn
        
    except Exception as e:
        print_error(f"Failed to create Lambda execution role: {e}")
        sys.exit(1)

def create_agentcore_memory(account_id):
    """Create AgentCore Memory instance"""
    print_header("Checking AgentCore Memory")
    
    agentcore = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    try:
        # Convert PROJECT_NAME to valid format (replace hyphens with underscores)
        project_name_normalized = PROJECT_NAME.replace("-", "_")
        
        # List existing memories
        response = agentcore.list_memories()
        existing_memories = response.get('memories', [])
        
        print_info(f"Found {len(existing_memories)} existing memories")
        
        # Check if memory starting with PROJECT_NAME exists
        # Note: list_memories() doesn't return 'name' field, but the 'id' contains the name as prefix
        for memory in existing_memories:
            memory_id = memory.get('id') or memory.get('memoryId') or ''
            
            # The memory ID format is: <name>-<suffix> or <name>_<suffix>-<suffix>
            # Check if the ID starts with our project name
            if memory_id.startswith(project_name_normalized):
                print_info(f"Found existing memory with ID: {memory_id}")
                print_success(f"Memory ID: {memory_id}")
                return memory_id
        
        print_info(f"No existing memory found matching '{project_name_normalized}'")
        
        # Create new memory
        # Note: Memory name must match pattern [a-zA-Z][a-zA-Z0-9_]{0,47}
        # Cannot contain hyphens, must use underscores
        # AgentCore will auto-generate a suffix for uniqueness
        memory_name = project_name_normalized
        
        print_info(f"Creating new memory: {memory_name}")
        
        # Updated API parameters - eventExpiryDuration is just an integer (days)
        # memoryStrategies is a list of strategy configurations
        response = agentcore.create_memory(
            name=memory_name,
            description='Shared memory for AgentCore Factory agents',
            eventExpiryDuration=90  # Number of days to retain events
        )
        
        # The response contains a 'memory' object with 'id' field (not 'memoryId')
        memory = response.get('memory', {})
        memory_id = memory.get('id') or memory.get('memoryId')
        
        if not memory_id:
            raise ValueError(f"No memory ID in response: {response}")
        
        print_success(f"Created memory: {memory_name}")
        print_success(f"Memory ID: {memory_id}")
        return memory_id
        
    except Exception as e:
        error_msg = str(e)
        # If memory already exists, try to find it by name
        if "already exists" in error_msg:
            print_warning(f"Memory creation failed because it already exists")
            print_info("Attempting to find existing memory by name...")
            try:
                response = agentcore.list_memories()
                existing_memories = response.get('memories', [])
                for memory in existing_memories:
                    memory_name = memory.get('name', '')
                    if project_name_normalized in memory_name:
                        memory_id = memory.get('id') or memory.get('memoryId')
                        print_success(f"Found existing memory: {memory_name}")
                        print_success(f"Memory ID: {memory_id}")
                        return memory_id
            except Exception as list_error:
                print_error(f"Failed to list memories: {list_error}")
        
        print_error(f"Failed to create AgentCore Memory: {e}")
        print_warning("Continuing without memory - agents will work but won't have conversation history")
        return None

def create_dynamodb_tables(account_id):
    """Create DynamoDB tables for HR and Expense agents"""
    print_header("Creating DynamoDB Tables")
    
    dynamodb = boto3.client('dynamodb', region_name=REGION)
    
    tables = [
        {
            'name': f'{PROJECT_NAME}-time-off',
            'description': 'Time off requests for HR agent',
            'key_schema': [
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'request_id', 'KeyType': 'RANGE'}
            ],
            'attribute_definitions': [
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'request_id', 'AttributeType': 'S'}
            ],
            'seed_data': [
                {
                    'user_id': {'S': 'user001'},
                    'request_id': {'S': 'req-001'},
                    'start_date': {'S': '2025-12-20'},
                    'end_date': {'S': '2025-12-27'},
                    'days': {'N': '5'},
                    'type': {'S': 'vacation'},
                    'status': {'S': 'approved'}
                },
                {
                    'user_id': {'S': 'user001'},
                    'request_id': {'S': 'req-002'},
                    'start_date': {'S': '2026-01-15'},
                    'end_date': {'S': '2026-01-16'},
                    'days': {'N': '2'},
                    'type': {'S': 'sick'},
                    'status': {'S': 'pending'}
                },
                {
                    'user_id': {'S': 'user002'},
                    'request_id': {'S': 'req-003'},
                    'start_date': {'S': '2025-11-28'},
                    'end_date': {'S': '2025-11-29'},
                    'days': {'N': '2'},
                    'type': {'S': 'vacation'},
                    'status': {'S': 'approved'}
                }
            ]
        },
        {
            'name': f'{PROJECT_NAME}-expenses',
            'description': 'Expense records for Expense agent',
            'key_schema': [
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'expense_id', 'KeyType': 'RANGE'}
            ],
            'attribute_definitions': [
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'expense_id', 'AttributeType': 'S'}
            ],
            'seed_data': [
                {
                    'user_id': {'S': 'user001'},
                    'expense_id': {'S': 'exp-001'},
                    'date': {'S': '2025-11-15'},
                    'amount': {'N': '125.50'},
                    'category': {'S': 'travel'},
                    'description': {'S': 'Taxi to client meeting'},
                    'status': {'S': 'approved'}
                },
                {
                    'user_id': {'S': 'user001'},
                    'expense_id': {'S': 'exp-002'},
                    'date': {'S': '2025-11-20'},
                    'amount': {'N': '45.00'},
                    'category': {'S': 'meals'},
                    'description': {'S': 'Team lunch'},
                    'status': {'S': 'pending'}
                },
                {
                    'user_id': {'S': 'user002'},
                    'expense_id': {'S': 'exp-003'},
                    'date': {'S': '2025-11-18'},
                    'amount': {'N': '350.00'},
                    'category': {'S': 'equipment'},
                    'description': {'S': 'Wireless keyboard and mouse'},
                    'status': {'S': 'approved'}
                }
            ]
        }
    ]
    
    created_tables = []
    
    for table_config in tables:
        table_name = table_config['name']
        
        try:
            # Check if table exists
            try:
                dynamodb.describe_table(TableName=table_name)
                print_info(f"Table {table_name} already exists")
                created_tables.append(table_name)
                continue
            except dynamodb.exceptions.ResourceNotFoundException:
                pass
            
            # Create table
            print_info(f"Creating table: {table_name}")
            dynamodb.create_table(
                TableName=table_name,
                KeySchema=table_config['key_schema'],
                AttributeDefinitions=table_config['attribute_definitions'],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # Wait for table to be active
            print_info(f"Waiting for table {table_name} to be active...")
            waiter = dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            print_success(f"Created table: {table_name}")
            
            # Seed data
            print_info(f"Seeding data into {table_name}...")
            for item in table_config['seed_data']:
                dynamodb.put_item(TableName=table_name, Item=item)
            
            print_success(f"Seeded {len(table_config['seed_data'])} items into {table_name}")
            created_tables.append(table_name)
            
        except Exception as e:
            print_error(f"Failed to create table {table_name}: {e}")
    
    return created_tables

def create_ecr_repository(account_id):
    """Create ECR repository for agent containers"""
    print_header("Creating ECR Repository")
    
    ecr = boto3.client('ecr', region_name=REGION)
    
    try:
        # Check if repository exists
        try:
            response = ecr.describe_repositories(repositoryNames=[ECR_REPOSITORY_NAME])
            repo_uri = response['repositories'][0]['repositoryUri']
            print_info(f"Repository {ECR_REPOSITORY_NAME} already exists")
            print_success(f"Repository URI: {repo_uri}")
            return repo_uri
        except ecr.exceptions.RepositoryNotFoundException:
            # Create repository
            print_info(f"Creating repository: {ECR_REPOSITORY_NAME}")
            response = ecr.create_repository(
                repositoryName=ECR_REPOSITORY_NAME,
                imageScanningConfiguration={'scanOnPush': False},
                imageTagMutability='MUTABLE'
            )
            repo_uri = response['repository']['repositoryUri']
            print_success(f"Created repository: {ECR_REPOSITORY_NAME}")
            print_success(f"Repository URI: {repo_uri}")
            return repo_uri
            
    except Exception as e:
        print_error(f"Failed to create ECR repository: {e}")
        sys.exit(1)

def check_docker():
    """Check if Docker is installed and running"""
    print_header("Checking Docker")
    
    import subprocess
    
    try:
        # Check if Docker is installed
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Docker installed: {result.stdout.strip()}")
        else:
            print_error("Docker is not installed")
            print_info("Please install Docker Desktop from: https://www.docker.com/products/docker-desktop")
            return False
        
        # Check if Docker daemon is running
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success("Docker daemon is running")
            return True
        else:
            print_warning("Docker daemon is not running")
            print_info("Starting Docker Desktop...")
            
            # Try to start Docker based on OS
            import platform
            system = platform.system()
            
            if system == 'Darwin':  # macOS
                subprocess.run(['open', '-a', 'Docker'], check=False)
                print_info("Waiting for Docker to start (this may take 30-60 seconds)...")
                
                # Wait for Docker to start
                for i in range(30):
                    time.sleep(2)
                    result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
                    if result.returncode == 0:
                        print_success("Docker started successfully")
                        return True
                    print(f"  Waiting... ({i*2}s)", end='\r')
                
                print_error("\nDocker failed to start. Please start Docker Desktop manually.")
                return False
            else:
                print_error("Please start Docker manually and run this script again")
                return False
                
    except FileNotFoundError:
        print_error("Docker is not installed")
        print_info("Please install Docker Desktop from: https://www.docker.com/products/docker-desktop")
        return False
    except Exception as e:
        print_error(f"Error checking Docker: {e}")
        return False

def login_to_ecr(account_id):
    """Login to ECR"""
    print_header("Logging into ECR")
    
    import subprocess
    
    try:
        # Get ECR login password
        print_info("Getting ECR login credentials...")
        result = subprocess.run(
            ['aws', 'ecr', 'get-login-password', '--region', REGION],
            capture_output=True,
            text=True,
            check=True
        )
        password = result.stdout.strip()
        
        # Login to Docker
        ecr_url = f"{account_id}.dkr.ecr.{REGION}.amazonaws.com"
        print_info(f"Logging into {ecr_url}...")
        
        result = subprocess.run(
            ['docker', 'login', '--username', 'AWS', '--password-stdin', ecr_url],
            input=password,
            capture_output=True,
            text=True,
            check=True
        )
        
        print_success("Successfully logged into ECR")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to login to ECR: {e}")
        print_error(f"Output: {e.stderr}")
        return False
    except Exception as e:
        print_error(f"Error logging into ECR: {e}")
        return False

def build_and_push_images(account_id):
    """Build and push Docker images"""
    print_header("Building and Pushing Docker Images")
    
    import subprocess
    
    ecr_prefix = f"{account_id}.dkr.ecr.{REGION}.amazonaws.com/{ECR_REPOSITORY_NAME}"
    
    images = [
        {
            'name': 'base',
            'dockerfile': 'base/Dockerfile',
            'tag': f'{ecr_prefix}:base',
            'description': 'Base image with dependencies',
            'build_args': []
        },
        {
            'name': 'generic-agent-a2a',
            'dockerfile': 'templates/generic_agent.dockerfile',
            'tag': f'{ecr_prefix}:generic-agent-a2a',
            'description': 'Generic agent template',
            'build_args': [
                '--build-arg', f'AWS_ACCOUNT_ID={account_id}',
                '--build-arg', f'AWS_REGION={REGION}',
                '--build-arg', f'ECR_REPOSITORY_PREFIX={ECR_REPOSITORY_NAME}'
            ]
        },
        {
            'name': 'builder',
            'dockerfile': 'builder_agent/Dockerfile',
            'tag': f'{ecr_prefix}:builder',
            'description': 'Builder agent',
            'build_args': [
                '--build-arg', f'AWS_ACCOUNT_ID={account_id}',
                '--build-arg', f'AWS_REGION={REGION}',
                '--build-arg', f'ECR_REPOSITORY_PREFIX={ECR_REPOSITORY_NAME}'
            ]
        }
    ]
    
    for image in images:
        print(f"\n{Colors.BOLD}Building {image['name']} image...{Colors.END}")
        print_info(f"Description: {image['description']}")
        print_info(f"Dockerfile: {image['dockerfile']}")
        print_info(f"Tag: {image['tag']}")
        
        try:
            # Build image
            print_info("Building... (this may take several minutes on first run)")
            build_cmd = [
                'docker', 'build',
                '--platform', 'linux/arm64',
                '-f', image['dockerfile'],
                '-t', image['tag']
            ]
            # Add build args if any
            build_cmd.extend(image['build_args'])
            build_cmd.append('.')
            
            result = subprocess.run(
                build_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            print_success(f"Built {image['name']} image")
            
            # Push image
            print_info("Pushing to ECR...")
            result = subprocess.run(
                ['docker', 'push', image['tag']],
                capture_output=True,
                text=True,
                check=True
            )
            print_success(f"Pushed {image['name']} image to ECR")
            
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to build/push {image['name']} image")
            print_error(f"Error: {e.stderr}")
            print_warning("You can manually build and push images later using the commands in DEMO.md")
            return False
        except Exception as e:
            print_error(f"Error building {image['name']}: {e}")
            return False
    
    print_success("\nAll images built and pushed successfully!")
    return True

def create_env_file(agentcore_role_arn, lambda_role_arn, memory_id, account_id, dynamodb_tables):
    """Create .env file with configuration"""
    print_header("Creating .env File")
    
    env_content = f"""# AWS Configuration
AWS_REGION={REGION}
AWS_ACCOUNT_ID={account_id}

# IAM Roles
AGENTCORE_EXECUTION_ROLE_ARN={agentcore_role_arn}
LAMBDA_EXECUTION_ROLE_ARN={lambda_role_arn}

# AgentCore Memory
BEDROCK_AGENTCORE_MEMORY_ID={memory_id if memory_id else ''}

# ECR Configuration
ECR_REPOSITORY_PREFIX={ECR_REPOSITORY_NAME}

# Model Configuration
MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
DEPLOYED_AGENT_MODEL_ID=us.anthropic.claude-haiku-4-5-20251001-v1:0

# DynamoDB Tables
DYNAMODB_TIME_OFF_TABLE={PROJECT_NAME}-time-off
DYNAMODB_EXPENSES_TABLE={PROJECT_NAME}-expenses

# Builder Agent ARN (set this after deploying the builder agent)
# Required for demo_cli.py to work
BUILDER_AGENT_ARN=
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print_success("Created .env file with configuration")
        print_info("Location: .env")
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        print_warning("You'll need to manually create the .env file")

def validate_permissions():
    """Validate AWS credentials and basic permissions"""
    print_header("Validating AWS Credentials")
    
    try:
        sts = boto3.client('sts', region_name=REGION)
        identity = sts.get_caller_identity()
        
        print_success(f"AWS Account: {identity['Account']}")
        print_success(f"User/Role: {identity['Arn']}")
        print_success(f"Region: {REGION}")
        
        return True
    except Exception as e:
        print_error(f"Failed to validate AWS credentials: {e}")
        print_error("Please configure AWS credentials using 'aws configure' or environment variables")
        return False

def main():
    """Main setup function"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║                                                               ║")
    print("║         AgentCore Factory - AWS Resource Setup               ║")
    print("║                                                               ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")
    
    print_info("This script will:")
    print_info("  1. Validate AWS credentials")
    print_info("  2. Create IAM roles for AgentCore and Lambda")
    print_info("  3. Create AgentCore Memory instance")
    print_info("  4. Create ECR repository")
    print_info("  5. Create DynamoDB tables (time-off, expenses)")
    print_info("  6. Check Docker installation")
    print_info("  7. Build and push Docker images (base, generic-agent, builder)")
    print_info("  8. Create .env configuration file")
    print()
    
    response = input(f"{Colors.BOLD}Continue with setup? (yes/no): {Colors.END}")
    if response.lower() not in ['yes', 'y']:
        print_warning("Setup cancelled")
        sys.exit(0)
    
    # Validate credentials
    if not validate_permissions():
        sys.exit(1)
    
    # Get account ID
    account_id = get_account_id()
    
    # Create AWS resources
    agentcore_role_arn = create_agentcore_execution_role(account_id)
    lambda_role_arn = create_lambda_execution_role(account_id)
    memory_id = create_agentcore_memory(account_id)
    ecr_uri = create_ecr_repository(account_id)
    dynamodb_tables = create_dynamodb_tables(account_id)
    
    # Create .env file
    create_env_file(agentcore_role_arn, lambda_role_arn, memory_id, account_id, dynamodb_tables)
    
    # Check Docker
    if not check_docker():
        print_warning("\nDocker is not available. Skipping image build.")
        print_info("You can build images later by running:")
        print_info("  1. Start Docker Desktop")
        print_info("  2. Run: python3 scripts/build_images.py")
        docker_success = False
    else:
        # Login to ECR
        if not login_to_ecr(account_id):
            print_warning("\nFailed to login to ECR. Skipping image build.")
            docker_success = False
        else:
            # Build and push images
            docker_success = build_and_push_images(account_id)
    
    # Summary
    print_header("Setup Complete!")
    
    if docker_success:
        print(f"{Colors.GREEN}✅ All AWS resources provisioned and Docker images built!{Colors.END}\n")
    else:
        print(f"{Colors.YELLOW}⚠️  AWS resources provisioned, but Docker images need to be built{Colors.END}\n")
    
    print(f"{Colors.BOLD}Resource Summary:{Colors.END}")
    print(f"  • AgentCore Execution Role: {agentcore_role_arn}")
    print(f"  • Lambda Execution Role: {lambda_role_arn}")
    print(f"  • AgentCore Memory ID: {memory_id if memory_id else 'Not created'}")
    print(f"  • ECR Repository: {ecr_uri}")
    print(f"  • DynamoDB Tables: {len(dynamodb_tables)} created")
    for table in dynamodb_tables:
        print(f"    - {table}")
    if docker_success:
        print(f"  • Docker Images: ✅ Built and pushed")
    else:
        print(f"  • Docker Images: ⚠️  Need to be built")
    print()
    
    print(f"{Colors.BOLD}Next Steps:{Colors.END}")
    if docker_success:
        print(f"  1. Deploy the builder agent:")
        print(f"     {Colors.BLUE}See DEMO.md Step 4{Colors.END}")
        print(f"  2. Start the demo CLI:")
        print(f"     {Colors.BLUE}python3 demo_cli.py{Colors.END}")
    else:
        print(f"  1. Build and push Docker images:")
        print(f"     {Colors.BLUE}See DEMO.md Step 3{Colors.END}")
        print(f"  2. Deploy the builder agent:")
        print(f"     {Colors.BLUE}See DEMO.md Step 4{Colors.END}")
        print(f"  3. Start the demo CLI:")
        print(f"     {Colors.BLUE}python3 demo_cli.py{Colors.END}")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup cancelled by user{Colors.END}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}\n")
        sys.exit(1)
