"""MCP client wrapper for n8n integration."""
import os
from typing import Optional, List, Dict, Any
import httpx


class N8nMCPClient:
    """Client for interacting with n8n via MCP server."""
    
    def __init__(self, mcp_server_url: Optional[str] = None):
        """Initialize MCP client.
        
        Args:
            mcp_server_url: URL of the MCP server. If None, reads from env.
        """
        self.mcp_server_url = mcp_server_url or os.getenv("N8N_MCP_SERVER_URL", "http://localhost:3000")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Tool execution result
        """
        try:
            response = await self.client.post(
                f"{self.mcp_server_url}/mcp",
                json={"tool": tool_name, "arguments": arguments}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows from n8n."""
        result = await self.call_tool("list_workflows", {})
        return result.get("data", []) if result.get("success") else []
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific workflow by ID.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Workflow data or None if not found
        """
        result = await self.call_tool("get_workflow", {"workflow_id": workflow_id})
        return result.get("data") if result.get("success") else None
    
    async def create_workflow(self, name: str, nodes: List[Dict], connections: Dict) -> Dict[str, Any]:
        """Create a new workflow.
        
        Args:
            name: Workflow name
            nodes: List of workflow nodes
            connections: Node connections
            
        Returns:
            Created workflow data
        """
        return await self.call_tool("create_workflow", {
            "name": name,
            "nodes": nodes,
            "connections": connections
        })
    
    async def update_workflow(self, workflow_id: str, **updates) -> Dict[str, Any]:
        """Update an existing workflow.
        
        Args:
            workflow_id: ID of workflow to update
            **updates: Fields to update (name, nodes, connections, etc.)
            
        Returns:
            Updated workflow data
        """
        return await self.call_tool("update_workflow", {
            "workflow_id": workflow_id,
            **updates
        })
    
    async def execute_workflow(self, workflow_id: str, input_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a workflow.
        
        Args:
            workflow_id: ID of workflow to execute
            input_data: Optional input data for the workflow
            
        Returns:
            Execution result
        """
        return await self.call_tool("execute_workflow", {
            "workflow_id": workflow_id,
            "input_data": input_data or {}
        })
    
    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution details by ID.
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            Execution data or None
        """
        result = await self.call_tool("get_execution", {"execution_id": execution_id})
        return result.get("data") if result.get("success") else None
    
    async def list_executions(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List executions, optionally filtered by workflow.
        
        Args:
            workflow_id: Optional workflow ID to filter by
            
        Returns:
            List of executions
        """
        args = {"workflow_id": workflow_id} if workflow_id else {}
        result = await self.call_tool("list_executions", args)
        return result.get("data", []) if result.get("success") else []
    
    async def get_node_types(self) -> List[Dict[str, Any]]:
        """Get all available node types."""
        result = await self.call_tool("get_node_types", {})
        return result.get("data", []) if result.get("success") else []
    
    async def get_node_info(self, node_type: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a node type.
        
        Args:
            node_type: Type of node to get info for
            
        Returns:
            Node information or None
        """
        result = await self.call_tool("get_node_info", {"node_type": node_type})
        return result.get("data") if result.get("success") else None
    
    async def check_connection(self) -> bool:
        """Check if MCP server is accessible.
        
        Returns:
            True if connected, False otherwise
        """
        try:
            response = await self.client.get(f"{self.mcp_server_url}/health")
            return response.status_code == 200
        except:
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global MCP client instance
_mcp_client: Optional[N8nMCPClient] = None


def get_mcp_client() -> N8nMCPClient:
    """Get or create the global MCP client instance."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = N8nMCPClient()
    return _mcp_client
