"""API routes for Flowgent backend."""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from models.schemas import (
    ChatMessage, ChatResponse, WorkflowListItem, Workflow,
    ExecutionRequest, ExecutionResponse, NodeInfo
)
from agent.flowgent_agent import get_agent
from mcp.n8n_client import get_mcp_client

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Chat with the AI assistant.
    
    Args:
        message: Chat message from user
        
    Returns:
        AI assistant response
    """
    try:
        agent = get_agent()
        result = await agent.chat(
            message=message.message,
            context=message.context
        )
        
        return ChatResponse(
            response=result.get("response", ""),
            workflow_data=result.get("function_result") if result.get("function_called") == "create_workflow" else None,
            action=result.get("function_called")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows", response_model=List[WorkflowListItem])
async def list_workflows():
    """Get all workflows from n8n.
    
    Returns:
        List of workflows
    """
    try:
        mcp_client = get_mcp_client()
        workflows = await mcp_client.list_workflows()
        
        # Convert to response model
        return [
            WorkflowListItem(
                id=w.get("id", ""),
                name=w.get("name", "Untitled"),
                active=w.get("active", False),
                created_at=w.get("createdAt"),
                updated_at=w.get("updatedAt")
            )
            for w in workflows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}", response_model=Workflow)
async def get_workflow(workflow_id: str):
    """Get a specific workflow by ID.
    
    Args:
        workflow_id: ID of the workflow
        
    Returns:
        Workflow details
    """
    try:
        mcp_client = get_mcp_client()
        workflow = await mcp_client.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return Workflow(
            id=workflow.get("id"),
            name=workflow.get("name", "Untitled"),
            active=workflow.get("active", False),
            nodes=workflow.get("nodes", []),
            connections=workflow.get("connections", {}),
            created_at=workflow.get("createdAt"),
            updated_at=workflow.get("updatedAt")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=ExecutionResponse)
async def execute_workflow(request: ExecutionRequest):
    """Execute a workflow with optional input data.
    
    Args:
        request: Execution request with workflow ID and input data
        
    Returns:
        Execution result
    """
    try:
        mcp_client = get_mcp_client()
        result = await mcp_client.execute_workflow(
            request.workflow_id,
            request.input_data
        )
        
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


@router.get("/node-info/{node_type}", response_model=NodeInfo)
async def get_node_info(node_type: str):
    """Get detailed information about a node type.
    
    Args:
        node_type: Type of node (e.g., 'n8n-nodes-base.httpRequest')
        
    Returns:
        Node information including description, parameters, and examples
    """
    try:
        mcp_client = get_mcp_client()
        node_info = await mcp_client.get_node_info(node_type)
        
        if not node_info:
            # If MCP doesn't have info, ask AI to generate it
            agent = get_agent()
            ai_response = await agent.chat(
                f"Provide detailed information about the n8n node type: {node_type}. Include description, common use cases, and best practices."
            )
            
            return NodeInfo(
                node_type=node_type,
                display_name=node_type.split(".")[-1],
                description=ai_response.get("response", ""),
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
    """Get execution history.
    
    Args:
        workflow_id: Optional workflow ID to filter by
        
    Returns:
        List of executions
    """
    try:
        mcp_client = get_mcp_client()
        executions = await mcp_client.list_executions(workflow_id)
        return executions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
