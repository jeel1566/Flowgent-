from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class N8nConfig(BaseModel):
    """n8n instance configuration from frontend."""
    instance_url: Optional[str] = None
    api_key: Optional[str] = None


class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    n8n_config: Optional[N8nConfig] = None


class ChatResponse(BaseModel):
    response: str
    workflow_data: Optional[Dict[str, Any]] = None
    action: Optional[str] = None


class WorkflowListItem(BaseModel):
    id: str
    name: str
    active: bool
    created_at: Optional[str] = Field(None, alias="createdAt")
    updated_at: Optional[str] = Field(None, alias="updatedAt")
    
    class Config:
        populate_by_name = True


class Workflow(BaseModel):
    id: Optional[str] = None
    name: str
    active: bool = False
    nodes: List[Dict[str, Any]] = []
    connections: Dict[str, Any] = {}
    created_at: Optional[str] = Field(None, alias="createdAt")
    updated_at: Optional[str] = Field(None, alias="updatedAt")
    
    class Config:
        populate_by_name = True


class CreateWorkflowRequest(BaseModel):
    """Request to create a workflow."""
    name: str
    nodes: List[Dict[str, Any]] = []
    connections: Dict[str, Any] = {}
    n8n_config: Optional[N8nConfig] = None


class UpdateWorkflowRequest(BaseModel):
    """Request to update an existing workflow."""
    workflow_id: str
    name: Optional[str] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    connections: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None
    n8n_config: Optional[N8nConfig] = None


class ExecutionRequest(BaseModel):
    workflow_id: str
    input_data: Optional[Dict[str, Any]] = None
    n8n_config: Optional[N8nConfig] = None


class ExecutionResponse(BaseModel):
    execution_id: str
    success: bool
    data: Optional[Any] = None
    error: Optional[Any] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


class NodeInfo(BaseModel):
    node_type: str
    display_name: str
    description: str
    parameters: List[Dict[str, Any]] = []
    use_cases: List[str] = []
    best_practices: List[str] = []
    example_config: Optional[Dict[str, Any]] = None


class HealthCheck(BaseModel):
    status: str
    version: str
    mcp_connected: bool
