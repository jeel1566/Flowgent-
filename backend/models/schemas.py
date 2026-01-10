"""Pydantic models for request/response validation."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    """Chat message from user."""
    message: str = Field(..., description="User's message to the AI assistant")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context like current workflow")


class ChatResponse(BaseModel):
    """Response from AI assistant."""
    response: str = Field(..., description="AI assistant's response")
    workflow_data: Optional[Dict[str, Any]] = Field(None, description="Generated workflow JSON if applicable")
    action: Optional[str] = Field(None, description="Suggested action: create, modify, execute")


class Workflow(BaseModel):
    """n8n workflow data."""
    id: Optional[str] = None
    name: str
    active: bool = False
    nodes: List[Dict[str, Any]] = []
    connections: Dict[str, Any] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WorkflowListItem(BaseModel):
    """Simplified workflow list item."""
    id: str
    name: str
    active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ExecutionRequest(BaseModel):
    """Request to execute a workflow."""
    workflow_id: str = Field(..., description="ID of workflow to execute")
    input_data: Optional[Dict[str, Any]] = Field(None, description="Test input data for workflow")


class ExecutionResponse(BaseModel):
    """Workflow execution result."""
    execution_id: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class NodeInfo(BaseModel):
    """Information about an n8n node type."""
    node_type: str
    display_name: str
    description: str
    parameters: List[Dict[str, Any]] = []
    use_cases: List[str] = []
    best_practices: List[str] = []
    example_config: Optional[Dict[str, Any]] = None


class HealthCheck(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    mcp_connected: bool = False
