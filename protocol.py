"""
MCP Protocol Models for Pure Agentic MCP Server
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel

class MCPRequest(BaseModel):
    """MCP request model"""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: str
    params: Optional[Dict[str, Any]] = None
    
class MCPResponse(BaseModel):
    """MCP response model"""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    
    def model_dump(self, **kwargs):
        """Custom model_dump that excludes None fields"""
        data = super().model_dump(**kwargs)
        # Remove None fields to comply with JSON-RPC
        return {k: v for k, v in data.items() if v is not None}
    
class MCPTool(BaseModel):
    """MCP tool definition"""
    name: str
    description: str
    inputSchema: Dict[str, Any]
    
class MCPError(BaseModel):
    """MCP error model"""
    code: int
    message: str
    data: Optional[Any] = None

# Common MCP error codes
class MCPErrorCodes:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # Custom application errors
    TOOL_NOT_FOUND = -32001
    TOOL_EXECUTION_ERROR = -32002
    AGENT_NOT_AVAILABLE = -32003
