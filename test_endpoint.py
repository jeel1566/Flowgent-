#!/usr/bin/env python3
"""
Simple test for the node-info endpoint without full agent dependencies
"""
import json
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Create a minimal test version of the endpoint
app = FastAPI()

# Mock cache
NODE_INFO_CACHE = {}

@app.get("/api/node-info/{node_type:path}")
async def get_node_info(node_type: str):
    """Get fast node information for Information Hand tooltip."""
    try:
        # Check cache first for speed
        if node_type in NODE_INFO_CACHE:
            return NODE_INFO_CACHE[node_type]

        print(f"Getting fast node info for: {node_type}")
        
        # Mock fast response
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
    client = TestClient(app)
    
    # Test the endpoint
    response = client.get("/api/node-info/n8n-nodes-base.httpRequest")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test cache on second call
    print("\n--- Testing cache ---")
    response2 = client.get("/api/node-info/n8n-nodes-base.httpRequest")
    print(f"Status: {response2.status_code}")
    print(f"Response: {json.dumps(response2.json(), indent=2)}")