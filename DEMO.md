# AgentCore Factory - Complete Demo Guide

This guide demonstrates the full capabilities of the AgentCore Factory, from building containers to deploying agents that communicate with each other via A2A protocol.

## Demo Flow Overview

1. **Setup**: Build and push all containers
2. **Deploy Builder Agent**: Deploy the agent factory
3. **Simple Agents**: Create and test basic agents
4. **Complex Agents**: Create agents with multiple Lambda functions
5. **A2A Communication**: Deploy agents that talk to each other

---

## Part 1: Initial Setup

### Step 1: Create ECR Repository (First Time Only)
```bash
aws ecr create-repository --repository-name reinvent/agents --region us-west-2
```

### Step 2: Login to ECR
```bash
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin \
  590183704046.dkr.ecr.us-west-2.amazonaws.com
```

### Step 3: Build and Push All Containers

**Build Base Image (~5 minutes)**
```bash
# IMPORTANT: AgentCore Runtime requires ARM64 architecture
docker build --no-cache --platform linux/arm64 \
  -f base/Dockerfile \
  -t 590183704046.dkr.ecr.us-west-2.amazonaws.com/reinvent/agents:base \
  .

docker push 590183704046.dkr.ecr.us-west-2.amazonaws.com/reinvent/agents:base
```

**Build Generic Agent (~30 seconds)**
```bash
docker build --no-cache --platform linux/arm64 \
  -f templates/generic_agent.dockerfile \
  -t 590183704046.dkr.ecr.us-west-2.amazonaws.com/reinvent/agents:generic-agent-a2a \
  .

docker push 590183704046.dkr.ecr.us-west-2.amazonaws.com/reinvent/agents:generic-agent-a2a
```

**Build Builder Agent (~30 seconds)**
```bash
docker build --no-cache --platform linux/arm64 \
  -f builder_agent/Dockerfile \
  -t 590183704046.dkr.ecr.us-west-2.amazonaws.com/reinvent/agents:builder \
  .

docker push 590183704046.dkr.ecr.us-west-2.amazonaws.com/reinvent/agents:builder
```

---

## Part 2: Deploy Builder Agent

### Step 4: Create Builder Agent Runtime
```bash
aws bedrock-agentcore-control create-agent-runtime \
  --region us-west-2 \
  --agent-runtime-name builder \
  --agent-runtime-artifact '{"containerConfiguration":{"containerUri":"552537893160.dkr.ecr.us-west-2.amazonaws.com/reinvent/agents:builder"}}' \
  --role-arn arn:aws:iam::552537893160:role/AgentCoreExecutionRole \
  --network-configuration '{"networkMode":"PUBLIC"}' \
  --environment-variables AWS_REGION=us-west-2,MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0,AGENTCORE_EXECUTION_ROLE_ARN=arn:aws:iam::552537893160:role/AgentCoreExecutionRole,LAMBDA_EXECUTION_ROLE_ARN=arn:aws:iam::552537893160:role/AgentCoreLambdaExecutionRole,ECR_REPOSITORY_PREFIX=reinvent/agents,DEPLOYED_AGENT_MODEL_ID=global.anthropic.claude-haiku-4-5-20251001-v1:0,BEDROCK_AGENTCORE_MEMORY_ID=reInvent_agent_factory-qvlx6iG5Tm
```

**Wait for builder agent to be READY:**
```bash
aws bedrock-agentcore-control get-agent-runtime \
  --region us-west-2 \
  --agent-runtime-id builder_ultimate-XXXXX \
  --query 'status' \
  --output text
```

