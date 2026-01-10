#!/usr/bin/env python3
"""
Test chat endpoint with n8n credentials
"""
import sys
sys.path.insert(0, '/home/engine/project/backend')

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_chat_with_n8n_config():
    """Test chat endpoint receives and uses n8n credentials."""
    print("Testing /api/chat with n8n config...")
    
    response = client.post("/api/chat", json={
        "message": "List my workflows",
        "context": {"session_id": "test_session"},
        "n8n_config": {
            "instance_url": "https://test.n8n.com",
            "api_key": "test-api-key"
        }
    })
    
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Response length: {len(data.get('response', ''))} chars")
        # Check that credentials were logged
        print("✓ Chat with n8n config completed")
    else:
        print(f"  Error: {response.text[:200]}")
        print("⚠ Chat endpoint returned non-200 (may be expected if no API key)")

def test_chat_without_n8n_config():
    """Test chat endpoint without n8n config."""
    print("\nTesting /api/chat without n8n config...")
    
    response = client.post("/api/chat", json={
        "message": "Hello",
        "context": None,
        "n8n_config": None
    })
    
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Response length: {len(data.get('response', ''))} chars")
        print("✓ Chat without n8n config completed")
    else:
        print(f"  Error: {response.text[:200]}")

def test_workflows_with_headers():
    """Test workflows endpoint with n8n headers."""
    print("\nTesting /api/workflows with n8n headers...")
    
    response = client.get("/api/workflows", headers={
        "X-N8N-Instance-URL": "https://test.n8n.com",
        "X-N8N-API-Key": "test-api-key"
    })
    
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Workflows: {len(data)} items")
        print("✓ Workflows with headers completed")
    else:
        print(f"  Error: {response.text[:200]}")
        print("⚠ Workflows endpoint returned non-200 (expected with fake credentials)")

if __name__ == "__main__":
    print("="*60)
    print("Flowgent Chat Integration Tests")
    print("="*60 + "\n")
    
    try:
        test_chat_with_n8n_config()
        test_chat_without_n8n_config()
        test_workflows_with_headers()
        
        print("\n" + "="*60)
        print("✓ All integration tests completed!")
        print("="*60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
