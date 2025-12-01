# AgentCore Factory Code Talk

An educational demonstration project that showcases how to build a system for deploying AI agents to AWS AgentCore Runtime. This project progressively introduces concepts through 7 phases, starting with a simple "Builder Agent" and gradually adding complexity including agent deployment, gateway integration, Lambda functions, and Agent-to-Agent (A2A) communication.

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Clone and navigate
git clone <repository-url>
cd agent_factory/code_talk

# 2. Configure AWS
aws configure  # Enter your credentials

# 3. Run automated setup
python3 scripts/setup_aws_resources.py

# 4. Deploy builder agent
# Load environment variables and deploy
export AWS_REGION=$(grep AWS_REGION .env | cut -d '=' -f2)
export AWS_ACCOUNT_ID=$(grep AWS_ACCOUNT_ID .env | cut -d '=' -f2)
export AGENTCORE_EXECUTION_ROLE_ARN=$(grep AGENTCORE_EXECUTION_ROLE_ARN .env | cut -d '=' -f2)
export ECR_REPOSITORY_PREFIX=$(grep ECR_REPOSITORY_PREFIX .env | cut -d '=' -f2)
export MODEL_ID=$(grep MODEL_ID .env | cut -d '=' -f2)
export DEPLOYED_AGENT_MODEL_ID=$(grep DEPLOYED_AGENT_MODEL_ID .env | cut -d '=' -f2)
export LAMBDA_EXECUTION_ROLE_ARN=$(grep LAMBDA_EXECUTION_ROLE_ARN .env | cut -d '=' -f2)
export BEDROCK_AGENTCORE_MEMORY_ID=$(grep BEDROCK_AGENTCORE_MEMORY_ID .env | cut -d '=' -f2)

aws bedrock-agentcore-control create-agent-runtime \
  --region $AWS_REGION \
  --agent-runtime-name builder \
  --agent-runtime-artifact "{\"containerConfiguration\":{\"containerUri\":\"${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_PREFIX}:builder\"}}" \
  --role-arn $AGENTCORE_EXECUTION_ROLE_ARN \
  --network-configuration '{"networkMode":"PUBLIC"}' \
  --environment-variables AWS_REGION=$AWS_REGION,MODEL_ID=$MODEL_ID,AGENTCORE_EXECUTION_ROLE_ARN=$AGENTCORE_EXECUTION_ROLE_ARN,LAMBDA_EXECUTION_ROLE_ARN=$LAMBDA_EXECUTION_ROLE_ARN,ECR_REPOSITORY_PREFIX=$ECR_REPOSITORY_PREFIX,DEPLOYED_AGENT_MODEL_ID=$DEPLOYED_AGENT_MODEL_ID,BEDROCK_AGENTCORE_MEMORY_ID=$BEDROCK_AGENTCORE_MEMORY_ID

# 5. Add builder ARN to .env (copy from command output)
echo "BUILDER_AGENT_ARN=<paste-arn-here>" >> .env

# 6. Install Python dependencies
rm -rf venv
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# 7. Start demo
./venv/bin/python3 demo_cli.py
```

## Overview

The AgentCore Factory Code Talk demonstrates:

- **Phase 1**: Basic Builder Agent with Strands, Code Interpreter, Browser tools, and AgentCore Memory
- **Phase 2**: Agent deployment capability (uncomment to enable)
- **Phase 3**: Deploy Builder Agent itself to AgentCore Runtime
- **Phase 4**: Gateway and Lambda function integration (uncomment to enable)
- **Phase 5**: Redeploy enhanced Builder Agent with gateway capabilities
- **Phase 6**: A2A protocol support for agent-to-agent communication (uncomment to enable)
- **Phase 7**: Demonstrate multi-agent collaboration via A2A

## Architecture

```
Builder Agent (Strands)
    ↓
Deployment Service → Docker + ECR + AgentCore Runtime
    ↓
Gateway Service → AgentCore Gateway + Lambda Functions
    ↓
