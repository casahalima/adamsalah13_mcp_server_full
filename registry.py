"""
Agentic Tool Registry for MCP Server
Manages agent registration and tool routing
"""
import logging
from typing import Dict, Any, List, Optional
from agents.base import BaseAgent

logger = logging.getLogger(__name__)

class AgenticToolRegistry:
    """
    Registry that manages agents and routes tool calls to the appropriate agent.
    This is the core of the agentic MCP architecture.
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.tool_to_agent: Dict[str, str] = {}  # tool_name -> agent_name
        self._tool_schemas: Dict[str, Any] = {}
    
    def register_agent(self, name: str, agent: BaseAgent) -> None:
        """
        Register an agent and its tools.
        
        Args:
            name: Unique name for the agent
            agent: Agent instance to register
        """
        if not agent.is_available():
            logger.warning(f"Agent {name} is not available - skipping registration")
            return
        
        self.agents[name] = agent
        
        # Register all tools provided by this agent
        tools = agent.get_tools()
        for tool_name, tool_schema in tools.items():
            if tool_name in self.tool_to_agent:
                logger.warning(f"Tool {tool_name} already registered by agent {self.tool_to_agent[tool_name]}")
                continue
            
            self.tool_to_agent[tool_name] = name
            self._tool_schemas[tool_name] = tool_schema
            logger.info(f"Registered tool '{tool_name}' from agent '{name}'")
    
    def unregister_agent(self, name: str) -> None:
        """
        Unregister an agent and all its tools.
        
        Args:
            name: Name of the agent to unregister
        """
        if name not in self.agents:
            logger.warning(f"Agent {name} not found for unregistration")
            return
        
        # Remove all tools for this agent
        tools_to_remove = [
            tool_name for tool_name, agent_name in self.tool_to_agent.items()
            if agent_name == name
        ]
        
        for tool_name in tools_to_remove:
            del self.tool_to_agent[tool_name]
            del self._tool_schemas[tool_name]
            logger.info(f"Unregistered tool '{tool_name}' from agent '{name}'")
        
        del self.agents[name]
        logger.info(f"Unregistered agent '{name}'")
    
    def get_all_tools(self) -> Dict[str, Any]:
        """
        Get all available tools from all registered agents.
        
        Returns:
            Dict mapping tool names to their MCP schemas
        """
        return self._tool_schemas.copy()
    
    def get_agent_tools(self, agent_name: str) -> Dict[str, Any]:
        """
        Get tools provided by a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dict mapping tool names to their MCP schemas
        """
        if agent_name not in self.agents:
            return {}
        
        return {
            tool_name: schema 
            for tool_name, schema in self._tool_schemas.items()
            if self.tool_to_agent[tool_name] == agent_name
        }
    
    def get_tool_schema(self, tool_name: str) -> Optional[Any]:
        """
        Get schema for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool schema or None if not found
        """
        return self._tool_schemas.get(tool_name)
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Route a tool call to the appropriate agent.
        
        Args:
            tool_name: Name of the tool to call
            params: Parameters for the tool call
            
        Returns:
            Result from the tool execution
            
        Raises:
            ValueError: If tool is not found or agent is not available
        """
        # Find the agent that provides this tool
        agent_name = self.tool_to_agent.get(tool_name)
        if not agent_name:
            available_tools = list(self._tool_schemas.keys())
            raise ValueError(f"Unknown tool: {tool_name}. Available tools: {available_tools}")
        
        # Get the agent
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent {agent_name} not found for tool {tool_name}")
        
        # Check if agent is still available
        if not agent.is_available():
            raise ValueError(f"Agent {agent_name} is not available")
        
        # Call the tool
        try:
            result = await agent.handle_tool_call(tool_name, params)
            logger.info(f"Successfully executed tool '{tool_name}' via agent '{agent_name}'")
            return result
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}' via agent '{agent_name}': {e}")
            raise
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status information for all registered agents.
        
        Returns:
            Dict with agent status information
        """
        status = {
            "total_agents": len(self.agents),
            "total_tools": len(self._tool_schemas),
            "agents": {}
        }
        
        for agent_name, agent in self.agents.items():
            agent_tools = self.get_agent_tools(agent_name)
            status["agents"][agent_name] = {
                "available": agent.is_available(),
                "tool_count": len(agent_tools),
                "tools": list(agent_tools.keys())
            }
        
        return status
    
    def list_agents(self) -> List[str]:
        """Get list of registered agent names."""
        return list(self.agents.keys())
    
    def list_tools(self) -> List[str]:
        """Get list of all available tool names."""
        return list(self._tool_schemas.keys())
