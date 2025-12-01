#!/usr/bin/env python3
"""
Cleanup script to delete all AgentCore Gateways and their Lambda targets.
"""

import boto3
import sys
import time
from typing import List, Dict

REGION = 'us-west-2'


def list_all_gateways() -> List[Dict]:
    """List all gateways with pagination support"""
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    try:
        all_gateways = []
        next_token = None
        
        while True:
            if next_token:
                response = client.list_gateways(nextToken=next_token)
            else:
                response = client.list_gateways()
            
            # API returns 'items' not 'gateways'
            gateways = response.get('items', [])
            all_gateways.extend(gateways)
            
            next_token = response.get('nextToken')
            if not next_token:
                break
        
        return all_gateways
    except Exception as e:
        print(f"❌ Error listing gateways: {e}")
        return []


def list_gateway_targets(gateway_id: str) -> List[Dict]:
    """List all targets for a gateway with pagination support"""
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    try:
        all_targets = []
        next_token = None
        
        while True:
            if next_token:
                response = client.list_gateway_targets(gatewayIdentifier=gateway_id, nextToken=next_token)
            else:
                response = client.list_gateway_targets(gatewayIdentifier=gateway_id)
            
            # API returns 'items' not 'gatewayTargets'
            targets = response.get('items', response.get('gatewayTargets', []))
            all_targets.extend(targets)
            
            next_token = response.get('nextToken')
            if not next_token:
                break
        
        return all_targets
    except Exception as e:
        print(f"❌ Error listing targets for gateway {gateway_id}: {e}")
        return []


def delete_gateway_target(gateway_id: str, target_id: str, target_name: str) -> bool:
    """Delete a gateway target"""
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    try:
        print(f"  🗑️  Deleting target: {target_name} ({target_id})...")
        client.delete_gateway_target(
            gatewayIdentifier=gateway_id,
            targetId=target_id
        )
        print(f"  ✅ Deleted target: {target_name}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to delete target {target_name}: {e}")
        return False


def delete_gateway(gateway_id: str, gateway_name: str) -> bool:
    """Delete a gateway and all its targets"""
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    print(f"\n🗑️  Deleting gateway: {gateway_name} ({gateway_id})")
    
    # First, delete all targets
    targets = list_gateway_targets(gateway_id)
    if targets:
        print(f"  📋 Found {len(targets)} target(s) to delete")
        for target in targets:
            target_id = target.get('targetId', target.get('gatewayTargetId', 'unknown'))
            target_name = target.get('name', target.get('gatewayTargetName', 'unknown'))
            delete_gateway_target(gateway_id, target_id, target_name)
            time.sleep(0.5)  # Small delay between deletions
        
        # Wait for targets to be fully deleted
        print(f"  ⏳ Waiting for targets to be fully deleted...")
        time.sleep(3)
    
    # Then delete the gateway with retries
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"  🗑️  Deleting gateway: {gateway_name}... (attempt {attempt + 1}/{max_retries})")
            client.delete_gateway(gatewayIdentifier=gateway_id)
            print(f"✅ Deleted gateway: {gateway_name}")
            return True
        except Exception as e:
            if "has targets associated" in str(e) and attempt < max_retries - 1:
                print(f"  ⏳ Targets still deleting, waiting...")
                time.sleep(2)
            else:
                print(f"❌ Failed to delete gateway {gateway_name}: {e}")
                return False
    
    return False


def main():
    print("=" * 80)
    print("AgentCore Gateway Cleanup - Delete All Gateways and Targets")
    print("=" * 80)
    print()
    
    # List all gateways
    print("📋 Fetching all gateways...")
    gateways = list_all_gateways()
    
    if not gateways:
        print("✅ No gateways found")
        return
    
    print(f"\n🔍 Found {len(gateways)} gateway(s) to delete:")
    for gateway in gateways:
        name = gateway.get('name', gateway.get('gatewayName', 'unknown'))
        gateway_id = gateway['gatewayId']
        status = gateway.get('status', 'unknown')
        print(f"  • {name} ({gateway_id}) - {status}")
    
    print()
    
    # Confirm deletion
    response = input("⚠️  Delete all gateways and their targets? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    print()
    
    # Delete gateways
    deleted_count = 0
    failed_count = 0
    
    for gateway in gateways:
        gateway_id = gateway['gatewayId']
        gateway_name = gateway.get('name', gateway.get('gatewayName', 'unknown'))
        
        if delete_gateway(gateway_id, gateway_name):
            deleted_count += 1
        else:
            failed_count += 1
        
        time.sleep(1)  # Delay between gateway deletions
    
    # Summary
    print()
    print("=" * 80)
    print(f"✅ Deleted: {deleted_count} gateway(s)")
    if failed_count > 0:
        print(f"❌ Failed: {failed_count} gateway(s)")
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