### Step 5: Update Builder Agent (When Rebuilding)
```bash
aws bedrock-agentcore-control update-agent-runtime \
  --region us-west-2 \
  --agent-runtime-id builder-7m5mPN7Hg1 \
  --agent-runtime-artifact '{"containerConfiguration":{"containerUri":"552537893160.dkr.ecr.us-west-2.amazonaws.com/reinvent/agents:builder"}}' \
  --role-arn arn:aws:iam::552537893160:role/AgentCoreExecutionRole \
  --network-configuration '{"networkMode":"PUBLIC"}' \
  --environment-variables AWS_REGION=us-west-2,MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0,AGENTCORE_EXECUTION_ROLE_ARN=arn:aws:iam::552537893160:role/AgentCoreExecutionRole,LAMBDA_EXECUTION_ROLE_ARN=arn:aws:iam::552537893160:role/AgentCoreLambdaExecutionRole,ECR_REPOSITORY_PREFIX=reinvent/agents,DEPLOYED_AGENT_MODEL_ID=global.anthropic.claude-haiku-4-5-20251001-v1:0,BEDROCK_AGENTCORE_MEMORY_ID=reInvent_agent_factory-7uLGsP8TfC
```

---

## Part 3: Simple Agent Demos

### Demo 3.1: Create a Simple Greeting Agent

**Ask the builder to create a greeting agent:**
```bash
echo '{"prompt":"Create a simple greeting agent called GreeterBot that welcomes users"}' | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/builder_ultimate-pSpEdXCehH \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'
```

**Test the Greeting Agent:**
```bash
# Use the agent ARN from the previous response
echo '{"prompt":"Hello! Who are you?"}' | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/GreeterBot-XXXXX \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'
```

---

## Part 4: Complex Agents with Lambda Functions

### Demo 4.1: Calculator Agent with Lambda Tool

**Create a calculator agent with a Lambda function:**
```bash
echo '{"prompt":"Create a calculator agent called CalcBot with a calculate tool that takes expression parameter and evaluates it. Handler code: result = eval(parameters.get(\"expression\")); return {\"expression\": parameters.get(\"expression\"), \"result\": result}"}' | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/builder_ultimate-pSpEdXCehH \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'
```

**Test the calculator:**
```bash
echo '{"prompt":"What is 42 * 137?"}' | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/CalcBot-XXXXX \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'
```

### Demo 4.2: E-Commerce Agent with Multiple Tools

**Create shopping agent with 4 Lambda functions:**
```bash
echo '{"prompt":"Create an e-commerce agent called ShopBot with four tools: 1) search_products tool that takes query parameter and returns mock product list. Handler: products = [{\"id\": f\"P{i}\", \"name\": f\"{parameters.get(\"query\")} Item {i}\", \"price\": 19.99 + i*10} for i in range(1, 4)]; return {\"query\": parameters.get(\"query\"), \"products\": products, \"count\": len(products)} 2) get_product_details tool that takes product_id parameter. Handler: return {\"product_id\": parameters.get(\"product_id\"), \"name\": \"Sample Product\", \"price\": 49.99, \"in_stock\": True, \"description\": \"High quality product\"} 3) add_to_cart tool that takes product_id and quantity parameters. Handler: import random; cart_id = f\"CART{random.randint(1000,9999)}\"; return {\"success\": True, \"cart_id\": cart_id, \"product_id\": parameters.get(\"product_id\"), \"quantity\": parameters.get(\"quantity\", 1), \"message\": \"Added to cart\"} 4) checkout tool that takes cart_id parameter. Handler: import random; order_id = f\"ORD{random.randint(10000,99999)}\"; return {\"success\": True, \"order_id\": order_id, \"cart_id\": parameters.get(\"cart_id\"), \"total\": 149.97, \"status\": \"confirmed\"}"}' | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/builder_ultimate-pSpEdXCehH \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'
```

**Test complete shopping flow:**
```bash
# 1. Search for products
echo '{"prompt":"Search for laptops"}' | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/ShopBot-XXXXX \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'

# 2. Add to cart
echo '{"prompt":"Add product P2 to cart with quantity 2"}' | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/ShopBot-XXXXX \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'

# 3. Checkout (use cart ID from previous response)
echo '{"prompt":"Checkout cart CART1234"}' | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/ShopBot-XXXXX \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'
```

---

## Part 5: Agent-to-Agent (A2A) Communication

### Demo 5.1: Deploy Two Agents for A2A

**First, create a specialized calculator agent:**
```bash
echo '{"prompt":"Create a calculator agent called MathBot that can perform arithmetic calculations"}' | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/builder_ultimate-pSpEdXCehH \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'

# Save the MathBot ARN for next step
export MATHBOT_ARN="arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/MathBot-XXXXX"
```

