from fastapi import APIRouter, HTTPException, Query, Header
from typing import List, Optional
from models.schemas import (
    ChatMessage, ChatResponse, WorkflowListItem, Workflow,
    ExecutionRequest, ExecutionResponse, NodeInfo, CreateWorkflowRequest
)
from agent.flowgent_agent import chat_with_agent
from n8n_mcp.n8n_client import get_mcp_client
from n8n_mcp.direct_client import create_n8n_client

router = APIRouter(prefix="/api", tags=["api"])


def get_n8n_client_from_headers(instance_url: str = None, api_key: str = None):
    """Get n8n client from request headers or fall back to MCP."""
    if instance_url and api_key:
        return create_n8n_client(instance_url, api_key)
    return None


@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Chat with the Flowgent AI assistant."""
    try:
        session_id = "default_session"
        if message.context and "session_id" in message.context:
            session_id = message.context["session_id"]
        
        # Store n8n config in context for agent to use
        context = message.context or {}
        if message.n8n_config:
            context["n8n_instance_url"] = message.n8n_config.instance_url
            context["n8n_api_key"] = message.n8n_config.api_key
            
        response_text = await chat_with_agent(message.message, session_id)
        return ChatResponse(response=response_text, workflow_data=None, action=None)
    except Exception as e:
        return ChatResponse(response=f"Error: {str(e)}")


@router.get("/workflows", response_model=List[WorkflowListItem])
async def list_workflows(
    x_n8n_instance_url: Optional[str] = Header(None, alias="X-N8N-Instance-URL"),
    x_n8n_api_key: Optional[str] = Header(None, alias="X-N8N-API-Key")
):
    """Get all workflows from n8n."""
    try:
        # Try direct n8n client first
        direct_client = get_n8n_client_from_headers(x_n8n_instance_url, x_n8n_api_key)
        if direct_client:
            workflows = await direct_client.list_workflows()
        else:
            # Fall back to MCP
            client = get_mcp_client()
            workflows = await client.list_workflows()
        
        return [
            WorkflowListItem(
                id=w.get("id", ""),
                name=w.get("name", "Untitled"),
                active=w.get("active", False),
                createdAt=w.get("createdAt"),
                updatedAt=w.get("updatedAt")
            ) for w in workflows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}", response_model=Workflow)
async def get_workflow(
    workflow_id: str,
    x_n8n_instance_url: Optional[str] = Header(None, alias="X-N8N-Instance-URL"),
    x_n8n_api_key: Optional[str] = Header(None, alias="X-N8N-API-Key")
):
    """Get a specific workflow by ID."""
    try:
        direct_client = get_n8n_client_from_headers(x_n8n_instance_url, x_n8n_api_key)
        if direct_client:
            workflow = await direct_client.get_workflow(workflow_id)
        else:
            client = get_mcp_client()
            workflow = await client.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return Workflow(
            id=workflow.get("id"),
            name=workflow.get("name", "Untitled"),
            active=workflow.get("active", False),
            nodes=workflow.get("nodes", []),
            connections=workflow.get("connections", {}),
            createdAt=workflow.get("createdAt"),
            updatedAt=workflow.get("updatedAt")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows", response_model=Workflow)
async def create_workflow(req: CreateWorkflowRequest):
    """Create a new workflow in n8n."""
    try:
        # Use direct client if n8n config provided
        if req.n8n_config and req.n8n_config.instance_url and req.n8n_config.api_key:
            direct_client = create_n8n_client(req.n8n_config.instance_url, req.n8n_config.api_key)
            result = await direct_client.create_workflow(req.name, req.nodes, req.connections)
        else:
            # Fall back to MCP
            client = get_mcp_client()
            result = await client.create_workflow(req.name, req.nodes, req.connections)
        
        return Workflow(
            id=result.get("id"),
            name=result.get("name", req.name),
            active=result.get("active", False),
            nodes=result.get("nodes", req.nodes),
            connections=result.get("connections", req.connections)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=ExecutionResponse)
async def execute_workflow(req: ExecutionRequest):
    """Execute a workflow with optional input data."""
    try:
        if req.n8n_config and req.n8n_config.instance_url and req.n8n_config.api_key:
            direct_client = create_n8n_client(req.n8n_config.instance_url, req.n8n_config.api_key)
            result = await direct_client.execute_workflow(req.workflow_id, req.input_data)
        else:
            client = get_mcp_client()
            result = await client.execute_workflow(req.workflow_id, req.input_data)
        
        return ExecutionResponse(
            execution_id=result.get("id", "unknown"),
            success=result.get("success", False),
            data=result.get("data"),
            error=result.get("error"),
            started_at=result.get("startedAt"),
            finished_at=result.get("finishedAt")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node-info/{node_type:path}", response_model=NodeInfo)
async def get_node_info(node_type: str):
    """Get detailed information about an n8n node type."""
    try:
        client = get_mcp_client()
        info = await client.get_node_info(node_type)
        
        if info:
            # Parse MCP response
            description = info.get("text", "") if isinstance(info, dict) else str(info)
            return NodeInfo(
                node_type=node_type,
                display_name=node_type.split(".")[-1],
                description=description,
                parameters=[],
                use_cases=[],
                best_practices=[],
                example_config=None
            )
        
        # Fall back to AI-generated info
        response = await chat_with_agent(
            f"Provide a brief description and use cases for the n8n node type: {node_type}",
            session_id="node_info_session"
        )
        
        return NodeInfo(
            node_type=node_type,
            display_name=node_type.split(".")[-1],
            description=response,
            parameters=[],
            use_cases=[],
            best_practices=[],
            example_config=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions")
async def list_executions(
    workflow_id: Optional[str] = Query(None),
    x_n8n_instance_url: Optional[str] = Header(None, alias="X-N8N-Instance-URL"),
    x_n8n_api_key: Optional[str] = Header(None, alias="X-N8N-API-Key")
):
    """Get execution history."""
    try:
        direct_client = get_n8n_client_from_headers(x_n8n_instance_url, x_n8n_api_key)
        if direct_client:
            executions = await direct_client.list_executions(workflow_id)
        else:
            client = get_mcp_client()
            executions = await client.list_executions(workflow_id)
        
        return executions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
