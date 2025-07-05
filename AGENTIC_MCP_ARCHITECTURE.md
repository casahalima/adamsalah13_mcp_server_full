# Agentic MCP Architecture: Pure Implementation

## Overview

This document outlines the **Pure Agentic MCP Architecture** where every capability is implemented as an MCP tool, and agents are the primary abstraction for organizing and providing these tools.

## Core Principles

### 1. Agents ARE MCP Tools
- Each agent registers one or more MCP tools
- Agents encapsulate domain-specific functionality (AI, file operations, graph operations, etc.)
- Tools are the interface through which Claude Desktop (or any MCP client) interacts with agents

### 2. Pure MCP Protocol
- The core server only speaks MCP (stdio, JSON-RPC)
- No HTTP endpoints in the core server
- Clean separation of concerns

### 3. MCP Host as Optional Proxy
- Separate component that can expose MCP tools as HTTP endpoints
- Enables web UI integration (Streamlit) while maintaining MCP purity
- Host acts as an MCP client internally

## Architecture Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Claude        │    │   Streamlit      │    │   Other MCP     │
│   Desktop       │    │   Web UI         │    │   Clients       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │ MCP Protocol          │ HTTP API              │ MCP Protocol
         │ (stdio/JSON-RPC)      │ (REST)                │ (stdio/JSON-RPC)
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Pure MCP      │    │   MCP Host       │    │   Pure MCP      │
│   Server        │◄───┤   (HTTP Proxy)   │    │   Server        │
│                 │    │                  │    │                 │
│   - OpenAI Agent│    │   - Exposes MCP  │    │   - Same Tools  │
│   - Ollama Agent│    │     tools as HTTP│    │   - Different   │
│   - File Agent  │    │   - Acts as MCP  │    │     Instance    │
│   - Graph Agent │    │     client       │    │                 │
│   - Vector Agent│    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Agent-Tool Mapping

### OpenAI Agent
**Tools Registered:**
- `openai_chat` - Conversational AI
- `openai_analysis` - Text analysis 
- `openai_completion` - Text completion
- `openai_summarize` - Text summarization

### Ollama Agent  
**Tools Registered:**
- `ollama_chat` - Local conversational AI
- `ollama_analysis` - Local text analysis
- `ollama_completion` - Local text completion

### File Agent
**Tools Registered:**
- `file_read` - Read file contents
- `file_write` - Write file contents  
- `file_list` - List directory contents
- `file_search` - Search within files

### Graph Agent
**Tools Registered:**
- `graph_add_node` - Add nodes to knowledge graph
- `graph_add_edge` - Add relationships
- `graph_query` - Query the graph
- `graph_visualize` - Generate graph visualizations

### Vector Agent
**Tools Registered:**
- `vector_embed` - Generate embeddings
- `vector_search` - Semantic search
- `vector_cluster` - Document clustering
- `vector_similarity` - Similarity analysis

## Implementation Pattern

### 1. Agent Base Class
```python
class BaseAgent(ABC):
    @abstractmethod
    def get_tools(self) -> Dict[str, Any]:
        """Return MCP tool definitions this agent provides"""
        pass
    
    @abstractmethod
    async def handle_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Handle a specific tool call"""
        pass
```

### 2. Tool Registry
```python
class AgenticToolRegistry:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.tools: Dict[str, str] = {}  # tool_name -> agent_name
    
    def register_agent(self, name: str, agent: BaseAgent):
        """Register an agent and its tools"""
        self.agents[name] = agent
        for tool_name in agent.get_tools():
            self.tools[tool_name] = name
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Route tool call to appropriate agent"""
        agent_name = self.tools.get(tool_name)
        if not agent_name:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        agent = self.agents[agent_name]
        return await agent.handle_tool_call(tool_name, params)
```

### 3. Pure MCP Server
```python
class PureMCPServer:
    def __init__(self):
        self.registry = AgenticToolRegistry()
        self._register_agents()
    
    def _register_agents(self):
        """Register all available agents"""
        config = Config()
        
        # Register AI agents
        if config.openai_api_key:
            self.registry.register_agent("openai", OpenAIAgent(config))
        
        if config.ollama_model:
            self.registry.register_agent("ollama", OllamaAgent(config))
        
        # Register utility agents
        self.registry.register_agent("file", FileAgent())
        
        if config.neo4j_uri:
            self.registry.register_agent("graph", GraphAgent(config))
        
        if config.vector_model:
            self.registry.register_agent("vector", VectorAgent(config))
    
    async def handle_list_tools(self) -> Dict[str, Any]:
        """List all available tools from all agents"""
        tools = {}
        for agent in self.registry.agents.values():
            tools.update(agent.get_tools())
        return {"tools": tools}
    
    async def handle_call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Route tool call to appropriate agent"""
        return await self.registry.call_tool(name, arguments)
```

## Benefits of This Architecture

### 1. True MCP Compliance
- Server only speaks MCP protocol
- All functionality exposed as standard MCP tools
- Compatible with any MCP client

### 2. Agentic Organization
- Logical grouping of related tools under agents
- Clear separation of concerns
- Easy to add new agents/capabilities

### 3. Flexible Integration
- HTTP access via optional MCP host
- Can run multiple MCP servers for different use cases
- Easy to scale or distribute agents

### 4. Development Benefits
- Clear patterns for adding new agents
- Testable components
- Type-safe interfaces

## Example Usage

### From Claude Desktop (Direct MCP)
```
User: "Analyze this text using OpenAI"
Claude: Calls `openai_analysis` tool with text parameter
OpenAI Agent: Processes request and returns analysis
Claude: Presents results to user
```

### From Streamlit (via MCP Host)
```
User: Clicks "Analyze Text" button
Streamlit: Makes HTTP POST to /tools/openai_analysis
MCP Host: Converts HTTP request to MCP tool call
Pure MCP Server: Routes to OpenAI Agent
OpenAI Agent: Processes and returns result
MCP Host: Converts MCP response to HTTP response  
Streamlit: Displays results to user
```

## Next Steps

1. **Implement Pure MCP Server** with agentic tool registry
2. **Refactor Existing Agents** to follow the new pattern
3. **Create MCP Host** for HTTP endpoint exposure
4. **Update Documentation** with concrete examples
5. **Add Agent Discovery** for dynamic tool registration

## Development Guide

For detailed instructions on adding new agents to this architecture, see **[ADDING_NEW_AGENTS.md](ADDING_NEW_AGENTS.md)**.

This architecture ensures that the agentic pattern is not just a organizational concept, but a fundamental part of how the MCP server operates, while maintaining pure MCP compliance for maximum compatibility and extensibility.