**Create a coordinator agent that knows about MathBot:**
```bash
# Get the MathBot runtime URL
MATHBOT_URL="https://bedrock-agentcore.us-west-2.amazonaws.com/runtimes/$(echo $MATHBOT_ARN | sed 's/:/\%3A/g' | sed 's/\//\%2F/g')/invocations/"

echo "{\"prompt\":\"Create a coordinator agent called CoordinatorBot that can delegate math tasks to other agents. Configure it to know about this agent URL: $MATHBOT_URL\"}" | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/builder_ultimate-pSpEdXCehH \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'
```

### Demo 5.2: Test A2A Communication

**Ask the coordinator to use the math agent:**
```bash
echo '{"prompt":"What is 42 * 137? Please use the math agent to calculate this."}' | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/CoordinatorBot-XXXXX \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'
```

**Expected behavior:**
- CoordinatorBot discovers MathBot via A2A protocol
- CoordinatorBot sends the calculation request to MathBot
- MathBot computes the result (5,754)
- CoordinatorBot receives and returns the answer

---

## Part 6: Advanced Demos

### Demo 6.1: Restaurant Booking System

**Create Restaurant Agent**
```bash
echo '{"prompt":"Create a restaurant booking agent called RestaurantBot with two tools: 1) book_table tool that takes restaurant_name, date, time, and party_size parameters and returns a booking confirmation with a booking_id. Handler code: import random; booking_id = f\"BK{random.randint(10000,99999)}\"; return {\"success\": True, \"booking_id\": booking_id, \"restaurant\": parameters.get(\"restaurant_name\"), \"date\": parameters.get(\"date\"), \"time\": parameters.get(\"time\"), \"party_size\": parameters.get(\"party_size\"), \"message\": f\"Table booked at {parameters.get(\"restaurant_name\")} for {parameters.get(\"party_size\")} people on {parameters.get(\"date\")} at {parameters.get(\"time\")}\"} 2) cancel_booking tool that takes booking_id parameter and returns cancellation confirmation. Handler code: return {\"success\": True, \"booking_id\": parameters.get(\"booking_id\"), \"message\": f\"Booking {parameters.get(\"booking_id\")} has been cancelled successfully\"}"}' | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/builder_ultimate-pSpEdXCehH \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'
```

**Test booking flow:**
```bash
# 1. Book a table
echo '{"prompt":"Book a table at The Italian Place for 4 people on December 25th at 7:00 PM"}' | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/RestaurantBot-XXXXX \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'

# 2. Cancel booking (use booking ID from previous response)
echo '{"prompt":"Cancel my booking BK12345"}' | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/RestaurantBot-XXXXX \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'
```

### Demo 6.2: Fitness Tracker

**Create Fitness Agent**
```bash
echo '{"prompt":"Create a fitness tracker agent called FitBot with three tools: 1) log_workout tool that takes exercise, duration_minutes, and calories parameters and returns a workout log. Handler: import random; workout_id = f\"WO{random.randint(1000,9999)}\"; return {\"workout_id\": workout_id, \"exercise\": parameters.get(\"exercise\"), \"duration\": parameters.get(\"duration_minutes\"), \"calories\": parameters.get(\"calories\"), \"logged_at\": \"today\", \"message\": f\"Logged {parameters.get(\"exercise\")} workout\"} 2) get_stats tool that takes period parameter (day/week/month) and returns mock fitness stats. Handler: import random; total_workouts = random.randint(5, 20); total_calories = random.randint(1000, 5000); return {\"period\": parameters.get(\"period\", \"week\"), \"total_workouts\": total_workouts, \"total_calories\": total_calories, \"avg_duration\": 45} 3) set_goal tool that takes goal_type and target parameters. Handler: import random; goal_id = f\"GOAL{random.randint(100,999)}\"; return {\"goal_id\": goal_id, \"goal_type\": parameters.get(\"goal_type\"), \"target\": parameters.get(\"target\"), \"status\": \"active\", \"message\": \"Goal set successfully\"}"}' | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/builder_ultimate-pSpEdXCehH \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'
```

