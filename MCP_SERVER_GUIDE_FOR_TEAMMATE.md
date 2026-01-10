# n8n MCP Server Setup for Flowgent Project

## Project Context

**Flowgent** is an AI-powered browser extension for n8n automation that we're building for the Agentic+ Product Hackathon. It has three main features:

1. **AI Chat Assistant** - Users can chat with an AI to create, modify, and debug n8n workflows
2. **Information Hand** - Floating tooltips that show node documentation when hovering over nodes in n8n
3. **Dashboard** - View workflow lists, execution history, and test workflows with custom inputs

## Your Role: n8n MCP Server

You're responsible for setting up the **n8n Model Context Protocol (MCP) server** that will allow our AI agent to interact with n8n programmatically.

### What is MCP?

Model Context Protocol (MCP) is a standard that connects AI systems with external tools and data sources. In our case, it lets our Gemini-powered AI agent interact with n8n to:
- List workflows
- Create new workflows
- Modify existing workflows
- Execute workflows
- Get workflow execution history
- Retrieve node information and documentation

---

## What You Need to Build

### 1. MCP Server Implementation

Create an MCP server that exposes n8n functionality through the following tools/resources:

#### Required MCP Tools:

**Workflow Management:**
- `list_workflows` - Get all workflows from n8n instance
- `get_workflow` - Get a specific workflow by ID with full details
- `create_workflow` - Create a new workflow from JSON definition
- `update_workflow` - Modify an existing workflow
- `delete_workflow` - Remove a workflow

**Execution:**
- `execute_workflow` - Run a workflow with optional input data
- `get_execution` - Get execution details by ID
- `list_executions` - Get execution history for a workflow

**Node Information:**
- `get_node_types` - List all available node types (including custom nodes)
- `get_node_info` - Get detailed info for a specific node type (description, parameters, examples)

**Example MCP Tool Definition:**
```python
@server.tool()
async def list_workflows() -> List[Dict]:
    """List all workflows from the n8n instance."""
    # Call n8n API
    response = await n8n_client.get("/workflows")
    return response.json()

@server.tool()
async def create_workflow(name: str, nodes: List[Dict], connections: Dict) -> Dict:
    """Create a new n8n workflow."""
    workflow_data = {
        "name": name,
        "nodes": nodes,
        "connections": connections,
        "active": False
    }
    response = await n8n_client.post("/workflows", json=workflow_data)
    return response.json()
```

### 2. n8n API Integration

Your MCP server needs to communicate with an n8n instance. You'll use the **n8n REST API**:

**n8n API Endpoints:**
- Base URL: `https://your-n8n-instance.com/api/v1/`
- Authentication: API Key (set in n8n settings)

**Key API Endpoints:**
- `GET /workflows` - List workflows
- `POST /workflows` - Create workflow
- `GET /workflows/:id` - Get workflow
- `PATCH /workflows/:id` - Update workflow
- `POST /workflows/:id/execute` - Execute workflow
- `GET /executions` - List executions
- `GET /node-types` - Get available node types

**Example:**
```python
import httpx

class N8nClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"X-N8N-API-KEY": api_key}
    
    async def get(self, endpoint: str):
        async with httpx.AsyncClient() as client:
            return await client.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers
            )
    
    async def post(self, endpoint: str, json: dict):
        async with httpx.AsyncClient() as client:
            return await client.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                json=json
            )
```

### 3. Configuration

Your server needs these environment variables:
- `N8N_BASE_URL` - Your n8n instance URL (e.g., `https://n8n.yourdomain.com/api/v1/`)
- `N8N_API_KEY` - API key for authentication (generate this in n8n user settings)

---

## Deployment Strategy

### Option 1: Local Development First (Recommended)

**Step 1:** Run n8n locally
```bash
# Using Docker
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -e N8N_API_KEY=your-api-key-here \
  n8nio/n8n

# Or using npm
npm install -g n8n
n8n start
```

**Step 2:** Create and run your MCP server locally
```bash
# Your MCP server
python mcp_server.py
# Should expose MCP endpoints on stdio or HTTP
```

**Step 3:** Test integration with our backend
- Our backend will connect to your MCP server
- We'll test workflow creation and execution locally first

### Option 2: Cloud Deployment (for Production)

Once local testing works, deploy both to Google Cloud Run:

**Deploy n8n to Cloud Run:**
```bash
# Create Dockerfile for n8n
gcloud run deploy n8n-instance \
  --image n8nio/n8n \
  --platform managed \
  --region us-central1 \
  --set-env-vars N8N_BASIC_AUTH_ACTIVE=true \
  --set-env-vars N8N_BASIC_AUTH_USER=admin \
  --set-env-vars N8N_BASIC_AUTH_PASSWORD=yourpassword
```

