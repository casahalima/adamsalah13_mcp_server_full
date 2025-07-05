#!/usr/bin/env python3
"""
Pure Agentic MCP Server Implementation
Following the Model Context Protocol specification with agentic architecture
"""
import asyncio
import json
import sys
import logging
from typing import Any, Dict, List, Optional
from registry import AgenticToolRegistry
from config import Config
from protocol import MCPRequest, MCPResponse

# Import agents
from agents.openai_agent import OpenAIAgent
from agents.ollama_agent import OllamaAgent
from agents.file_agent import FileAgent

logger = logging.getLogger(__name__)

class PureAgenticMCPServer:
    """
    Pure MCP Server implementing agentic architecture.
    All functionality exposed as MCP tools provided by agents.
    """
    
    def __init__(self):
        self.config = Config()
        self.registry = AgenticToolRegistry()
        self.server_info = {
            "name": "Pure Agentic MCP Server",
            "version": "1.0.0",
            "description": "MCP server with agentic tool architecture"
        }
        self._register_agents()
    
    def _register_agents(self):
        """Register all available agents with the tool registry"""
        logger.info("Registering agents...")
        
        # Register OpenAI agent if available
        if self.config.openai_api_key:
            try:
                openai_agent = OpenAIAgent(self.config)
                self.registry.register_agent("openai", openai_agent)
                logger.info("OpenAI agent registered successfully")
            except Exception as e:
                logger.error(f"Failed to register OpenAI agent: {e}")
        else:
            logger.info("OpenAI agent not registered - API key not provided")
        
        # Register Ollama agent if available
        try:
            ollama_agent = OllamaAgent(self.config)
            if ollama_agent.is_available():
                self.registry.register_agent("ollama", ollama_agent)
                logger.info("Ollama agent registered successfully")
            else:
                logger.info("Ollama agent not available - skipping registration")
        except Exception as e:
            logger.error(f"Failed to register Ollama agent: {e}")
        
        # Register file agent (always available)
        try:
            file_agent = FileAgent()
            self.registry.register_agent("file", file_agent)
            logger.info("File agent registered successfully")
        except Exception as e:
            logger.error(f"Failed to register file agent: {e}")
        
        # Log final status
        status = self.registry.get_agent_status()
        logger.info(f"Agent registration complete: {status['total_agents']} agents, {status['total_tools']} tools")
    
    async def handle_request(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming MCP requests"""
        try:
            # Handle notifications (no response needed)
            method = request_data.get("method", "")
            if method and method.startswith("notifications/"):
                logger.info(f"Received notification: {method}")
                return None  # No response for notifications
            
            # Parse request
            request = MCPRequest(**request_data)
            logger.debug(f"Handling request: {request.method}")
            
            # Route request to appropriate handler
            if request.method == "initialize":
                return await self._handle_initialize(request)
            elif request.method == "tools/list":
                return await self._handle_list_tools(request)
            elif request.method == "tools/call":
                return await self._handle_call_tool(request)
            elif request.method == "ping":
                return await self._handle_ping(request)
            elif request.method == "agent/status":
                return await self._handle_agent_status(request)
            elif request.method == "resources/list":
                return await self._handle_resources_list(request)
            elif request.method == "prompts/list":
                return await self._handle_prompts_list(request)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request.id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {request.method}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def _handle_initialize(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle initialization request"""
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": self.server_info
            }
        }
    
    async def _handle_list_tools(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle tools list request"""
        try:
            tools = self.registry.get_all_tools()
            
            # Convert to MCP tools format
            mcp_tools = []
            for tool_name, tool_schema in tools.items():
                mcp_tools.append({
                    "name": tool_name,
                    "description": tool_schema.get("description", ""),
                    "inputSchema": tool_schema.get("inputSchema", {})
                })
            
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "result": {"tools": mcp_tools}
            }
            
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "error": {"message": f"Failed to list tools: {str(e)}"}
            }
    
    async def _handle_call_tool(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle tool call request"""
        try:
            params = request.params or {}
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not tool_name:
                return {
                    "jsonrpc": "2.0",
                    "id": request.id,
                    "error": {"message": "Tool name is required"}
                }
            
            # Call the tool through the registry
            result = await self.registry.call_tool(tool_name, arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
                        }
                    ]
                }
            }
            
        except ValueError as e:
            logger.error(f"Tool call error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "error": {"message": str(e)}
            }
        except Exception as e:
            logger.error(f"Unexpected error in tool call: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "error": {"message": f"Internal error: {str(e)}"}
            }
    
    async def _handle_ping(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle ping request"""
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": {"status": "ok", "server": self.server_info["name"]}
        }
    
    async def _handle_agent_status(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle agent status request (custom method)"""
        try:
            status = self.registry.get_agent_status()
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "result": status
            }
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "error": {"message": f"Failed to get agent status: {str(e)}"}
            }
    
    async def _handle_resources_list(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle resources list request"""
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": {"resources": []}
        }
    
    async def _handle_prompts_list(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle prompts list request"""
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": {"prompts": []}
        }
    
    async def start_stdio_server(self):
        """Start the MCP server using stdio transport"""
        logger.info("Starting Pure Agentic MCP Server (stdio transport)")
        logger.info(f"Server: {self.server_info['name']} v{self.server_info['version']}")
        
        # Log agent status
        status = self.registry.get_agent_status()
        logger.info(f"Available agents: {list(status['agents'].keys())}")
        logger.info(f"Available tools: {self.registry.list_tools()}")
        
        try:
            while True:
                # Read JSON-RPC request from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                try:
                    request_data = json.loads(line.strip())
                    response = await self.handle_request(request_data)
                    
                    # Only write response if it's not None (notifications return None)
                    if response is not None:
                        print(json.dumps(response), flush=True)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            logger.info("Pure Agentic MCP Server stopped")

def main():
    """Main entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('mcp_server.log'),
            logging.StreamHandler(sys.stderr)  # Use stderr to avoid conflicting with stdio transport
        ]
    )
    
    # Create and start server
    server = PureAgenticMCPServer()
    
    try:
        asyncio.run(server.start_stdio_server())
    except KeyboardInterrupt:
        logger.info("Server interrupted")
    except Exception as e:
        logger.error(f"Server startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
