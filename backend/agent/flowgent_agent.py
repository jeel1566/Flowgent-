import os
import json
import logging
from typing import Optional, Dict, Any

# ADK imports
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent.config import AGENT_MODEL, SYSTEM_INSTRUCTION, get_gemini_api_key
from n8n_mcp.n8n_client import get_mcp_client

logger = logging.getLogger(__name__)

# ============= Core MCP Tools (Work without n8n API) =============

async def search_nodes(query: str) -> Dict[str, Any]:
    """Search for n8n nodes by name or description. Use this to find nodes for workflows."""
    try:
        client = get_mcp_client()
        result = await client.search_nodes(query)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_node_documentation(node_type: str) -> Dict[str, Any]:
    """Get detailed documentation for a specific n8n node type (e.g., 'n8n-nodes-base.httpRequest')."""
    try:
        client = get_mcp_client()
        result = await client.get_node(node_type, mode="docs", detail="full")
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def search_workflow_templates(query: str) -> Dict[str, Any]:
    """Search for workflow templates by keyword."""
    try:
        client = get_mcp_client()
        result = await client.search_templates(query, search_mode="keyword")
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_workflow_template(template_id: str) -> Dict[str, Any]:
    """Get a specific workflow template by ID."""
    try:
        client = get_mcp_client()
        result = await client.get_template(template_id, mode="full")
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def validate_workflow_json(workflow_json: str) -> Dict[str, Any]:
    """Validate a workflow JSON structure."""
    try:
        workflow = json.loads(workflow_json) if isinstance(workflow_json, str) else workflow_json
        client = get_mcp_client()
        result = await client.validate_workflow(workflow)
        return {"status": "success", "data": result}
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"Invalid JSON: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============= n8n Management Tools (Require n8n API Config) =============

async def list_workflows() -> Dict[str, Any]:
    """List all workflows from connected n8n instance."""
    try:
        client = get_mcp_client()
        workflows = await client.list_workflows()
        return {
            "status": "success",
            "count": len(workflows),
            "workflows": [{"id": w.get("id"), "name": w.get("name"), "active": w.get("active")} for w in workflows]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_workflow(workflow_id: str) -> Dict[str, Any]:
    """Get a specific workflow by ID from connected n8n instance."""
    try:
        client = get_mcp_client()
        workflow = await client.get_workflow(workflow_id)
        if workflow:
            return {"status": "success", "workflow": workflow}
        return {"status": "error", "message": f"Workflow {workflow_id} not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def create_workflow(name: str, description: str, nodes_json: str) -> Dict[str, Any]:
    """Create a new n8n workflow from JSON definition."""
    try:
        nodes_data = json.loads(nodes_json) if isinstance(nodes_json, str) else nodes_json
        nodes = nodes_data.get("nodes", [])
        connections = nodes_data.get("connections", {})
        
        client = get_mcp_client()
        result = await client.create_workflow(name, nodes, connections)
        return {"status": "success", "workflow_id": result.get("id"), "name": name}
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"Invalid JSON: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def execute_workflow(workflow_id: str, input_data: Optional[str] = None) -> Dict[str, Any]:
    """Execute a workflow with optional input data."""
    try:
        parsed_input = None
        if input_data:
            parsed_input = json.loads(input_data) if isinstance(input_data, str) else input_data
        
        client = get_mcp_client()
        result = await client.execute_workflow(workflow_id, parsed_input)
        return {"status": "success", "execution_id": result.get("id"), "result": result}
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"Invalid input JSON: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============= ADK Agent =============

def create_flowgent_agent() -> Agent:
    """Create the Flowgent agent with all MCP tools."""
    return Agent(
        name="flowgent",
        model=AGENT_MODEL,
        description="AI assistant for n8n workflow automation with MCP integration",
        instruction=SYSTEM_INSTRUCTION,
        tools=[
            # Core MCP tools (always work)
            search_nodes,
            get_node_documentation,
            search_workflow_templates,
            get_workflow_template,
            validate_workflow_json,
            # n8n management tools (need n8n API)
            list_workflows,
            get_workflow,
            create_workflow,
            execute_workflow,
        ]
    )


APP_NAME = "flowgent"
USER_ID = "default_user"

# Singletons
_session_service: Optional[InMemorySessionService] = None
_runner: Optional[Runner] = None
_agent: Optional[Agent] = None


def get_session_service() -> InMemorySessionService:
    global _session_service
    if _session_service is None:
        _session_service = InMemorySessionService()
    return _session_service


def _init_env():
    api_key = get_gemini_api_key()
    os.environ["GOOGLE_GENAI_API_KEY"] = api_key


def get_agent() -> Agent:
    global _agent
    if _agent is None:
        _init_env()
        _agent = create_flowgent_agent()
    return _agent


def get_runner() -> Runner:
    global _runner
    if _runner is None:
        _init_env()
        _runner = Runner(
            agent=get_agent(),
            app_name=APP_NAME,
            session_service=get_session_service()
        )
    return _runner


async def ensure_session(session_id: str):
    """Ensure session exists - only create if it doesn't exist."""
    svc = get_session_service()
    session = await svc.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)
    if session is None:
        logger.info(f"Creating new session: {session_id}")
        await svc.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)


async def chat_with_agent(message: str, session_id: str = "default_session") -> str:
    """Send a message to the agent and get a response."""
    try:
        runner = get_runner()
        await ensure_session(session_id)
        
        user_content = types.Content(role="user", parts=[types.Part(text=message)])
        
        final_response = ""
        try:
            async for event in runner.run_async(
                user_id=USER_ID,
                session_id=session_id,
                new_message=user_content
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                final_response += part.text
        except Exception as e:
            logger.error(f"Error during agent run: {e}", exc_info=True)
            
            # Check if it's an API key error
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "missing key" in error_msg.lower():
                return (
                    "⚠️ **API Key Not Configured**\n\n"
                    "The Gemini API key is not set. Please configure it in your backend .env file:\n\n"
                    "1. Get your API key from: https://aistudio.google.com/apikey\n"
                    "2. Add it to backend/.env: `GOOGLE_GENAI_API_KEY=your-key-here`\n"
                    "3. Restart the backend\n\n"
                    "Until then, I can't provide AI-powered responses, but the n8n MCP tools should still work."
                )
            
            return f"Error processing request: {str(e)}"
            
        return final_response if final_response else "I processed your request but have no response."
    except ValueError as e:
        # Handle API key configuration errors
        error_msg = str(e)
        if "GOOGLE_GENAI_API_KEY" in error_msg:
            return (
                "⚠️ **API Key Not Configured**\n\n"
                "The Gemini API key is not set. Please configure it in your backend .env file:\n\n"
                "1. Get your API key from: https://aistudio.google.com/apikey\n"
                "2. Add it to backend/.env: `GOOGLE_GENAI_API_KEY=your-key-here`\n"
                "3. Restart the backend"
            )
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat_with_agent: {e}", exc_info=True)
        return f"An unexpected error occurred: {str(e)}"