**Test fitness tracking:**
```bash
# 1. Log a workout
echo '{"prompt":"Log a workout: running for 30 minutes, 300 calories"}' | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/FitBot-XXXXX \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'

# 2. Get stats
echo '{"prompt":"Show me my stats for this week"}' | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/FitBot-XXXXX \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'

# 3. Set a goal
echo '{"prompt":"Set a goal to run 100 miles this month"}' | \
  base64 | tr -d '\n' > /tmp/request.b64

aws bedrock-agentcore invoke-agent-runtime \
  --region us-west-2 \
  --agent-runtime-arn arn:aws:bedrock-agentcore:us-west-2:590183704046:runtime/FitBot-XXXXX \
  --payload file:///tmp/request.b64 \
  /tmp/response.json

cat /tmp/response.json | jq -r '.result'
```

---

## Part 7: Utility Commands



**Check agent status:**
```bash
aws bedrock-agentcore-control get-agent-runtime \
  --region us-west-2 \
  --agent-runtime-id <agent-runtime-id> \
  --query 'status' \
  --output text
```

**List all deployed agents:**
```bash
aws bedrock-agentcore-control list-agent-runtimes \
  --region us-west-2 \
  --query 'agentRuntimes[*].[agentRuntimeId,agentRuntimeName,status]' \
  --output table
```

**Delete an agent:**
```bash
aws bedrock-agentcore-control delete-agent-runtime \
  --region us-west-2 \
  --agent-runtime-id <agent-runtime-id>
```

**View Lambda function logs:**
```bash
aws logs tail /aws/lambda/<function-name> \
  --region us-west-2 \
  --since 5m \
  --format short
```

**View agent runtime logs:**
```bash
aws logs tail /aws/bedrock-agentcore/runtimes/<agent-id>-DEFAULT \
  --region us-west-2 \
  --since 10m \
  --format short
```

---

## Demo Tips

### Timing
- Wait 5-10 seconds after creating an agent before testing it
- Builder agent takes ~30 seconds to create agents with Lambda tools
- Simple agents without tools deploy in ~10 seconds

### Troubleshooting
- **Agent not responding**: Check status with `get-agent-runtime`
- **Lambda errors**: View CloudWatch logs for the Lambda function
- **A2A not working**: Verify both agents are READY and URLs are correct
- **Gateway errors**: Check that gateway was created successfully

### Best Practices
- Save agent ARNs in environment variables for easy reuse
- Use `jq -r '.result'` to format responses
- Clean up test agents after demos to avoid costs
- Test simple agents before complex multi-tool agents

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Builder Agent                          │
│  (Orchestrates agent creation with Lambda tools)            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ├─► Creates AgentCore Gateway
                     ├─► Creates Lambda Functions
                     ├─► Deploys Generic Agent Container
                     └─► Configures A2A Communication
                     
┌─────────────────────────────────────────────────────────────┐
│                    Deployed Agent                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Generic Agent Container (A2A Protocol)              │  │
│  │  - Port 9000                                         │  │
│  │  - Agent Card at /.well-known/agent-card.json       │  │
│  │  - Strands Agent with Tools                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                     │                                       │
│                     ├─► AgentCore Gateway (MCP)            │
│                     │   └─► Lambda Functions               │
│                     │                                       │
│                     └─► A2A Client (discovers other agents)│
└─────────────────────────────────────────────────────────────┘
```

### Key Features
- **Single Container**: One generic agent container configured via environment variables
- **A2A Protocol**: All agents support agent-to-agent communication
- **Lambda Tools**: Dynamic Lambda function creation via Gateway
- **Fast Deployment**: ~10-30 seconds per agent
- **Scalable**: Reuses base container for all agents


create me a risk analysis agent that has a tool for generating risk profile based on industry

create me a PTO agent that can access current PTO of people and allow them to submit PTO

create me an expense agent that can access current expenses or people and allow them to submit new expenses

create me one agent orchestrator that communicates with the PTO agent and the expense agent to delegate tasks to them