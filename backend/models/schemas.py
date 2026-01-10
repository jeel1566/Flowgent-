from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

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

class Workflow(BaseModel):
    id: Optional[str] = None
    name: str
    active: bool = False
    nodes: List[Dict[str, Any]] = []
    connections: Dict[str, Any] = {}
    created_at: Optional[str] = Field(None, alias="createdAt")
    updated_at: Optional[str] = Field(None, alias="updatedAt")

class ExecutionRequest(BaseModel):
    workflow_id: str
    input_data: Optional[Dict[str, Any]] = None

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
