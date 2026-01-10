import os
import json
import logging
import re
from typing import Optional, Dict, Any, AsyncGenerator, List

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


# ============= Information Hand Preview Tools =============

async def get_node_preview(node_type: str, preview_type: str = "brief") -> Dict[str, Any]:
    """Get a quick preview of a node for Information Hand hover feature.
    
    Args:
        node_type: The n8n node type (e.g., 'n8n-nodes-base.httpRequest')
        preview_type: 'brief' for quick tooltip, 'full' for detailed preview
    
    Returns:
        Dictionary with preview information for display
    """
    try:
        client = get_mcp_client()
        
        # Get basic node info
        node_info = await client.get_node(node_type, mode="docs", detail="standard")
        
        if preview_type == "brief":
            # Quick summary for hover tooltip
            return {
                "status": "success",
                "preview": {
                    "node_type": node_type,
                    "display_name": _extract_display_name(node_type, node_info),
                    "short_description": _get_short_description(node_info),
                    "icon_emoji": _get_node_icon(node_type),
                    "category": _get_node_category(node_type),
                    "popularity": _get_node_popularity(node_type)
                }
            }
        else:
            # Full preview with examples and use cases
            return {
                "status": "success",
                "preview": {
                    "node_type": node_type,
                    "display_name": _extract_display_name(node_type, node_info),
                    "description": _get_description(node_info),
                    "icon_emoji": _get_node_icon(node_type),
                    "category": _get_node_category(node_type),
                    "parameters": _extract_parameters(node_info),
                    "use_cases": _extract_use_cases(node_info),
                    "best_practices": _extract_best_practices(node_info),
                    "example_configs": _extract_examples(node_info),
                    "documentation_url": _get_docs_url(node_type)
                }
            }
    except Exception as e:
        logger.error(f"Error getting node preview: {e}")
        return {"status": "error", "message": str(e), "preview_type": preview_type}


async def search_nodes_for_preview(query: str, limit: int = 5) -> Dict[str, Any]:
    """Quick search for nodes with preview data - optimized for Information Hand."""
    try:
        client = get_mcp_client()
        results = await client.search_nodes(query, include_examples=True)
        
        previews = []
        if isinstance(results, dict) and "results" in results:
            for item in results["results"][:limit]:
                previews.append({
                    "node_type": item.get("nodeType", item.get("id")),
                    "display_name": item.get("name", item.get("nodeType", "Unknown")),
                    "short_description": item.get("description", "")[:100],
                    "icon_emoji": _get_node_icon(item.get("nodeType", "")),
                    "category": _get_node_category(item.get("nodeType", ""))
                })
        
        return {"status": "success", "previews": previews, "query": query}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============= Helper Functions for Node Previews =============

def _extract_display_name(node_type: str, node_info: Any) -> str:
    """Extract display name from node type or info."""
    if isinstance(node_info, dict):
        name = node_info.get("name") or node_info.get("displayName")
        if name:
            return name
    
    # Parse from node type
    parts = node_type.split(".")
    if len(parts) > 1:
        # Convert camelCase to spaced words
        last_part = parts[-1]
        spaced = re.sub(r'([A-Z])', r' \1', last_part)
        return spaced.strip()
    return node_type


def _get_short_description(node_info: Any) -> str:
    """Get short description for hover tooltip."""
    if isinstance(node_info, dict):
        return node_info.get("text", node_info.get("description", ""))[:150]
    return str(node_info)[:150]


def _get_description(node_info: Any) -> str:
    """Get full description."""
    if isinstance(node_info, dict):
        return node_info.get("text", node_info.get("description", "No description available"))
    return str(node_info)


