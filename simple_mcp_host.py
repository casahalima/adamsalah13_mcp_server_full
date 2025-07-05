"""
Simple MCP Host - Direct Integration
Directly integrates with the agentic registry without subprocess
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from aiohttp import web
from aiohttp.web import Request, Response
import aiohttp_cors

# Import our agentic components
from registry import AgenticToolRegistry
from config import Config
from agents.openai_agent import OpenAIAgent
from agents.ollama_agent import OllamaAgent
from agents.file_agent import FileAgent

logger = logging.getLogger(__name__)

class SimpleMCPHost:
    """
    Simple MCP Host that directly uses the agentic registry.
    Provides HTTP endpoints for MCP tools without subprocess complexity.
    """
    
    def __init__(self):
        self.config = Config()
        self.registry = AgenticToolRegistry()
        self.server_info = {
            "name": "Simple MCP Host",
            "version": "1.0.0",
            "description": "Direct HTTP access to agentic MCP tools"
        }
        self._register_agents()
    
    def _register_agents(self):
        """Register all available agents with the tool registry"""
        logger.info("Registering agents...")
        
        # Register file agent (always available)
        try:
            file_agent = FileAgent()
            self.registry.register_agent("file", file_agent)
            logger.info("File agent registered successfully")
        except Exception as e:
            logger.error(f"Failed to register file agent: {e}")
        
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
        
        # Log final status
        status = self.registry.get_agent_status()
        logger.info(f"Agent registration complete: {status['total_agents']} agents, {status['total_tools']} tools")
    
    # HTTP endpoint handlers
    
    async def handle_tools_list(self, request: Request) -> Response:
        """HTTP endpoint to list available tools"""
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
            
            return web.json_response({
                "status": "success",
                "tools": mcp_tools,
                "server_info": self.server_info,
                "agent_count": len(self.registry.list_agents()),
                "tool_count": len(tools)
            })
            
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return web.json_response({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    async def handle_tool_call(self, request: Request) -> Response:
        """HTTP endpoint to call a tool"""
        try:
            data = await request.json()
            tool_name = data.get("tool_name")
            arguments = data.get("arguments", {})
            
            if not tool_name:
                return web.json_response({
                    "status": "error",
                    "message": "tool_name is required"
                }, status=400)
            
            logger.info(f"Calling tool: {tool_name} with arguments: {arguments}")
            result = await self.registry.call_tool(tool_name, arguments)
            
            return web.json_response({
                "status": "success",
                "tool_name": tool_name,
                "result": result
            })
            
        except ValueError as e:
            logger.error(f"Tool call validation error: {e}")
            return web.json_response({
                "status": "error",
                "message": str(e)
            }, status=400)
        except Exception as e:
            logger.error(f"Error calling tool: {e}")
            return web.json_response({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    async def handle_agent_status(self, request: Request) -> Response:
        """HTTP endpoint to get agent status"""
        try:
            status = self.registry.get_agent_status()
            
            return web.json_response({
                "status": "success",
                "agent_status": status,
                "server_info": self.server_info
            })
            
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return web.json_response({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    async def handle_ping(self, request: Request) -> Response:
        """HTTP endpoint for health check"""
        try:
            return web.json_response({
                "status": "success",
                "message": "Simple MCP Host is running",
                "server_info": self.server_info,
                "available_agents": self.registry.list_agents(),
                "available_tools": self.registry.list_tools()
            })
            
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            return web.json_response({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    # Specific tool endpoints for common operations
    
    async def handle_openai_chat(self, request: Request) -> Response:
        """HTTP endpoint for OpenAI chat"""
        try:
            data = await request.json()
            result = await self.registry.call_tool("openai_chat", data)
            
            return web.json_response({
                "status": "success",
                "response": result
            })
            
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            return web.json_response({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    async def handle_ollama_chat(self, request: Request) -> Response:
        """HTTP endpoint for Ollama chat"""
        try:
            data = await request.json()
            result = await self.registry.call_tool("ollama_chat", data)
            
            return web.json_response({
                "status": "success",
                "response": result
            })
            
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            return web.json_response({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    async def handle_file_operation(self, request: Request) -> Response:
        """HTTP endpoint for file operations"""
        try:
            data = await request.json()
            operation = data.get("operation")  # read, write, list, search, etc.
            
            if not operation:
                return web.json_response({
                    "status": "error",
                    "message": "operation is required (read, write, list, search, info, create_directory)"
                }, status=400)
            
            tool_name = f"file_{operation}"
            arguments = data.get("arguments", {})
            
            result = await self.registry.call_tool(tool_name, arguments)
            
            return web.json_response({
                "status": "success",
                "operation": operation,
                "result": result
            })
            
        except Exception as e:
            logger.error(f"File operation error: {e}")
            return web.json_response({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    # Analysis endpoints
    
    async def handle_analyze_text(self, request: Request) -> Response:
        """HTTP endpoint for text analysis (tries OpenAI first, then Ollama)"""
        try:
            data = await request.json()
            text = data.get("text")
            analysis_type = data.get("analysis_type", "general")
            
            if not text:
                return web.json_response({
                    "status": "error",
                    "message": "text is required"
                }, status=400)
            
            # Try OpenAI first, then Ollama
            result = None
            used_tool = None
            
            if "openai_analysis" in self.registry.get_all_tools():
                try:
                    result = await self.registry.call_tool("openai_analysis", {
                        "text": text,
                        "analysis_type": analysis_type
                    })
                    used_tool = "openai_analysis"
                except Exception as e:
                    logger.warning(f"OpenAI analysis failed, trying Ollama: {e}")
            
            if not result and "ollama_analysis" in self.registry.get_all_tools():
                try:
                    result = await self.registry.call_tool("ollama_analysis", {
                        "text": text,
                        "analysis_type": analysis_type
                    })
                    used_tool = "ollama_analysis"
                except Exception as e:
                    logger.error(f"Both OpenAI and Ollama analysis failed: {e}")
            
            if not result:
                return web.json_response({
                    "status": "error",
                    "message": "No analysis tools available"
                }, status=503)
            
            return web.json_response({
                "status": "success",
                "analysis_type": analysis_type,
                "used_tool": used_tool,
                "result": result
            })
            
        except Exception as e:
            logger.error(f"Text analysis error: {e}")
            return web.json_response({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    def create_app(self) -> web.Application:
        """Create the aiohttp web application"""
        app = web.Application()
        
        # Setup CORS
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # General MCP endpoints
        cors.add(app.router.add_get("/tools", self.handle_tools_list))
        cors.add(app.router.add_post("/tools/call", self.handle_tool_call))
        cors.add(app.router.add_get("/agent/status", self.handle_agent_status))
        cors.add(app.router.add_get("/ping", self.handle_ping))
        
        # Specific tool endpoints
        cors.add(app.router.add_post("/openai/chat", self.handle_openai_chat))
        cors.add(app.router.add_post("/ollama/chat", self.handle_ollama_chat))
        cors.add(app.router.add_post("/file", self.handle_file_operation))
        cors.add(app.router.add_post("/analyze", self.handle_analyze_text))
        
        return app
    
    async def start_http_server(self, host: str = "localhost", port: int = 8000):
        """Start the HTTP server"""
        app = self.create_app()
        
        logger.info(f"Starting Simple MCP Host HTTP server on {host}:{port}")
        
        # Log available tools
        tools = self.registry.get_all_tools()
        logger.info(f"Available tools: {list(tools.keys())}")
        
        # Log agent status
        status = self.registry.get_agent_status()
        for agent_name, agent_info in status["agents"].items():
            status_symbol = "✓" if agent_info["available"] else "✗"
            logger.info(f"{status_symbol} {agent_name}: {agent_info['tool_count']} tools")
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        logger.info(f"Simple MCP Host ready at http://{host}:{port}")
        logger.info("Endpoints:")
        logger.info("  GET  /tools           - List available tools")
        logger.info("  POST /tools/call      - Call any tool")
        logger.info("  GET  /agent/status    - Get agent status")
        logger.info("  GET  /ping            - Health check")
        logger.info("  POST /openai/chat     - OpenAI chat")
        logger.info("  POST /ollama/chat     - Ollama chat")
        logger.info("  POST /file            - File operations")
        logger.info("  POST /analyze         - Text analysis (auto-select tool)")
        
        return runner

async def main():
    """Main entry point for the Simple MCP Host"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    host = SimpleMCPHost()
    
    try:
        runner = await host.start_http_server()
        
        # Keep the server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            await runner.cleanup()
            
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
