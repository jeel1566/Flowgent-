from fastapi import APIRouter, HTTPException, Query, Header
from typing import List, Optional
import logging
from models.schemas import (
    ChatMessage, ChatResponse, WorkflowListItem, Workflow,
    ExecutionRequest, ExecutionResponse, NodeInfo, CreateWorkflowRequest,
    UpdateWorkflowRequest
)
from agent.flowgent_agent import chat_with_agent
from n8n_mcp.n8n_client import get_mcp_client
from n8n_mcp.direct_client import create_n8n_client

logger = logging.getLogger(__name__)
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
        logger.info(f"Chat message received: {message.message[:50]}...")
        session_id = "default_session"
        if message.context and "session_id" in message.context:
            session_id = message.context["session_id"]
        
        # Store n8n config in context for agent to use
        context = message.context or {}
        if message.n8n_config:
            context["n8n_instance_url"] = message.n8n_config.instance_url
            context["n8n_api_key"] = message.n8n_config.api_key
            logger.info(f"n8n config provided: {message.n8n_config.instance_url}")
            
        response_text = await chat_with_agent(message.message, session_id)
        logger.info(f"Chat response generated: {len(response_text)} chars")
        return ChatResponse(response=response_text, workflow_data=None, action=None)
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return ChatResponse(response=f"I apologize, but I encountered an error: {str(e)}. Please try again or rephrase your question.")


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
            logger.info("Using direct n8n client for list_workflows")
            workflows = await direct_client.list_workflows()
        else:
            # Fall back to MCP
            logger.info("Using MCP client for list_workflows")
            client = get_mcp_client()
            workflows = await client.list_workflows()
        
        if not workflows:
            logger.warning("No workflows returned from n8n")
            return []
        
        logger.info(f"Retrieved {len(workflows)} workflows")
        return [
            WorkflowListItem(
                id=str(w.get("id", "")),
                name=w.get("name", "Untitled"),
                active=w.get("active", False),
                createdAt=w.get("createdAt"),
                updatedAt=w.get("updatedAt")
            ) for w in workflows
        ]
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}", exc_info=True)
        if "401" in str(e) or "403" in str(e):
            raise HTTPException(status_code=401, detail="Authentication failed with n8n. Check your API key.")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve workflows: {str(e)}")


