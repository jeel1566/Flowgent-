"""n8n MCP Client using HTTP POST-based MCP protocol with session management."""
import os
import json
import logging
from typing import Optional, Dict, List, Any
import httpx

logger = logging.getLogger(__name__)


class N8nMcpClient:
    """n8n MCP Client with proper session ID management."""
    
    def __init__(self):
        self.mcp_url = os.getenv("N8N_MCP_URL") or os.getenv("N8N_MCP_SERVER_URL") or "https://api.n8n-mcp.com/mcp"
        self.api_key = os.getenv("N8N_MCP_API_KEY", "")
        self._client: Optional[httpx.AsyncClient] = None
        self._request_id = 0
        self._initialized = False
        self._session_id: Optional[str] = None  # MCP session ID from server
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=60.0, follow_redirects=True)
        return self._client
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with session ID if available."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        return headers
    
    def _next_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id

    async def _call_mcp(self, method: str, params: Dict = None) -> Any:
        """Make an MCP JSON-RPC call with session management."""
        client = self._get_client()
        
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {}
        }
        
        logger.debug(f"MCP call: {method}")
        
        try:
            response = await client.post(
                self.mcp_url, 
                json=payload, 
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            # Extract session ID from response headers
            session_id = response.headers.get("Mcp-Session-Id") or response.headers.get("mcp-session-id")
            if session_id:
                self._session_id = session_id
                logger.debug(f"Session ID updated: {session_id[:50]}...")
            
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
                result = json.loads(text) if text else {}
            
            if "error" in result:
                logger.error(f"MCP error: {result['error']}")
                raise Exception(result["error"].get("message", str(result["error"])))
            
            return result.get("result")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP {e.response.status_code}: {e.response.text[:200]}")
            raise
        except Exception as e:
            logger.error(f"MCP call failed: {e}")
            raise

    async def initialize(self) -> bool:
        """Initialize the MCP connection and get session ID."""
        if self._initialized and self._session_id:
            logger.debug("MCP already initialized")
            return True
        
        if not self.api_key:
            logger.warning("N8N_MCP_API_KEY not set - MCP features may not work")
            return False
            
        try:
            logger.info(f"Initializing MCP connection to {self.mcp_url}")
            result = await self._call_mcp("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "flowgent", "version": "2.0.0"}
            })
            self._initialized = True
            session_info = self._session_id[:30] if self._session_id else 'None'
            logger.info(f"MCP initialized successfully. Session: {session_info}...")
            return True
        except Exception as e:
            logger.error(f"MCP initialization failed: {e}", exc_info=True)
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
                logger.info(f"Initializing MCP before calling tool {tool_name}")
                initialized = await self.initialize()
                if not initialized:
                    raise Exception("MCP initialization failed - cannot call tools")
            
            logger.debug(f"Calling MCP tool: {tool_name} with args: {arguments}")
            result = await self._call_mcp("tools/call", {
                "name": tool_name,
                "arguments": arguments or {}
            })
            
            # Parse content from MCP response
            if result and "content" in result:
                contents = []
                for item in result["content"]:
                    if isinstance(item, dict) and "text" in item:
                        contents.append(item["text"])
                if contents:
                    try:
                        parsed = json.loads(contents[0])
                        logger.debug(f"Tool {tool_name} returned parsed JSON")
                        return parsed
                    except json.JSONDecodeError:
                        logger.debug(f"Tool {tool_name} returned text (not JSON)")
                        return {"text": "\n".join(contents)}
            
            logger.debug(f"Tool {tool_name} returned raw result")
            return result
        except Exception as e:
            logger.error(f"Tool call failed ({tool_name}): {e}", exc_info=True)
            raise

    # ========== Core MCP Tools ==========

    async def search_nodes(self, query: str, source: str = None, include_examples: bool = False) -> Dict[str, Any]:
        """Search n8n nodes."""
        args = {"query": query}
        if source:
            args["source"] = source
        if include_examples:
            args["includeExamples"] = True
        return await self.call_tool("search_nodes", args)

    async def get_node(self, node_type: str, mode: str = "docs", detail: str = "standard") -> Dict[str, Any]:
        """Get node information."""
        return await self.call_tool("get_node", {
            "nodeType": node_type,
            "mode": mode,
            "detail": detail
        })

    async def validate_workflow(self, workflow: Dict) -> Dict[str, Any]:
        """Validate a workflow."""
        return await self.call_tool("validate_workflow", {"workflow": workflow})

    async def search_templates(self, query: str = None, search_mode: str = "keyword") -> Dict[str, Any]:
        """Search workflow templates."""
        args = {"searchMode": search_mode}
        if query:
            args["query"] = query
        return await self.call_tool("search_templates", args)

    async def get_template(self, template_id: str, mode: str = "full") -> Dict[str, Any]:
        """Get a workflow template."""
        return await self.call_tool("get_template", {
            "templateId": template_id,
            "mode": mode
        })

    async def get_tools_documentation(self, tool_name: str = None) -> Dict[str, Any]:
        """Get documentation for MCP tools."""
        args = {}
        if tool_name:
            args["toolName"] = tool_name
        return await self.call_tool("tools_documentation", args)

    # ========== n8n Management Tools (Require n8n API) ==========

    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List workflows from n8n instance."""
        try:
            result = await self.call_tool("n8n_list_workflows", {})
            if isinstance(result, list):
                return result
            if isinstance(result, dict):
                # Try common keys
                for key in ["workflows", "data", "result"]:
                    if key in result and isinstance(result[key], list):
                        return result[key]
            return []
        except Exception as e:
            logger.warning(f"list_workflows failed: {e}")
            return []

    async def get_workflow(self, workflow_id: str, mode: str = "full") -> Optional[Dict[str, Any]]:
        """Get workflow by ID."""
        try:
            return await self.call_tool("n8n_get_workflow", {
                "workflowId": workflow_id,
                "mode": mode
            })
        except Exception:
            return None

    async def create_workflow(self, name: str, nodes: List[Dict], connections: Dict) -> Dict[str, Any]:
        """Create a new workflow."""
        return await self.call_tool("n8n_create_workflow", {
            "name": name,
            "nodes": nodes,
            "connections": connections
        })
    
    async def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing workflow."""
        # MCP tool for updating workflows
        tool_args = {"workflowId": workflow_id}
        
        # Add optional fields if provided
        if "name" in updates and updates["name"] is not None:
            tool_args["name"] = updates["name"]
        if "nodes" in updates and updates["nodes"] is not None:
            tool_args["nodes"] = updates["nodes"]
        if "connections" in updates and updates["connections"] is not None:
            tool_args["connections"] = updates["connections"]
        if "active" in updates and updates["active"] is not None:
            tool_args["active"] = updates["active"]
        
        return await self.call_tool("n8n_update_workflow", tool_args)

    async def execute_workflow(self, workflow_id: str, input_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute/test a workflow."""
        args = {"workflowId": workflow_id}
        if input_data:
            args["data"] = input_data
        return await self.call_tool("n8n_test_workflow", args)

    async def get_node_info(self, node_type: str) -> Optional[Dict[str, Any]]:
        """Get node info (wrapper for get_node)."""
        try:
            return await self.get_node(node_type, mode="docs")
        except Exception:
            return None

    async def list_executions(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List execution history."""
        try:
            args = {"action": "list"}
            if workflow_id:
                args["workflowId"] = workflow_id
            result = await self.call_tool("n8n_executions", args)
            
            if isinstance(result, list):
                return result
            if isinstance(result, dict):
                # Try common keys
                for key in ["executions", "data", "result"]:
                    if key in result and isinstance(result[key], list):
                        return result[key]
            return []
        except Exception as e:
            logger.warning(f"list_executions failed: {e}")
            return []

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()


# Singleton instance with lock for thread safety
_client: Optional[N8nMcpClient] = None


def get_mcp_client() -> N8nMcpClient:
    """Get singleton MCP client instance."""
    global _client
    if _client is None:
        _client = N8nMcpClient()
    return _client