A2A Service → Agent Discovery + Inter-Agent Communication
```

## Prerequisites

### Required Software

1. **AWS CLI** - [Install AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
2. **Docker Desktop** - [Install Docker](https://www.docker.com/products/docker-desktop)
3. **Python 3.11+** - [Install Python](https://www.python.org/downloads/)
4. **Git** - For cloning the repository

### AWS Account Requirements

- An AWS account with administrator permissions or permissions to create:
  - IAM roles and policies (including iam:PassRole)
  - ECR repositories
  - AgentCore Runtime resources (create, update, delete)
  - AgentCore Gateway resources (create, update, delete)
  - AgentCore Memory instances
  - Lambda functions
  - CloudWatch log groups

- AWS region with AgentCore availability (e.g., `us-west-2`)

**Note**: The automated setup script (`setup_aws_resources.py`) creates all necessary IAM permissions including:
- Gateway creation and management
- Agent runtime creation and management
- Lambda function creation and invocation
- IAM role passing for both AgentCore and Lambda roles

## Quick Setup (Automated)

The fastest way to get started is using our automated setup script:

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd agent_factory/code_talk
```

### 2. Configure AWS Credentials

Ensure your AWS credentials are configured:

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and default region (us-west-2)
```

Verify access:
```bash
aws sts get-caller-identity
```

### 3. Run Automated Setup Script

This script will create all required AWS resources:

```bash
python3 scripts/setup_aws_resources.py
```

The script will:
- ✅ Create IAM roles (AgentCoreExecutionRole, AgentCoreLambdaExecutionRole)
- ✅ Create AgentCore Memory instance
- ✅ Create ECR repository
- ✅ Build and push Docker images (base, generic-agent, builder)
- ✅ Generate `.env` configuration file

**Note**: The script will prompt for confirmation before making changes. Review the planned actions and type `yes` to proceed.

### 4. Deploy the Builder Agent

After the setup script completes, deploy the builder agent:

```bash
# Get your account ID and ECR repository URI from the .env file
source .env

# Deploy the builder agent
aws bedrock-agentcore-control create-agent-runtime \
  --region $AWS_REGION \
  --agent-runtime-name builder \
  --agent-runtime-artifact "{\"containerConfiguration\":{\"containerUri\":\"${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_PREFIX}:builder\"}}" \
  --role-arn $AGENTCORE_EXECUTION_ROLE_ARN \
  --network-configuration '{"networkMode":"PUBLIC"}' \
  --environment-variables AWS_REGION=$AWS_REGION,MODEL_ID=$MODEL_ID,AGENTCORE_EXECUTION_ROLE_ARN=$AGENTCORE_EXECUTION_ROLE_ARN,LAMBDA_EXECUTION_ROLE_ARN=$LAMBDA_EXECUTION_ROLE_ARN,ECR_REPOSITORY_PREFIX=$ECR_REPOSITORY_PREFIX,DEPLOYED_AGENT_MODEL_ID=$DEPLOYED_AGENT_MODEL_ID,BEDROCK_AGENTCORE_MEMORY_ID=$BEDROCK_AGENTCORE_MEMORY_ID
```

The command will output the builder agent ARN. Copy it and add to your `.env` file:

```bash
# Add this line to .env
BUILDER_AGENT_ARN=arn:aws:bedrock-agentcore:us-west-2:123456789012:runtime/builder-XXXXX
```

### 5. Install Python Dependencies

```bash
# Create fresh virtual environment
rm -rf venv
python3 -m venv venv