@router.get("/workflows/{workflow_id}", response_model=Workflow)
async def get_workflow(
    workflow_id: str,
    x_n8n_instance_url: Optional[str] = Header(None, alias="X-N8N-Instance-URL"),
    x_n8n_api_key: Optional[str] = Header(None, alias="X-N8N-API-Key")
):
    """Get a specific workflow by ID."""
    try:
        logger.info(f"Getting workflow: {workflow_id}")
        direct_client = get_n8n_client_from_headers(x_n8n_instance_url, x_n8n_api_key)
        if direct_client:
            logger.info("Using direct n8n client for get_workflow")
            workflow = await direct_client.get_workflow(workflow_id)
        else:
            logger.info("Using MCP client for get_workflow")
            client = get_mcp_client()
            workflow = await client.get_workflow(workflow_id)
        
        if not workflow:
            logger.warning(f"Workflow {workflow_id} not found")
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        
        return Workflow(
            id=str(workflow.get("id", workflow_id)),
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
        logger.error(f"Failed to get workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve workflow: {str(e)}")


@router.post("/workflows", response_model=Workflow)
async def create_workflow(req: CreateWorkflowRequest):
    """Create a new workflow in n8n."""
    try:
        logger.info(f"Creating workflow: {req.name}")
        # Use direct client if n8n config provided
        if req.n8n_config and req.n8n_config.instance_url and req.n8n_config.api_key:
            logger.info("Using direct n8n client for create_workflow")
            direct_client = create_n8n_client(req.n8n_config.instance_url, req.n8n_config.api_key)
            result = await direct_client.create_workflow(req.name, req.nodes, req.connections)
        else:
            # Fall back to MCP
            logger.info("Using MCP client for create_workflow")
            client = get_mcp_client()
            result = await client.create_workflow(req.name, req.nodes, req.connections)
        
        logger.info(f"Workflow created successfully: {result.get('id')}")
        return Workflow(
            id=str(result.get("id", "")),
            name=result.get("name", req.name),
            active=result.get("active", False),
            nodes=result.get("nodes", req.nodes),
            connections=result.get("connections", req.connections),
            createdAt=result.get("createdAt"),
            updatedAt=result.get("updatedAt")
        )
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


@router.put("/workflows/{workflow_id}", response_model=Workflow)
async def update_workflow(workflow_id: str, req: UpdateWorkflowRequest):
    """Update an existing workflow in n8n."""
    try:
        logger.info(f"Updating workflow: {workflow_id}")
        
        # Prepare updates dict
        updates = {}
        if req.name is not None:
            updates["name"] = req.name
        if req.nodes is not None:
            updates["nodes"] = req.nodes
        if req.connections is not None:
            updates["connections"] = req.connections
        if req.active is not None:
            updates["active"] = req.active
        
        # Use direct client if n8n config provided
        if req.n8n_config and req.n8n_config.instance_url and req.n8n_config.api_key:
            logger.info("Using direct n8n client for update_workflow")
            direct_client = create_n8n_client(req.n8n_config.instance_url, req.n8n_config.api_key)
            result = await direct_client.update_workflow(workflow_id, updates)
        else:
            # Fall back to MCP
            logger.info("Using MCP client for update_workflow")
            client = get_mcp_client()
            result = await client.update_workflow(workflow_id, updates)
        
        logger.info(f"Workflow updated successfully: {workflow_id}")
        return Workflow(
            id=str(result.get("id", workflow_id)),
            name=result.get("name", req.name or "Untitled"),
            active=result.get("active", False),
            nodes=result.get("nodes", req.nodes or []),
            connections=result.get("connections", req.connections or {}),
            createdAt=result.get("createdAt"),
            updatedAt=result.get("updatedAt")
        )
    except Exception as e:
        logger.error(f"Failed to update workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update workflow: {str(e)}")


@router.post("/execute", response_model=ExecutionResponse)
async def execute_workflow(req: ExecutionRequest):
    """Execute a workflow with optional input data."""
    try:
        logger.info(f"Executing workflow: {req.workflow_id}")
        if req.n8n_config and req.n8n_config.instance_url and req.n8n_config.api_key:
            logger.info("Using direct n8n client for execute_workflow")
            direct_client = create_n8n_client(req.n8n_config.instance_url, req.n8n_config.api_key)
            result = await direct_client.execute_workflow(req.workflow_id, req.input_data)
        else:
            logger.info("Using MCP client for execute_workflow")
            client = get_mcp_client()
            result = await client.execute_workflow(req.workflow_id, req.input_data)
        
        logger.info(f"Workflow executed: {result.get('id', 'unknown')}")
        return ExecutionResponse(
            execution_id=str(result.get("id", "unknown")),
            success=result.get("finished", True) and not result.get("error"),
            data=result.get("data"),
            error=result.get("error"),
            started_at=result.get("startedAt"),
            finished_at=result.get("finishedAt")
        )
    except Exception as e:
        logger.error(f"Failed to execute workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")


@router.get("/node-info/{node_type:path}", response_model=NodeInfo)
async def get_node_info(node_type: str):
    """Get detailed information about an n8n node type."""
    try:
        logger.info(f"Getting node info for: {node_type}")
        client = get_mcp_client()
        info = await client.get_node_info(node_type)
        
        if info:
            logger.info(f"Successfully retrieved node info for {node_type}")
            # Parse MCP response - handle different response formats
            if isinstance(info, dict):
                description = info.get("description", info.get("text", ""))
                display_name = info.get("displayName", info.get("name", node_type.split(".")[-1]))
                use_cases = info.get("use_cases", info.get("useCases", []))
                best_practices = info.get("best_practices", info.get("bestPractices", []))
            else:
                description = str(info)
                display_name = node_type.split(".")[-1]
                use_cases = []
                best_practices = []
            
            return NodeInfo(
                node_type=node_type,
                display_name=display_name,
                description=description,
                parameters=[],
                use_cases=use_cases if isinstance(use_cases, list) else [],
                best_practices=best_practices if isinstance(best_practices, list) else [],
                example_config=None
            )
        
        logger.warning(f"No MCP info for {node_type}, falling back to AI")
        # Fall back to AI-generated info
        response = await chat_with_agent(
            f"Provide a brief description and 2-3 use cases for the n8n node type: {node_type}. Be concise.",
            session_id="node_info_session"
        )
        
        return NodeInfo(
            node_type=node_type,
            display_name=node_type.split(".")[-1].replace("-", " ").title(),
            description=response,
            parameters=[],
            use_cases=[],
            best_practices=[],
            example_config=None
        )
    except Exception as e:
        logger.error(f"Failed to get node info for {node_type}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve node info: {str(e)}")


@router.get("/executions")
async def list_executions(
    workflow_id: Optional[str] = Query(None),
    x_n8n_instance_url: Optional[str] = Header(None, alias="X-N8N-Instance-URL"),
    x_n8n_api_key: Optional[str] = Header(None, alias="X-N8N-API-Key")
):
    """Get execution history."""
    try:
        logger.info(f"Listing executions{f' for workflow {workflow_id}' if workflow_id else ''}")
        direct_client = get_n8n_client_from_headers(x_n8n_instance_url, x_n8n_api_key)
        if direct_client:
            logger.info("Using direct n8n client for list_executions")
            executions = await direct_client.list_executions(workflow_id)
        else:
            logger.info("Using MCP client for list_executions")
            client = get_mcp_client()
            executions = await client.list_executions(workflow_id)
        
        if not executions:
            logger.info("No executions found")
            return []
        
        logger.info(f"Retrieved {len(executions)} executions")
        return executions
    except Exception as e:
        logger.error(f"Failed to list executions: {e}", exc_info=True)
        if "401" in str(e) or "403" in str(e):
            raise HTTPException(status_code=401, detail="Authentication failed with n8n. Check your API key.")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve executions: {str(e)}")
