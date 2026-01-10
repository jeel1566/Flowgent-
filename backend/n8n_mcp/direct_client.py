"""Direct n8n API Client - uses user-provided credentials."""
import httpx
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class DirectN8nClient:
    """Client for direct n8n API calls using user-provided credentials."""
    
    def __init__(self, instance_url: str, api_key: str):
        self.instance_url = instance_url.rstrip('/')
        self.api_key = api_key
        self.base_url = f"{self.instance_url}/api/v1"
        self.headers = {
            "X-N8N-API-KEY": api_key,
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to n8n API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{self.base_url}{endpoint}"
            logger.debug(f"n8n API: {method} {url}")
            
            try:
                response = await client.request(
                    method, url, headers=self.headers, **kwargs
                )
                response.raise_for_status()
                result = response.json()
                logger.debug(f"n8n API response: {response.status_code}")
                return result
            except httpx.HTTPStatusError as e:
                logger.error(f"n8n API error {e.response.status_code}: {e.response.text[:200]}")
                raise
            except Exception as e:
                logger.error(f"n8n API request failed: {e}", exc_info=True)
                raise
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows."""
        result = await self._request("GET", "/workflows")
        return result.get("data", result) if isinstance(result, dict) else result
    
    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get a specific workflow."""
        return await self._request("GET", f"/workflows/{workflow_id}")
    
    async def create_workflow(self, name: str, nodes: List[Dict], connections: Dict) -> Dict[str, Any]:
        """Create a new workflow."""
        workflow_data = {
            "name": name,
            "nodes": nodes,
            "connections": connections,
            "active": False,
            "settings": {}
        }
        return await self._request("POST", "/workflows", json=workflow_data)
    
    async def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing workflow."""
        # Get current workflow first to merge updates
        current = await self.get_workflow(workflow_id)
        
        # Prepare update data - only include provided fields
        workflow_data = {}
        if "name" in updates and updates["name"] is not None:
            workflow_data["name"] = updates["name"]
        else:
            workflow_data["name"] = current.get("name", "Untitled")
        
        if "nodes" in updates and updates["nodes"] is not None:
            workflow_data["nodes"] = updates["nodes"]
        else:
            workflow_data["nodes"] = current.get("nodes", [])
        
        if "connections" in updates and updates["connections"] is not None:
            workflow_data["connections"] = updates["connections"]
        else:
            workflow_data["connections"] = current.get("connections", {})
        
        if "active" in updates and updates["active"] is not None:
            workflow_data["active"] = updates["active"]
        else:
            workflow_data["active"] = current.get("active", False)
        
        # Preserve other fields
        if "settings" in current:
            workflow_data["settings"] = current["settings"]
        
        logger.info(f"Updating workflow {workflow_id} with data: name={workflow_data.get('name')}, nodes={len(workflow_data.get('nodes', []))}")
        return await self._request("PUT", f"/workflows/{workflow_id}", json=workflow_data)
    
    async def execute_workflow(self, workflow_id: str, input_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a workflow."""
        # First get workflow to find trigger type
        workflow = await self.get_workflow(workflow_id)
        
        # Try webhook execution
        return await self._request(
            "POST", f"/workflows/{workflow_id}/run",
            json=input_data or {}
        )
    
    async def list_executions(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List execution history."""
        params = {}
        if workflow_id:
            params["workflowId"] = workflow_id
        result = await self._request("GET", "/executions", params=params)
        return result.get("data", result) if isinstance(result, dict) else result
    
    async def check_connection(self) -> bool:
        """Check if n8n API is accessible."""
        try:
            await self._request("GET", "/workflows", params={"limit": 1})
            return True
        except Exception as e:
            logger.error(f"n8n connection check failed: {e}")
            return False


def create_n8n_client(instance_url: str, api_key: str) -> Optional[DirectN8nClient]:
    """Create a direct n8n client if credentials are provided."""
    if instance_url and api_key:
        return DirectN8nClient(instance_url, api_key)
    return None
