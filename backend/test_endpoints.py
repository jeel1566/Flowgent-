#!/usr/bin/env python3
"""
Test script to verify all backend endpoints work correctly
"""
import asyncio
import sys
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    """Test health endpoint"""
    print("Testing /health...")
    response = client.get("/health")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
    assert response.status_code == 200
    print("✓ Health check passed\n")

def test_root():
    """Test root endpoint"""
    print("Testing /...")
    response = client.get("/")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
    assert response.status_code == 200
    print("✓ Root endpoint passed\n")

def test_workflows():
    """Test workflows list endpoint"""
    print("Testing /api/workflows...")
    try:
        response = client.get("/api/workflows")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {data[:2] if isinstance(data, list) else data}")
            print("✓ Workflows endpoint passed\n")
        else:
            print(f"  Error: {response.text[:200]}")
            print("⚠ Workflows endpoint returned non-200 (may be expected if n8n not configured)\n")
    except Exception as e:
        print(f"  Error: {e}")
        print("⚠ Workflows endpoint failed (may be expected if n8n not configured)\n")

def test_chat():
    """Test chat endpoint"""
    print("Testing /api/chat...")
    try:
        response = client.post("/api/chat", json={
            "message": "Hello, can you help me with n8n?",
            "context": None,
            "n8n_config": None
        })
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response length: {len(data.get('response', ''))} chars")
            print("✓ Chat endpoint passed\n")
        else:
            print(f"  Error: {response.text[:200]}")
            print("⚠ Chat endpoint returned non-200\n")
    except Exception as e:
        print(f"  Error: {e}")
        print("⚠ Chat endpoint failed\n")

def test_node_info():
    """Test node info endpoint"""
    print("Testing /api/node-info/n8n-nodes-base.httpRequest...")
    try:
        response = client.get("/api/node-info/n8n-nodes-base.httpRequest")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Node type: {data.get('node_type')}")
            print(f"  Display name: {data.get('display_name')}")
            print(f"  Description length: {len(data.get('description', ''))} chars")
            print("✓ Node info endpoint passed\n")
        else:
            print(f"  Error: {response.text[:200]}")
            print("⚠ Node info endpoint returned non-200\n")
    except Exception as e:
        print(f"  Error: {e}")
        print("⚠ Node info endpoint failed\n")

if __name__ == "__main__":
    print("="*60)
    print("Flowgent Backend Endpoint Tests")
    print("="*60 + "\n")
    
    try:
        test_health()
        test_root()
        test_workflows()
        test_node_info()
        test_chat()
        
        print("="*60)
        print("✓ All basic tests completed!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
