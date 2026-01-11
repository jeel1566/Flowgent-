#!/usr/bin/env python3
"""
Test the improved node-info endpoint functionality
"""
import sys
import json
from typing import Dict, Any

# Simple mock for the endpoint logic
NODE_INFO_CACHE: Dict[str, Any] = {}

def get_node_info(node_type: str) -> Dict[str, Any]:
    """Get fast node information for Information Hand tooltip."""
    try:
        # Check cache first for speed
        if node_type in NODE_INFO_CACHE:
            print(f"Using cached info for: {node_type}")
            return NODE_INFO_CACHE[node_type]

        print(f"Getting fast node info for: {node_type}")
        
        # Mock fast response (simulating MCP call)
        result = {
            "name": node_type.split(".")[-1].replace("-", " ").title(),
            "description": f"Node for {node_type.split('.')[-1].replace('-', ' ').lower()} operations",
            "howItWorks": f"Configurable {node_type.split('.')[-1].replace('-', ' ').lower()} node for workflow automation",
            "whatItDoes": f"Executes {node_type.split('.')[-1].replace('-', ' ').lower()} tasks within automation workflows",
            "nodeType": node_type,
            "icon": ""
        }
        
        # Cache the result for future fast access
        NODE_INFO_CACHE[node_type] = result
        print(f"Cached node info for: {node_type}")
        return result
            
    except Exception as e:
        print(f"Error: {e}")
        # Return fast fallback instead of error
        return {
            "name": node_type.split(".")[-1].replace("-", " ").title(),
            "description": f"Node for {node_type.split('.')[-1].replace('-', ' ').lower()} operations",
            "howItWorks": f"Configurable {node_type.split('.')[-1].replace('-', ' ').lower()} node",
            "whatItDoes": f"Executes {node_type.split('.')[-1].replace('-', ' ').lower()} tasks in workflows",
            "nodeType": node_type,
            "icon": ""
        }

if __name__ == "__main__":
    # Test the endpoint logic
    test_cases = [
        "n8n-nodes-base.httpRequest",
        "n8n-nodes-base.slack",
        "n8n-nodes-base.set",
        "n8n-nodes-base.if"
    ]
    
    print("=== Testing Node Info Endpoint Logic ===\n")
    
    for node_type in test_cases:
        print(f"Test: {node_type}")
        result = get_node_info(node_type)
        print(f"Response: {json.dumps(result, indent=2)}")
        print("-" * 50)
    
    print("\n=== Testing Cache (Second Call) ===\n")
    
    # Test cache on second call
    for node_type in test_cases[:2]:  # Just test first 2
        print(f"Test cache: {node_type}")
        result = get_node_info(node_type)
        print(f"Response: {json.dumps(result, indent=2)}")
        print("-" * 50)