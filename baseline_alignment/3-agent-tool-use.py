"""
3: Agent Tool Use
===========================
This example demonstrates how to give your agent superpowers by adding tools!
Tools allow agents to interact with external systems, APIs, and services.

In this example, we create an AWS news agent that can:
- Fetch web content (http_request)
- Interact with AWS services like S3 (use_aws)
- Get current time and date (current_time)
"""

# ============================================================================
# STEP 1: Import Required Components
# ============================================================================
from strands import Agent

# Import pre-built tools from strands_tools
# These tools extend your agent's capabilities beyond just text generation
from strands_tools import http_request, use_aws, current_time


# ============================================================================
# STEP 2: Create a Specialized Agent with Tools
# ============================================================================
# This agent is designed to fetch, summarize, and store AWS news
aws_news_agent = Agent(
    # Specify the model to use
    model="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    
    # Define the agent's role and behavior through a system prompt
    # This prompt gives the agent context about its purpose and capabilities
    system_prompt="""You are an AWS news anchor specializing in creating bite sized content about
    weekly AWS news. Your expertise is reviewing the AWS weekly, writing a narrative with one sentence
    about each news, creating a text file, and storing it on S3. The object on S3 should have 
    the time and date of user request and should be stored in the "aws-weekly-news-renvent" bucket. 
    eg: 15Nov_16:05UTC_aws_weekly_briefing
    
    Use the following instructions:
    1. Use the "https://aws.amazon.com/blogs/aws/tag/week-in-review/" URL and use only the first
    AWS Weekly Roundup article from there. 
    2. Use PST time zone only.
    3. Give examples when necessary.
    4. Create the PDF file and upload it to the S3 bucket.
    
    Your goal is to help AWS users quickly understand weekly news brief.
    """,
    
    # Provide tools that the agent can use to accomplish its tasks
    # The agent will automatically decide when and how to use these tools
    tools=[
        http_request,   # Allows fetching web content from URLs
        use_aws,        # Enables interaction with AWS services (S3, etc.)
        current_time    # Provides current date and time information
    ]
)


# ============================================================================
# STEP 3: Invoke the Agent
# ============================================================================
# Ask the agent to perform its task
# The agent will automatically:
# 1. Use http_request to fetch the AWS blog
# 2. Use current_time to get the timestamp
# 3. Process and summarize the news
# 4. Use use_aws to upload the result to S3
response = aws_news_agent("Whats the latest AWS news?")


# ============================================================================
# How Tool Use Works:
# ============================================================================
# 1. Agent receives your prompt
# 2. Agent decides which tools (if any) it needs to use
# 3. Agent calls the appropriate tools with the right parameters
# 4. Agent receives tool results
# 5. Agent synthesizes the information and responds
#
# This is called "agentic behavior" - the agent autonomously decides
# how to accomplish the task using the tools at its disposal!
#
# Available Tools in strands_tools:
# - http_request: Make HTTP requests to APIs and websites
# - use_aws: Interact with AWS services (S3, DynamoDB, etc.)
# - current_time: Get current date/time
# - calculator: Perform mathematical calculations
# - retrieve: Search knowledge bases
# - And many more!
