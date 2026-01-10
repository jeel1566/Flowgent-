"""Flowgent AI Agent implementation using Google Agent SDK."""
import os
from typing import Optional, Dict, Any, List
from google import genai
from google.genai.types import Tool, GenerateContentConfig, Content, Part

from agent.config import AGENT_CONFIG, SYSTEM_INSTRUCTION, get_gemini_api_key
from mcp.n8n_client import get_mcp_client


class FlowgentAgent:
    """AI Agent for n8n workflow assistance using Google Agent SDK."""
    
    def __init__(self):
        """Initialize the Flowgent agent."""
        self.api_key = get_gemini_api_key()
        self.client = genai.Client(api_key=self.api_key)
        self.mcp_client = get_mcp_client()
        self.sessions: Dict[str, Any] = {}  # Store chat sessions
        
    def _create_mcp_tools(self) -> List[Tool]:
        """Create MCP tools for the agent.
        
        Returns:
            List of Tool definitions for n8n operations
        """
        # For now, we'll define tools manually
        # In production, these would be dynamically loaded from MCP server
        tools = [
            Tool(
                function_declarations=[
                    {
                        "name": "list_workflows",
                        "description": "Get all workflows from the n8n instance",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                        }
                    },
                    {
                        "name": "get_workflow",
                        "description": "Get a specific workflow by ID with full details",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "workflow_id": {
                                    "type": "string",
                                    "description": "The ID of the workflow to retrieve"
                                }
                            },
                            "required": ["workflow_id"]
                        }
                    },
                    {
                        "name": "create_workflow",
                        "description": "Create a new n8n workflow from JSON definition",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the workflow"
                                },
                                "nodes": {
                                    "type": "array",
                                    "description": "Array of workflow nodes",
                                    "items": {"type": "object"}
                                },
                                "connections": {
                                    "type": "object",
                                    "description": "Node connections mapping"
                                }
                            },
                            "required": ["name", "nodes", "connections"]
                        }
                    },
                    {
                        "name": "execute_workflow",
                        "description": "Execute a workflow with optional input data",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "workflow_id": {
                                    "type": "string",
                                    "description": "ID of the workflow to execute"
                                },
                                "input_data": {
                                    "type": "object",
                                    "description": "Optional input data for the workflow"
                                }
                            },
                            "required": ["workflow_id"]
                        }
                    },
                    {
                        "name": "get_node_info",
                        "description": "Get detailed information about a specific n8n node type",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "node_type": {
                                    "type": "string",
                                    "description": "The type of node (e.g., 'n8n-nodes-base.httpRequest')"
                                }
                            },
                            "required": ["node_type"]
                        }
                    }
                ]
            )
        ]
        return tools
    
    async def _execute_tool_call(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool call via MCP.
        
        Args:
            function_name: Name of the function to call
            arguments: Function arguments
            
        Returns:
            Tool execution result
        """
        # Map function calls to MCP client methods
        if function_name == "list_workflows":
            return await self.mcp_client.list_workflows()
        elif function_name == "get_workflow":
            return await self.mcp_client.get_workflow(arguments["workflow_id"])
        elif function_name == "create_workflow":
            return await self.mcp_client.create_workflow(
                arguments["name"],
                arguments["nodes"],
                arguments["connections"]
            )
        elif function_name == "execute_workflow":
            return await self.mcp_client.execute_workflow(
                arguments["workflow_id"],
                arguments.get("input_data")
            )
        elif function_name == "get_node_info":
            return await self.mcp_client.get_node_info(arguments["node_type"])
        else:
            return {"error": f"Unknown function: {function_name}"}
    
    async def chat(self, message: str, session_id: Optional[str] = None, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Chat with the agent.
        
        Args:
            message: User's message
            session_id: Optional session ID for conversation continuity
            context: Optional context (e.g., current workflow data)
            
        Returns:
            Agent response with message and optional workflow data
        """
        try:
            # Prepare tools
            tools = self._create_mcp_tools()
            
            # Create config
            config = GenerateContentConfig(
                temperature=AGENT_CONFIG["temperature"],
                top_p=AGENT_CONFIG["top_p"],
                top_k=AGENT_CONFIG["top_k"],
                max_output_tokens=AGENT_CONFIG["max_output_tokens"],
                system_instruction=SYSTEM_INSTRUCTION,
                tools=tools
            )
            
            # Add context to message if provided
            full_message = message
            if context:
                full_message = f"Context: {context}\n\nUser message: {message}"
            
            # Generate response
            response = await self.client.aio.models.generate_content(
                model=AGENT_CONFIG["model"],
                contents=full_message,
                config=config
            )
            
            # Handle function calls if present
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        # Execute the function call
                        function_result = await self._execute_tool_call(
                            part.function_call.name,
                            dict(part.function_call.args)
                        )
                        
                        # Send result back to model for final response
                        follow_up = await self.client.aio.models.generate_content(
                            model=AGENT_CONFIG["model"],
                            contents=[
                                Content(parts=[Part(text=full_message)]),
                                Content(parts=[part]),
                                Content(parts=[Part(function_response={
                                    "name": part.function_call.name,
                                    "response": function_result
                                })])
                            ],
                            config=config
                        )
                        
                        return {
                            "response": follow_up.text,
                            "function_called": part.function_call.name,
                            "function_result": function_result
                        }
            
            return {
                "response": response.text,
                "function_called": None
            }
            
        except Exception as e:
            return {
                "response": f"I encountered an error: {str(e)}",
                "error": str(e)
            }
    
    async def generate_workflow(self, description: str) -> Dict[str, Any]:
        """Generate a workflow from natural language description.
        
        Args:
            description: Natural language description of desired workflow
            
        Returns:
            Workflow JSON and creation result
        """
        prompt = f"""Create an n8n workflow based on this description: {description}

Generate a complete, valid n8n workflow JSON with:
1. All necessary nodes configured properly
2. Correct connections between nodes
3. Appropriate error handling nodes
4. Best practices applied

Return the workflow in this format:
{{
    "name": "Workflow Name",
    "nodes": [...],
    "connections": {{...}}
}}"""
        
        response = await self.chat(prompt)
        return response


# Global agent instance
_agent: Optional[FlowgentAgent] = None


def get_agent() -> FlowgentAgent:
    """Get or create the global agent instance."""
    global _agent
    if _agent is None:
        _agent = FlowgentAgent()
    return _agent
