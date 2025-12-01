"""
5: Knowledge Base Integration
=======================================
This example demonstrates how to connect your agent to a knowledge base
for Retrieval-Augmented Generation (RAG). This allows agents to answer
questions based on your organization's specific documents and data.

Use Case: HR Assistant
An agent that can answer employee questions by searching company HR policies
stored in an AWS Bedrock Knowledge Base.
"""

# ============================================================================
# STEP 1: Import Required Components
# ============================================================================
from strands import Agent
from strands_tools import retrieve  # Tool for searching knowledge bases
from strands.models import BedrockModel


# ============================================================================
# STEP 2: Configure the Model
# ============================================================================
# Use Claude Sonnet for strong reasoning and comprehension
model = BedrockModel(
    model_id="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    streaming=True
)


# ============================================================================
# STEP 3: Specify Your Knowledge Base
# ============================================================================
# AWS Bedrock Knowledge Base ID
# This KB contains company HR policies, benefits information, etc.
# Replace with your own Knowledge Base ID
kb_id = "ESIT73MSXO"


# ============================================================================
# STEP 4: Create Knowledge Base-Enabled Agent
# ============================================================================
# This agent is specialized for answering HR questions using the KB
agent_kb = Agent(
    model=model,
    
    # System prompt defines the agent's role and how to use the KB
    system_prompt=f"""You are a friendly HR Assistant helping employees find answers to HR questions. 

Use the retrieve tool to search the company's HR knowledge base (KB ID: {kb_id}) before answering any question. Provide clear, accurate answers based on the knowledge base content.

When answering:
- Be concise and helpful
- Reference the source policy or document
- If information isn't in the knowledge base, direct employees to contact HR directly at [hr@company.com]
- Never ask for or store personal employee information

Common topics: vacation policies, benefits, leave policies, company holidays, performance reviews, expenses, and workplace guidelines.
""",
    
    # Provide the retrieve tool for KB search
    # The agent will automatically use this to search the knowledge base
    tools=[retrieve]
)


# ============================================================================
# STEP 5: Query the Agent
# ============================================================================
# Ask a question that requires knowledge base lookup
# The agent will:
# 1. Use the retrieve tool to search the KB
# 2. Find relevant documents/passages
# 3. Synthesize an answer based on the retrieved information
response = agent_kb("What's the vacation policy of the company?")


# ============================================================================
# How Knowledge Base Integration Works:
# ============================================================================
# 1. User asks a question
# 2. Agent uses 'retrieve' tool with the KB ID
# 3. Bedrock Knowledge Base performs semantic search
# 4. Relevant documents/passages are returned
# 5. Agent synthesizes answer from retrieved content
# 6. Agent cites sources from the knowledge base
#
# Benefits of RAG with Knowledge Bases:
# - Answers based on your specific documents
# - Reduces hallucinations (grounded in real data)
# - Easy to update (just update the KB)
# - Automatic citation of sources
# - Scales to large document collections
#
# Setting Up a Knowledge Base:
# 1. Create a Knowledge Base in AWS Bedrock console
# 2. Upload your documents (PDFs, text files, etc.)
# 3. Configure data source (S3, web crawler, etc.)
# 4. Sync the knowledge base
# 5. Use the KB ID in your agent
#
# Common Use Cases:
# - HR policy assistants
# - Technical documentation Q&A
# - Customer support bots
# - Internal knowledge management
# - Compliance and regulatory guidance