**Deploy your MCP server to Cloud Run:**
```bash
gcloud run deploy n8n-mcp-server \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars N8N_BASE_URL=https://your-n8n-cloudrun-url/api/v1/ \
  --set-env-vars N8N_API_KEY=your-api-key
```

### Option 3: Use Existing n8n Cloud Instance

If you have an n8n.cloud account:
1. Get your n8n.cloud instance URL
2. Generate an API key in settings
3. Point your MCP server to that URL
4. Deploy only the MCP server to Cloud Run

---

## Integration with Our Backend

Our Python backend (FastAPI + Google Agent SDK) will connect to your MCP server like this:

```python
from google.genai import Client
from google.genai.types import Tool, GenerateContentConfig

# Initialize MCP client
mcp_client = await create_mcp_client("your-mcp-server-url")

# Create agent with MCP tools
client = Client(api_key=os.getenv("GEMINI_API_KEY"))
agent = client.agentic.create_agent(
    model="gemini-2.0-flash-exp",
    tools=[mcp_client.get_tools()],  # Your MCP tools
    config=GenerateContentConfig(
        system_instruction="You are an n8n workflow expert..."
    )
)
```

**What we need from you:**
- MCP server endpoint URL (e.g., `http://localhost:3000` for local or Cloud Run URL)
- Connection method (stdio, HTTP, SSE)
- Any authentication required

---

## Testing Checklist

Before integration, please verify:

- [ ] MCP server starts successfully
- [ ] Can connect to n8n instance
- [ ] `list_workflows` returns workflow data
- [ ] `create_workflow` successfully creates a simple workflow
- [ ] `execute_workflow` runs and returns results
- [ ] `get_node_types` returns node information
- [ ] All errors are handled gracefully (n8n down, invalid API key, etc.)

**Test with these commands:**
```bash
# Test list workflows
curl -X POST http://your-mcp-server/mcp \
  -H "Content-Type: application/json" \
  -d '{"tool": "list_workflows", "arguments": {}}'

# Test create workflow
curl -X POST http://your-mcp-server/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "create_workflow",
    "arguments": {
      "name": "Test Workflow",
      "nodes": [...],
      "connections": {...}
    }
  }'
```

---

## Resources

**n8n API Documentation:**
- https://docs.n8n.io/api/

**Google MCP SDK:**
- https://github.com/google/genai-sdk-python
- MCP Documentation: https://modelcontextprotocol.io/

**Example MCP Servers:**
- https://github.com/modelcontextprotocol/servers

**n8n on Cloud Run:**
- https://docs.n8n.io/hosting/installation/docker/

---

## Timeline & Coordination

**What we need from you:**
1. Basic MCP server running (local is fine) - **ASAP**
2. At minimum: `list_workflows`, `create_workflow`, `execute_workflow` tools
3. Your server URL and connection details
4. Cloud deployment (can be done later if time permits)

**We'll handle:**
- Frontend Chrome extension
- AI agent integration
- User interface
- Extension deployment

**Let's sync when:**
- Your MCP server is ready for integration testing
- You hit any blockers
- Ready to deploy to Cloud Run

---

## Quick Start Template

Here's a minimal MCP server to get started:

```python
# mcp_server.py
import asyncio
from typing import List, Dict
from mcp.server import Server, Tool
import httpx
import os

# Initialize MCP server
server = Server("n8n-mcp-server")

# n8n API client
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "http://localhost:5678/api/v1")
N8N_API_KEY = os.getenv("N8N_API_KEY")

async def n8n_request(method: str, endpoint: str, **kwargs):
    """Make request to n8n API"""
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            f"{N8N_BASE_URL}{endpoint}",
            headers={"X-N8N-API-KEY": N8N_API_KEY},
            **kwargs
        )
        return response.json()

@server.tool()
async def list_workflows() -> List[Dict]:
    """List all workflows"""
    return await n8n_request("GET", "/workflows")

@server.tool()
async def create_workflow(name: str, nodes: List[Dict], connections: Dict) -> Dict:
    """Create a new workflow"""
    data = {"name": name, "nodes": nodes, "connections": connections}
    return await n8n_request("POST", "/workflows", json=data)

@server.tool()
async def execute_workflow(workflow_id: str, input_data: Dict = None) -> Dict:
    """Execute a workflow"""
    return await n8n_request("POST", f"/workflows/{workflow_id}/execute", json=input_data or {})

if __name__ == "__main__":
    # Run server
    asyncio.run(server.run())
```

---

## Questions?

If you have any questions or need clarification:
1. Check the n8n API docs first
2. Look at MCP example servers
3. Ask in our hackathon team chat
4. We can pair program if needed!

**Good luck! Let's build something awesome! 🚀**
