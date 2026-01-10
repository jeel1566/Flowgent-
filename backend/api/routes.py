from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from models.schemas import (
    ChatMessage, ChatResponse, WorkflowListItem, Workflow,
    ExecutionRequest, ExecutionResponse, NodeInfo
)
from agent.flowgent_agent import chat_with_agent
from n8n_mcp.n8n_client import get_mcp_client

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Chat with the Flowgent AI assistant."""
    try:
        session_id = "default_session"
        if message.context and "session_id" in message.context:
            session_id = message.context["session_id"]
            
        response_text = await chat_with_agent(message.message, session_id)
        return ChatResponse(response=response_text, workflow_data=None, action=None)
    except Exception as e:
        return ChatResponse(response=f"Error: {str(e)}")


@router.get("/workflows", response_model=List[WorkflowListItem])
async def list_workflows():
    """Get all workflows from n8n."""
    try:
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
async def get_workflow(workflow_id: str):
    """Get a specific workflow by ID."""
    try:
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


@router.post("/execute", response_model=ExecutionResponse)
async def execute_workflow(req: ExecutionRequest):
    """Execute a workflow with optional input data."""
    try:
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
    """Get detailed information about a node type."""
    try:
        client = get_mcp_client()
        node_info = await client.get_node_info(node_type)
        
        if not node_info:
            # Use AI to generate info if MCP doesn't have it
            ai_response = await chat_with_agent(
                f"Provide brief info about the n8n node type: {node_type}. Include description and common use cases.",
                session_id="node_info_session"
            )
            return NodeInfo(
                node_type=node_type,
                display_name=node_type.split(".")[-1] if "." in node_type else node_type,
                description=ai_response,
                parameters=[],
                use_cases=[],
                best_practices=[]
            )
        
        return NodeInfo(
            node_type=node_type,
            display_name=node_info.get("displayName", node_type),
            description=node_info.get("description", ""),
            parameters=node_info.get("properties", []),
            use_cases=node_info.get("useCases", []),
            best_practices=node_info.get("bestPractices", []),
            example_config=node_info.get("exampleConfig")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions")
async def list_executions(workflow_id: Optional[str] = Query(None)):
    """Get execution history, optionally filtered by workflow."""
    try:
        client = get_mcp_client()
        executions = await client.list_executions(workflow_id)
        return executions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