def _get_node_icon(node_type: str) -> str:
    """Get emoji icon for node type."""
    icons = {
        "httpRequest": "🌐",
        "webhook": "🪝",
        "set": "📝",
        "if": "🔀",
        "switch": "🎛️",
        "code": "💻",
        "function": "⚡",
        "slack": "💬",
        "googleSheets": "📊",
        "gmail": "📧",
        "scheduleTrigger": "⏰",
        "cron": "⏰",
        "merge": "🔗",
        "postgres": "🐘",
        "mysql": "🐬",
        "notion": "📓",
        "airtable": "📋",
        "discord": "🎮",
        "telegram": "✈️",
        "openai": "🤖",
        "ai": "🧠",
        "database": "💾",
        "api": "🔌",
        "trigger": "🚀",
        "email": "📬",
        "http": "🌐",
        "filter": "🔍",
        "editFields": "✏️",
        "noOp": "⏭️",
        "wait": "⏳",
        "errorTrigger": "⚠️",
    }
    
    lower = node_type.lower()
    for key, icon in icons.items():
        if key.lower() in lower:
            return icon
    return "📦"


def _get_node_category(node_type: str) -> str:
    """Get category for node type."""
    categories = {
        "http": "Core",
        "webhook": "Core",
        "set": "Core",
        "if": "Logic",
        "switch": "Logic",
        "code": "Core",
        "function": "Core",
        "scheduleTrigger": "Trigger",
        "cron": "Trigger",
        "slack": "Communication",
        "googleSheets": "Data & Storage",
        "gmail": "Communication",
        "postgres": "Data & Storage",
        "mysql": "Data & Storage",
        "notion": "Data & Storage",
        "airtable": "Data & Storage",
        "discord": "Communication",
        "telegram": "Communication",
        "openai": "AI",
        "ai": "AI",
        "database": "Data & Storage",
        "trigger": "Trigger",
        "email": "Communication",
        "filter": "Data & Storage",
    }
    
    lower = node_type.lower()
    for key, category in categories.items():
        if key.lower() in lower:
            return category
    return "General"


def _get_node_popularity(node_type: str) -> str:
    """Get popularity indicator for node type."""
    popular = {
        "httpRequest": "⭐⭐⭐⭐⭐",
        "webhook": "⭐⭐⭐⭐⭐",
        "set": "⭐⭐⭐⭐⭐",
        "if": "⭐⭐⭐⭐⭐",
        "code": "⭐⭐⭐⭐",
        "scheduleTrigger": "⭐⭐⭐⭐",
        "slack": "⭐⭐⭐⭐",
        "gmail": "⭐⭐⭐⭐",
        "googleSheets": "⭐⭐⭐⭐",
    }
    
    lower = node_type.lower()
    for key, pop in popular.items():
        if key.lower() in lower:
            return pop
    return "⭐⭐"


def _extract_parameters(node_info: Any) -> List[Dict[str, Any]]:
    """Extract parameters from node info."""
    if isinstance(node_info, dict):
        return node_info.get("parameters", [])
    return []


def _extract_use_cases(node_info: Any) -> List[str]:
    """Extract use cases from node info."""
    if isinstance(node_info, dict):
        return node_info.get("useCases", node_info.get("use_cases", []))
    return []


def _extract_best_practices(node_info: Any) -> List[str]:
    """Extract best practices from node info."""
    if isinstance(node_info, dict):
        return node_info.get("bestPractices", node_info.get("best_practices", []))
    return []


def _extract_examples(node_info: Any) -> List[Dict[str, Any]]:
    """Extract example configurations from node info."""
    if isinstance(node_info, dict):
        return node_info.get("examples", node_info.get("example_configs", []))
    return []


def _get_docs_url(node_type: str) -> str:
    """Get documentation URL for node."""
    return f"https://docs.n8n.io/integrations/builtin/node-n8n-nodes-base/{node_type.split('.')[-1].lower()}/"


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
            # Information Hand preview tools
            get_node_preview,
            search_nodes_for_preview,
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
        logger.error(f"Error during agent run: {e}")
        return f"Error processing request: {str(e)}"
        
    return final_response if final_response else "I processed your request but have no response."


async def stream_chat_with_agent(message: str, session_id: str = "default_session") -> AsyncGenerator[str, None]:
    """Stream response from the agent for real-time updates."""
    runner = get_runner()
    await ensure_session(session_id)
    
    user_content = types.Content(role="user", parts=[types.Part(text=message)])
    
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
                            yield part.text
            else:
                # Stream partial responses if available
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            yield part.text
    except Exception as e:
        logger.error(f"Error during agent stream: {e}")
        yield f"Error processing request: {str(e)}"
