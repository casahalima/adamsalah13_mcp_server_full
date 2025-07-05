import logging
from abc import ABC, abstractmethod
from typing import Dict, Any
from protocol import MCPRequest, MCPResponse

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Base class for all agents in the Agentic MCP architecture.
    Each agent provides MCP tools and handles tool calls.
    """
    
    @abstractmethod
    def get_tools(self) -> Dict[str, Any]:
        """
        Return MCP tool definitions this agent provides.
        
        Returns:
            Dict mapping tool names to their MCP tool schemas
        """
        pass
    
    @abstractmethod
    async def handle_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Handle a specific tool call for this agent.
        
        Args:
            tool_name: Name of the tool being called
            params: Parameters for the tool call
            
        Returns:
            Tool execution result
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this agent is available for use.
        
        Returns:
            True if agent can handle requests, False otherwise
        """
        pass
    
    # Legacy method for backward compatibility
    async def handle(self, request: MCPRequest) -> MCPResponse:
        """Legacy handler - will be deprecated"""
        logger.warning(f"Using legacy handle method in {self.__class__.__name__}")
        return MCPResponse(
            id=request.id,
            error={"message": "Legacy handler not implemented"}
        )
