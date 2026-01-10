#!/bin/bash
# Simple test runner for Flowgent backend

set -e

echo "================================"
echo "Flowgent Backend Tests"
echo "================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run syntax check
echo ""
echo "1. Checking Python syntax..."
python -m py_compile main.py
python -m py_compile api/routes.py
python -m py_compile agent/flowgent_agent.py
python -m py_compile n8n_mcp/n8n_client.py
python -m py_compile n8n_mcp/direct_client.py
echo "✅ Syntax check passed"

# Run import test
echo ""
echo "2. Testing imports..."
python -c "from main import app; print('✅ Main imports OK')"
python -c "from api.routes import router; print('✅ API routes imports OK')"
python -c "from agent.flowgent_agent import chat_with_agent; print('✅ Agent imports OK')"
python -c "from n8n_mcp.n8n_client import get_mcp_client; print('✅ MCP client imports OK')"
echo "✅ All imports successful"

# Run endpoint tests
echo ""
echo "3. Testing endpoints..."
python test_endpoints.py

echo ""
echo "================================"
echo "✅ All tests passed!"
echo "================================"
