from fastapi import APIRouter, HTTPException, Query, Header
from typing import List, Optional, Dict
import logging
from models.schemas import (
    ChatMessage, ChatResponse, WorkflowListItem, Workflow,
    ExecutionRequest, ExecutionResponse, NodeInfo, CreateWorkflowRequest,
    UpdateWorkflowRequest
)
from agent.flowgent_agent import chat_with_agent
from agent.context import set_n8n_credentials, clear_n8n_credentials
from n8n_mcp.n8n_client import get_mcp_client, N8nMcpClient
from n8n_mcp.direct_client import create_n8n_client

logger = logging.getLogger(__name__)

# Cache for node info to improve performance and reduce API/LLM calls
NODE_INFO_CACHE: Dict[str, NodeInfo] = {
    "n8n-nodes-base.manualTrigger": NodeInfo(
        node_type="n8n-nodes-base.manualTrigger",
        display_name="Manual Trigger",
        description="Starts a workflow manually from the n8n interface.",
        parameters=[], use_cases=["Testing workflows", "On-demand execution"], best_practices=[], example_config=None
    ),
    "n8n-nodes-base.httpRequest": NodeInfo(
        node_type="n8n-nodes-base.httpRequest",
        display_name="HTTP Request",
        description="Makes an HTTP request to an API or website.",
        parameters=[], use_cases=["Fetching data from APIs", "Sending webhooks"], best_practices=["Use authentication"], example_config=None
    ),
    "n8n-nodes-base.set": NodeInfo(
        node_type="n8n-nodes-base.set",
        display_name="Set",
        description="Sets values on items and removes other values.",
        parameters=[], use_cases=["Creating variables", "Mocking data"], best_practices=[], example_config=None
    )
}
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
        
        # Set n8n credentials in agent context for this request
        if message.n8n_config and message.n8n_config.instance_url and message.n8n_config.api_key:
            set_n8n_credentials(
                instance_url=message.n8n_config.instance_url,
                api_key=message.n8n_config.api_key
            )
            logger.info(f"n8n credentials set for agent: {message.n8n_config.instance_url}")
        
        try:
            response_text = await chat_with_agent(message.message, session_id)
            logger.info(f"Chat response generated: {len(response_text)} chars")
            return ChatResponse(response=response_text, workflow_data=None, action=None)
        finally:
            # Clear credentials after request
            clear_n8n_credentials()
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


@router.get("/node-info/{node_type:path}")
async def get_node_info(node_type: str):
    """Get fast node information for Information Hand tooltip using MCP."""
    try:
        # Check cache first for speed
        if node_type in NODE_INFO_CACHE:
            logger.info(f"Using cached info for: {node_type}")
            return NODE_INFO_CACHE[node_type]

        logger.info(f"Getting fast node info for: {node_type}")
        
        # Use MCP client directly for speed (not slow chat)
        client = get_mcp_client()
        info = await client.get_node_info(node_type)
        
        if info:
            logger.info(f"Successfully retrieved MCP node info for {node_type}")
            
            # Parse and format the response for tooltip
            if isinstance(info, dict):
                # Extract basic info
                display_name = info.get("displayName", info.get("name", node_type.split(".")[-1]))
                description = info.get("description", info.get("text", info.get("summary", "")))
                
                # Generate "how it works" and "what it does" from available data
                how_it_works = ""
                what_it_does = ""
                
                # Try to extract meaningful content from various fields
                if "properties" in info:
                    # Use parameter descriptions to understand functionality
                    params = info["properties"]
                    if params:
                        how_it_works = f"Operates with {len(params)} parameters including {', '.join(list(params.keys())[:3])}"
                
                if "inputs" in info:
                    inputs = info["inputs"]
                    if isinstance(inputs, list) and inputs:
                        how_it_works += f", processes {len(inputs)} input types"
                
                # Default descriptions if we can't extract meaningful content
                if not how_it_works:
                    how_it_works = f"Processes data according to its configuration and parameters"
                
                if not what_it_does:
                    what_it_does = f"Performs {display_name.lower()} operations within automation workflows"
                
                # Format response for tooltip
                result = {
                    "name": display_name,
                    "description": description[:100] if description else f"Node for {display_name.lower()} operations",
                    "howItWorks": how_it_works[:200] if how_it_works else f"Configurable {display_name.lower()} node",
                    "whatItDoes": what_it_does[:200] if what_it_does else f"Executes {display_name.lower()} tasks in workflows",
                    "nodeType": node_type,
                    "icon": info.get("icon", "")
                }
            else:
                # Fallback for non-dict responses
                result = {
                    "name": node_type.split(".")[-1].replace("-", " ").title(),
                    "description": str(info)[:100],
                    "howItWorks": f"Performs {node_type.split('.')[-1].replace('-', ' ')} operations",
                    "whatItDoes": f"Executes {node_type.split('.')[-1].replace('-', ' ')} tasks in workflows",
                    "nodeType": node_type,
                    "icon": ""
                }
        else:
            logger.warning(f"No MCP info for {node_type}, using fallback")
            # Fast fallback without slow AI call
            result = {
                "name": node_type.split(".")[-1].replace("-", " ").title(),
                "description": f"Node for {node_type.split('.')[-1].replace('-', ' ').lower()} operations",
                "howItWorks": f"Configurable {node_type.split('.')[-1].replace('-', ' ').lower()} node for workflow automation",
                "whatItDoes": f"Executes {node_type.split('.')[-1].replace('-', ' ').lower()} tasks within automation workflows",
                "nodeType": node_type,
                "icon": ""
            }
        
        # Cache the result for future fast access
        NODE_INFO_CACHE[node_type] = result
        logger.info(f"Cached node info for: {node_type}")
        return result
            
    except Exception as e:
        logger.error(f"Failed to get node info for {node_type}: {e}", exc_info=True)
        # Return fast fallback instead of error
        return {
            "name": node_type.split(".")[-1].replace("-", " ").title(),
            "description": f"Node for {node_type.split('.')[-1].replace('-', ' ').lower()} operations",
            "howItWorks": f"Configurable {node_type.split('.')[-1].replace('-', ' ').lower()} node",
            "whatItDoes": f"Executes {node_type.split('.')[-1].replace('-', ' ').lower()} tasks in workflows",
            "nodeType": node_type,
            "icon": ""
        }


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
