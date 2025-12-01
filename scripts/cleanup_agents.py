#!/usr/bin/env python3
"""
Cleanup script to delete all AgentCore Runtime agents except the builder agent.
"""

import boto3
import sys
from typing import List, Dict

REGION = 'us-west-2'
BUILDER_AGENT_ID = 'builder-cN967nENBt'  # Keep this one


def list_all_agents() -> List[Dict]:
    """List all agent runtimes"""
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    try:
        response = client.list_agent_runtimes()
        return response.get('agentRuntimes', [])
    except Exception as e:
        print(f"❌ Error listing agents: {e}")
        return []


def delete_agent(agent_id: str, agent_name: str) -> bool:
    """Delete a specific agent runtime"""
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    try:
        print(f"🗑️  Deleting agent: {agent_name} ({agent_id})...")
        client.delete_agent_runtime(agentRuntimeId=agent_id)
        print(f"✅ Deleted: {agent_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to delete {agent_name}: {e}")
        return False


def main():
    print("=" * 80)
    print("AgentCore Runtime Cleanup - Delete All Agents (except Builder)")
    print("=" * 80)
    print()
    
    # List all agents
    print("📋 Fetching all agents...")
    agents = list_all_agents()
    
    if not agents:
        print("✅ No agents found")
        return
    
    # Filter out builder agent
    agents_to_delete = [
        agent for agent in agents 
        if agent['agentRuntimeId'] != BUILDER_AGENT_ID
    ]
    
    if not agents_to_delete:
        print(f"✅ Only builder agent exists (keeping {BUILDER_AGENT_ID})")
        return
    
    print(f"\n🔍 Found {len(agents_to_delete)} agent(s) to delete:")
    for agent in agents_to_delete:
        name = agent.get('agentRuntimeName', 'unknown')
        agent_id = agent['agentRuntimeId']
        status = agent.get('status', 'unknown')
        print(f"  • {name} ({agent_id}) - {status}")
    
    print(f"\n⚠️  Keeping builder agent: {BUILDER_AGENT_ID}")
    print()
    
    # Confirm deletion
    response = input("⚠️  Delete these agents? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    print()
    
    # Delete agents
    deleted_count = 0
    failed_count = 0
    
    for agent in agents_to_delete:
        agent_id = agent['agentRuntimeId']
        agent_name = agent.get('agentRuntimeName', 'unknown')
        
        if delete_agent(agent_id, agent_name):
            deleted_count += 1
        else:
            failed_count += 1
    
    # Summary
    print()
    print("=" * 80)
    print(f"✅ Deleted: {deleted_count} agent(s)")
    if failed_count > 0:
        print(f"❌ Failed: {failed_count} agent(s)")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