# Install dependencies using the venv's pip directly
./venv/bin/pip install -r requirements.txt
```

### 6. Start the Demo CLI

```bash
# Run using the virtual environment's Python
./venv/bin/python3 demo_cli.py
```

You're now ready to build and deploy agents!

## Manual Setup (Advanced)

If you prefer to set up resources manually or need more control:

### 1. Create IAM Roles

#### AgentCore Execution Role

Create a role with trust policy for `bedrock-agentcore.amazonaws.com`:

```json
{
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
```

Attach these inline policies (see `scripts/setup_aws_resources.py` for complete policy definitions):
- AgentCoreA2AAccess
- AgentCoreA2APermissions
- AgentCoreBedrockAccess (includes marketplace permissions)
- AgentCoreECRAccess
- AgentCoreGatewayAccess
- AgentCoreLambdaInvoke
- AgentCoreLambdaManagement
- AgentCoreLogsAccess
- AgentCoreMemoryAccess

#### Lambda Execution Role

Create a role with trust policy for `lambda.amazonaws.com`:

```json
{
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
```

Attach policy with CloudWatch Logs and Bedrock permissions.

### 2. Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name reinvent/agents \
  --region us-west-2
```

### 3. Create AgentCore Memory

```bash
aws bedrock-agentcore-control create-memory \
  --region us-west-2 \
  --name "agentcore-factory-memory" \
  --description "Shared memory for AgentCore Factory agents" \
  --event-expiry-duration 90
```

### 4. Build and Push Docker Images

```bash
# Get your AWS account ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-west-2
export ECR_PREFIX="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/reinvent/agents"

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Build base image
docker build --no-cache --platform linux/arm64 \
  -f base/Dockerfile \
  -t ${ECR_PREFIX}:base \
  .
docker push ${ECR_PREFIX}:base

# Build generic agent template
docker build --no-cache --platform linux/arm64 \
  -f templates/generic_agent.dockerfile \
  --build-arg AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID} \
  --build-arg AWS_REGION=${AWS_REGION} \
  --build-arg ECR_REPOSITORY_PREFIX=reinvent/agents \
  -t ${ECR_PREFIX}:generic-agent-a2a \
  .
docker push ${ECR_PREFIX}:generic-agent-a2a

# Build builder agent
docker build --no-cache --platform linux/arm64 \
  -f builder_agent/Dockerfile \
  --build-arg AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID} \
  --build-arg AWS_REGION=${AWS_REGION} \
  --build-arg ECR_REPOSITORY_PREFIX=reinvent/agents \
  -t ${ECR_PREFIX}:builder \
  .
docker push ${ECR_PREFIX}:builder
```

### 5. Configure Environment

Create `.env` file with your AWS resources:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```bash
AWS_REGION=us-west-2
AWS_ACCOUNT_ID=123456789012
AGENTCORE_EXECUTION_ROLE_ARN=arn:aws:iam::123456789012:role/AgentCoreExecutionRole
LAMBDA_EXECUTION_ROLE_ARN=arn:aws:iam::123456789012:role/AgentCoreLambdaExecutionRole
BEDROCK_AGENTCORE_MEMORY_ID=mem-xxxxx
ECR_REPOSITORY_PREFIX=reinvent/agents
MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
DEPLOYED_AGENT_MODEL_ID=us.anthropic.claude-haiku-4-5-20251001-v1:0
BUILDER_AGENT_ARN=  # Set after deploying builder agent
```

### 6. Deploy Builder Agent

Follow step 4 from the Quick Setup section above.

## Verifying Your Setup

After setup, verify everything is working:

```bash
# Check IAM roles exist
aws iam get-role --role-name AgentCoreExecutionRole
aws iam get-role --role-name AgentCoreLambdaExecutionRole

# Check ECR repository
aws ecr describe-repositories --repository-names reinvent/agents --region us-west-2

# Check Docker images
aws ecr list-images --repository-name reinvent/agents --region us-west-2

# Check AgentCore Memory
aws bedrock-agentcore-control list-memories --region us-west-2

# Check Builder Agent
aws bedrock-agentcore-control list-agent-runtimes --region us-west-2
```

## Using the AgentCore Factory

### Interactive Demo CLI

The easiest way to interact with the factory is through the demo CLI:

```bash
./venv/bin/python3 demo_cli.py
```

The CLI provides:
1. **Chat with Builder Agent** - Ask the builder to create new agents
2. **Chat with Deployed Agents** - Interact with agents you've created
3. **List All Agents** - View all deployed agents
4. **Show A2A URLs** - Get URLs for agent-to-agent connections

### Example: Creating Your First Agent

1. Start the demo CLI:
```bash
./venv/bin/python3 demo_cli.py
```

2. Select option 1 (Chat with Builder Agent)

3. Ask the builder to create an agent:
```
You: Create a greeting agent that says hello in different languages
```

4. The builder will:
   - Generate the agent code
   - Create a Dockerfile
   - Build and push the Docker image
   - Deploy to AgentCore Runtime
   - Return the agent ARN

5. Select option 2 to chat with your new agent!

### Example Agent Requests

Try asking the builder to create:

**Simple Agents:**
- "Create a math tutor agent that helps with algebra"
- "Build a weather information agent"
- "Make a joke-telling agent"

**Agents with Tools:**
- "Create an agent that can search the web and summarize articles"
- "Build a code review agent that can execute Python code"
- "Make a research agent with web browsing capabilities"

**Multi-Agent Systems:**
- "Create a customer support agent that can delegate to a billing specialist"
- "Build a travel planning agent that coordinates with a booking agent"
- "Make a project manager agent that assigns tasks to worker agents"

### Advanced: Direct Agent Invocation

You can also invoke agents directly using the AWS CLI:

```bash
# Create a request payload
echo '{"prompt": "Hello, how are you?"}' | base64 > /tmp/request.b64

# Invoke the agent
aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn $BUILDER_AGENT_ARN \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

# View the response
cat /tmp/response.json | jq -r '.result'
```

## Project Structure

```
agent_factory/code_talk/
├── README.md                 # This file
├── PHASES.md                 # Step-by-step phase guide
├── .env.example              # Configuration template
├── requirements.txt          # Python dependencies
│
├── builder_agent.py          # Main Builder Agent
├── deployment_service.py     # Agent deployment logic
├── gateway_service.py        # Gateway & Lambda (Phase 4+)
├── a2a_service.py           # A2A communication (Phase 6+)
├── agent_registry.py        # Agent discovery registry
│
├── templates/               # Code generation templates
│   ├── agent_template.py    # Template for generated agents
│   ├── dockerfile_template  # Dockerfile template
│   └── lambda_template.py   # Lambda function template
│
└── utils/                   # Utility functions
    ├── aws_helpers.py       # AWS SDK helpers
    ├── validation.py        # Input validation
    └── logging_config.py    # Logging setup
```

## Key Concepts

### Builder Agent

A Strands-based AI agent that can:
- Have natural conversations
- Execute Python code via Code Interpreter
- Browse the web via Browser tool
- Remember conversations via AgentCore Memory
- Deploy other agents (Phase 2+)
- Create gateways and Lambda tools (Phase 4+)
- Communicate with other agents via A2A (Phase 6+)

### Agent Deployment

The deployment workflow:
1. Generate agent code from template
2. Create Dockerfile and requirements.txt
3. Build Docker container
4. Push to Amazon ECR
5. Create AgentCore Runtime
6. Register in agent registry

### AgentCore Memory

Provides conversation persistence with:
- **Short-term memory (STM)**: Recent conversation turns
- **Long-term memory (LTM)**: User facts, preferences, summaries
- Automatic memory strategies for different data types

### Gateway & Lambda Integration

- **AgentCore Gateway**: Provides MCP tools to agents
- **Lambda Functions**: Serverless functions as agent tools
- **SigV4 Authentication**: Secure access to gateway tools

### A2A Protocol

Enables agents to:
- Discover other agents via registry
- Send messages to other agents
- Receive responses from other agents
- Delegate tasks to specialized agents

## Configuration Reference

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `AWS_REGION` | Yes | AWS region for AgentCore | `us-west-2` |
| `AGENTCORE_EXECUTION_ROLE_ARN` | Yes | IAM role for agent execution | `arn:aws:iam::123456789012:role/AgentCoreExecutionRole` |
| `ECR_REPOSITORY_PREFIX` | Yes | Prefix for ECR repositories | `agentcore-agents` |
| `BEDROCK_AGENTCORE_MEMORY_ID` | No | Existing memory ID (created if not provided) | `mem-abc123` |
| `BEDROCK_AGENTCORE_GATEWAY_ID` | No | Existing gateway ID (Phase 4+) | `gw-xyz789` |
| `MODEL_ID` | No | Model for Builder Agent | `global.anthropic.claude-sonnet-4-5-20251022-v2:0` |
| `DEPLOYED_AGENT_MODEL_ID` | No | Model for deployed agents | `global.anthropic.claude-haiku-4-5-20251001-v1:0` |

### IAM Role Permissions

The execution role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

## Troubleshooting

### Setup Script Issues

**Issue**: Setup script fails with "AWS credentials not configured"
**Solution**: 
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region
```

**Issue**: Setup script fails with "Docker is not running"
**Solution**: 
- Start Docker Desktop
- Wait for it to fully start (check the Docker icon in system tray)
- Run the setup script again

**Issue**: Setup script fails with permission errors
**Solution**: 
- Ensure your AWS user has permissions to create IAM roles, ECR repositories, etc.
- Check AWS CloudTrail for specific permission denials

**Issue**: Docker build takes too long or fails
**Solution**: 
- Ensure you have at least 10GB free disk space
- Check your internet connection (downloads base images and dependencies)
- Try building images individually to identify which one fails

### Bedrock Model Access

**Issue**: "Could not resolve the foundation model" error
**Solution**: 
1. Go to AWS Console → Bedrock → Model access
2. Request access to Claude models (Sonnet and Haiku)
3. Wait for approval (usually instant for Claude models)
4. The marketplace permissions in the IAM role will handle subscription

**Issue**: Model invocation fails with access denied
**Solution**: 
- Verify the AgentCore execution role has `bedrock:InvokeModel` permission
- Check that marketplace permissions are included in the role
- Ensure you're using the correct model ID for your region

### Docker Build Failures

**Issue**: Docker build fails with "base image not found"
**Solution**: 
- Build the base image first: `docker build -f base/Dockerfile -t <ecr-uri>:base .`
- Ensure you've pushed the base image to ECR before building other images

**Issue**: Playwright installation fails during Docker build
**Solution**: 
- Ensure sufficient disk space (at least 5GB free)
- Check network connectivity
- Try building with `--no-cache` flag

### ECR Issues

**Issue**: "RepositoryNotFoundException" when pushing images
**Solution**: 
```bash
aws ecr create-repository --repository-name reinvent/agents --region us-west-2
```

**Issue**: ECR login fails
**Solution**: 
```bash
# Re-authenticate with ECR
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin \
  $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-west-2.amazonaws.com
```

### AgentCore Runtime Errors

**Issue**: Agent deployment fails with "Invalid role ARN"
**Solution**: 
- Verify the role exists: `aws iam get-role --role-name AgentCoreExecutionRole`
- Check the trust policy allows `bedrock-agentcore.amazonaws.com`
- Ensure the role ARN in `.env` is correct

**Issue**: Agent status stuck in "CREATING"
**Solution**: 
- Wait 2-3 minutes (initial deployment can take time)
- Check CloudWatch logs: `/aws/bedrock-agentcore/<agent-name>`
- Verify the Docker image exists in ECR and is accessible

**Issue**: Agent fails with "Container failed to start"
**Solution**: 
- Check CloudWatch logs for the specific error
- Verify environment variables are set correctly
- Test the Docker image locally: `docker run -p 9000:9000 <image-uri>`

### Demo CLI Issues

**Issue**: "BUILDER_AGENT_ARN environment variable not set"
**Solution**: 
1. Deploy the builder agent first (see setup instructions)
2. Add the ARN to your `.env` file:
   ```bash
   BUILDER_AGENT_ARN=arn:aws:bedrock-agentcore:us-west-2:123456789012:runtime/builder-xxxxx
   ```
3. Restart the demo CLI

**Issue**: "No agents available" in demo CLI
**Solution**: 
- Use option 1 to create an agent with the builder first
- Or deploy agents manually using AWS CLI
- Check that agents are in "READY" status

### Memory Integration Issues

**Issue**: Conversations not persisting across sessions
**Solution**: 
- Verify `BEDROCK_AGENTCORE_MEMORY_ID` is set in `.env`
- Check the memory exists: `aws bedrock-agentcore-control get-memory --memory-id <id>`
- Ensure the execution role has memory permissions

**Issue**: Memory quota exceeded
**Solution**: 
```bash
# List and delete old memories
aws bedrock-agentcore-control list-memories --region us-west-2
aws bedrock-agentcore-control delete-memory --memory-id <id> --region us-west-2
```

### Common Error Messages

**"AccessDeniedException"**
- Check IAM role permissions
- Verify trust policy is correct
- Ensure you're in a supported region

**"ResourceNotFoundException"**
- Verify the resource (agent, memory, gateway) exists
- Check the ARN/ID is correct
- Ensure you're using the correct region

**"ThrottlingException"**
- You're hitting API rate limits
- Add delays between API calls
- Request a quota increase if needed

**"ValidationException: Invalid container URI"**
- Verify the ECR image exists and is accessible
- Check the URI format: `<account>.dkr.ecr.<region>.amazonaws.com/<repo>:<tag>`
- Ensure the execution role can pull from ECR

### Getting Help

If you're still stuck:

1. **Check CloudWatch Logs**: Most errors are logged to CloudWatch
   ```bash
   aws logs tail /aws/bedrock-agentcore/<agent-name> --follow
   ```

2. **Verify AWS Resources**: Ensure all resources exist and are accessible
   ```bash
   # Run the verification commands from the setup section
   ```

3. **Review IAM Permissions**: Use IAM Policy Simulator to test permissions

4. **Check AWS Service Health**: Visit [AWS Service Health Dashboard](https://status.aws.amazon.com/)

5. **Enable Debug Logging**: Set `LOG_LEVEL=DEBUG` in `.env` for verbose output

## Development Tips

### Faster Docker Builds

Pre-build a base image with common dependencies:

```dockerfile
FROM public.ecr.aws/docker/library/python:3.11-slim
RUN apt-get update && apt-get install -y \
    wget gnupg && \
    playwright install-deps && \
    rm -rf /var/lib/apt/lists/*
RUN pip install strands-agents strands-agents-tools bedrock-agentcore boto3 playwright
RUN playwright install chromium
```

### Debug Logging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Individual Components

Test deployment service:
```python
from deployment_service import AgentDeploymentService, AgentSpec

service = AgentDeploymentService(region_name="us-west-2", ...)
spec = AgentSpec(name="test-agent", purpose="Testing", ...)
result = service.deploy_agent(spec)
```

## Cost Considerations

Running this demo will incur AWS costs. Here's what to expect:

### Ongoing Costs
- **AgentCore Runtime**: Charged per agent runtime hour
- **Bedrock Model Invocations**: Charged per input/output token
- **ECR Storage**: Charged per GB-month for stored images
- **CloudWatch Logs**: Charged per GB ingested and stored
- **Lambda Invocations**: Charged per invocation and compute time (Phase 4+)

### Cost Optimization Tips
1. **Delete unused agents** when done testing
2. **Use Haiku model** for deployed agents (cheaper than Sonnet)
3. **Clean up old ECR images** regularly
4. **Set CloudWatch log retention** to 7 days
5. **Delete test Lambda functions** after demos

### Estimated Costs (US West 2)
For light testing (a few hours):
- AgentCore Runtime: ~$5-10
- Bedrock invocations: ~$2-5
- ECR storage: <$1
- CloudWatch Logs: <$1
- **Total: ~$10-20 per day of active testing**

## Cleanup

When you're done with the demo, clean up resources to avoid ongoing charges:

### Quick Cleanup Script

```bash
# Delete all agent runtimes
for agent in $(aws bedrock-agentcore-control list-agent-runtimes --region us-west-2 --query 'agentRuntimes[].agentRuntimeId' --output text); do
  echo "Deleting agent: $agent"
  aws bedrock-agentcore-control delete-agent-runtime --agent-runtime-id $agent --region us-west-2
done

# Delete memories
for memory in $(aws bedrock-agentcore-control list-memories --region us-west-2 --query 'memories[].memoryId' --output text); do
  echo "Deleting memory: $memory"
  aws bedrock-agentcore-control delete-memory --memory-id $memory --region us-west-2
done

# Delete ECR images (keeps repository)
aws ecr batch-delete-image \
  --repository-name reinvent/agents \
  --region us-west-2 \
  --image-ids "$(aws ecr list-images --repository-name reinvent/agents --region us-west-2 --query 'imageIds[*]' --output json)"

# Optional: Delete ECR repository
aws ecr delete-repository --repository-name reinvent/agents --region us-west-2 --force

# Optional: Delete IAM roles (only if you don't need them)
aws iam delete-role --role-name AgentCoreExecutionRole
aws iam delete-role --role-name AgentCoreLambdaExecutionRole
```

### Manual Cleanup via Console

1. **AgentCore Runtimes**: Bedrock Console → AgentCore → Runtimes → Delete each runtime
2. **Memories**: Bedrock Console → AgentCore → Memories → Delete each memory
3. **ECR Images**: ECR Console → Repositories → reinvent/agents → Delete images
4. **Lambda Functions**: Lambda Console → Delete any created functions
5. **CloudWatch Logs**: CloudWatch Console → Log groups → Delete `/aws/bedrock-agentcore/*`
6. **IAM Roles**: IAM Console → Roles → Delete AgentCoreExecutionRole and AgentCoreLambdaExecutionRole

## Resources

- [AWS AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html)
- [AgentCore Runtime Quickstart](https://aws.github.io/bedrock-agentcore-starter-toolkit/user-guide/runtime/quickstart.html)
- [Strands Agents Documentation](https://github.com/awslabs/strands)
- [A2A Protocol Specification](https://github.com/awslabs/strands/blob/main/docs/a2a.md)
- [AWS Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [Docker Documentation](https://docs.docker.com/)

## FAQ

**Q: Do I need to subscribe to Claude models in AWS Marketplace?**
A: The IAM role includes marketplace permissions, so subscription happens automatically on first use.

**Q: Can I use a different AWS region?**
A: Yes, but ensure AgentCore is available in that region. Update `AWS_REGION` in `.env`.

**Q: How long does initial setup take?**
A: Automated setup takes 15-30 minutes (mostly Docker builds). Manual setup takes 30-60 minutes.

**Q: Can I run this on Windows?**
A: Yes, but you'll need Docker Desktop for Windows and may need to adjust some bash commands.

**Q: What if I already have IAM roles with these names?**
A: The setup script will update existing roles. Review the policies before running.

**Q: Can I deploy agents to private subnets?**
A: Yes, change `networkMode` to `PRIVATE` and configure VPC settings in the deployment.

**Q: How do I update an existing agent?**
A: Rebuild the Docker image, push to ECR, then use `update-agent-runtime` with the new image URI.

**Q: Can I use different models?**
A: Yes, update `MODEL_ID` and `DEPLOYED_AGENT_MODEL_ID` in `.env` with any Bedrock model ID.

## License

This project is provided as educational material for AWS AgentCore demonstrations.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review CloudWatch logs for deployed agents
3. Verify AWS permissions and quotas
4. Consult AWS AgentCore documentation
5. Check AWS Service Health Dashboard
