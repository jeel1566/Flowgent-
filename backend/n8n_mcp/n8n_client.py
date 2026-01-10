"""n8n MCP Client using HTTP POST-based MCP protocol (JSON-RPC)."""
import os
import json
import logging
from typing import Optional, Dict, List, Any
import httpx

logger = logging.getLogger(__name__)


class N8nMcpClient:
    """n8n MCP Client using HTTP POST JSON-RPC protocol."""
    
    def __init__(self):
        self.mcp_url = os.getenv("N8N_MCP_URL", "https://api.n8n-mcp.com/mcp")
        self.api_key = os.getenv("N8N_MCP_API_KEY", "")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        self._client: Optional[httpx.AsyncClient] = None
        self._request_id = 0
        self._initialized = False
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=self.headers,
                timeout=60.0,
                follow_redirects=True
            )
        return self._client
    
    def _next_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id

    async def _call_mcp(self, method: str, params: Dict = None) -> Any:
        """Make an MCP JSON-RPC call (handles SSE response format)."""
        client = self._get_client()
        
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {}
        }
        
        logger.info(f"MCP call: {method}")
        
        try:
            response = await client.post(self.mcp_url, json=payload)
            response.raise_for_status()
            
            # Parse SSE response format: "event: message\ndata: {...}\n"
            text = response.text.strip()
            result = None
            
            for line in text.split("\n"):
                line = line.strip()
                if line.startswith("data:"):
                    json_str = line[5:].strip()
                    if json_str:
                        result = json.loads(json_str)
                        break
            
            if result is None:
                # Try parsing as regular JSON
                result = response.json()
            
            if "error" in result:
                logger.error(f"MCP error: {result['error']}")
                raise Exception(result["error"].get("message", str(result["error"])))
            
            return result.get("result")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"MCP call failed: {e}")
            raise

    async def initialize(self) -> bool:
        """Initialize the MCP connection."""
        if self._initialized:
            return True
        try:
            result = await self._call_mcp("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "flowgent", "version": "2.0.0"}
            })
            self._initialized = True
            logger.info(f"MCP initialized: {result}")
            return True
        except Exception as e:
            logger.error(f"MCP initialization failed: {e}")
            return False

    async def check_connection(self) -> bool:
        """Check if MCP server is reachable."""
        try:
            return await self.initialize()
        except Exception:
            return False

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools."""
        try:
            if not self._initialized:
                await self.initialize()
            result = await self._call_mcp("tools/list", {})
            return result.get("tools", []) if result else []
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call an MCP tool."""
        try:
            if not self._initialized:
                await self.initialize()
            
            result = await self._call_mcp("tools/call", {
                "name": tool_name,
                "arguments": arguments or {}
            })
            
            # Parse content from result
            if result and "content" in result:
                contents = []
                for item in result["content"]:
                    if isinstance(item, dict) and "text" in item:
                        contents.append(item["text"])
                if contents:
                    try:
                        return json.loads(contents[0])
                    except json.JSONDecodeError:
                        return {"text": "\n".join(contents)}
            return result
        except Exception as e:
            logger.error(f"Tool call failed ({tool_name}): {e}")
            raise

    # ========== MCP Tool Wrappers ==========

    async def search_nodes(self, query: str, source: str = None) -> Dict[str, Any]:
        """Search n8n nodes using MCP."""
        args = {"query": query}
        if source:
            args["source"] = source
        return await self.call_tool("search_nodes", args)

    async def get_node(self, node_type: str, mode: str = "docs") -> Dict[str, Any]:
        """Get node information using MCP."""
        return await self.call_tool("get_node", {
            "nodeType": node_type,
            "mode": mode
        })

    async def validate_workflow(self, workflow: Dict) -> Dict[str, Any]:
        """Validate a workflow using MCP."""
        return await self.call_tool("validate_workflow", {"workflow": workflow})

    async def search_templates(self, query: str = None, search_mode: str = "keyword") -> Dict[str, Any]:
        """Search workflow templates using MCP."""
        args = {"searchMode": search_mode}
        if query:
            args["query"] = query
        return await self.call_tool("search_templates", args)

    async def get_template(self, template_id: str, mode: str = "full") -> Dict[str, Any]:
        """Get a workflow template using MCP."""
        return await self.call_tool("get_template", {
            "templateId": template_id,
            "mode": mode
        })

    # ========== Legacy Methods (For Compatibility) ==========
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List workflows - requires n8n API configuration in MCP."""
        try:
            result = await self.call_tool("n8n_list_workflows", {})
            if isinstance(result, dict) and "workflows" in result:
                return result["workflows"]
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.warning(f"list_workflows failed: {e}")
            return []

    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by ID - requires n8n API configuration."""
        try:
            return await self.call_tool("n8n_get_workflow", {"workflowId": workflow_id})
        except Exception:
            return None

    async def create_workflow(self, name: str, nodes: List[Dict], connections: Dict) -> Dict[str, Any]:
        """Create workflow - requires n8n API configuration."""
        return await self.call_tool("n8n_create_workflow", {
            "name": name,
            "nodes": nodes,
            "connections": connections
        })

    async def execute_workflow(self, workflow_id: str, input_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute workflow - requires n8n API configuration."""
        args = {"workflowId": workflow_id}
        if input_data:
            args["data"] = input_data
        return await self.call_tool("n8n_test_workflow", args)

    async def get_node_info(self, node_type: str) -> Optional[Dict[str, Any]]:
        """Get node info using MCP get_node tool."""
        try:
            return await self.get_node(node_type, mode="docs")
        except Exception:
            return None

    async def list_executions(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List executions - requires n8n API configuration."""
        try:
            args = {"action": "list"}
            if workflow_id:
                args["workflowId"] = workflow_id
            result = await self.call_tool("n8n_executions", args)
            return result if isinstance(result, list) else []
        except Exception:
            return []

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()


# Singleton instance
_client: Optional[N8nMcpClient] = None


def get_mcp_client() -> N8nMcpClient:
    """Get singleton MCP client instance."""
    global _client
    if _client is None:
        _client = N8nMcpClient()
    return _client
