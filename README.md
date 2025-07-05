# Pure Agentic MCP Server

A pure implementation of the Model Context Protocol (MCP) following an agentic architecture where all features are exposed as MCP tools through specialized agents.

## Features

- **🤖 Pure Agentic Architecture**: All capabilities (OpenAI, Ollama, File operations) are implemented as agents
- **🔗 Dual Access Modes**: MCP protocol for Claude Desktop + HTTP endpoints for web/Streamlit UI
- **⚡ Dynamic Tool Registry**: Agents register their tools automatically at startup
- **🔧 Modular Design**: Add new agents easily without modifying core server code
- **📱 Clean Web UI**: Modern Streamlit interface for interactive tool usage
- **🛡️ Graceful Degradation**: Agents fail independently without affecting the system
- **🔑 Environment-Based Config**: Secure API key management via environment variables

## Architecture Overview

The server implements a **pure agentic pattern** where:

1. **Agents** encapsulate specific functionality (OpenAI API, Ollama, file operations)
2. **Registry** manages dynamic tool registration and routing
3. **MCP Server** provides JSON-RPC protocol compliance for Claude Desktop
4. **HTTP Host** exposes tools via REST API for web interfaces
5. **Streamlit UI** provides user-friendly web access to all tools

```
Claude Desktop ←→ MCP Protocol ←→ Pure MCP Server ←→ Agent Registry ←→ Agents
                                                                      ↕
Web Browser    ←→ HTTP API     ←→ Simple MCP Host  ←→ Agent Registry ←→ Agents
```

## Quick Start

### Prerequisites

- Python 3.11+
- Virtual environment support

### Installation

```bash
git clone <repo-url>
cd mcp_server_full

# Create and activate virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Configuration

Create a `.env` file with your API keys (all optional):

```env
# OpenAI Agent (optional)
OPENAI_API_KEY=your_openai_api_key_here

# Ollama Agent (optional, uses local Ollama server)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# File Agent (enabled by default, no config needed)
# Provides file reading, writing, and listing capabilities
```

### Running the Server

#### For Claude Desktop (MCP Protocol)

```bash
# Start the pure MCP server for Claude Desktop
python run_mcp_server.py
```

Add to your Claude Desktop config (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "agentic-mcp": {
      "command": "python",
      "args": ["run_mcp_server.py"],
      "cwd": "d:\\AI Lab\\MCP research\\mcp_server_full"
    }
  }
}
```

#### For Web Interface (HTTP + Streamlit)

```bash
# Terminal 1: Start HTTP host for tools
python simple_mcp_host.py

# Terminal 2: Start Streamlit UI  
streamlit run streamlit_app.py
```

Access the web interface at: http://localhost:8501

### Testing Your Setup

```bash
# Test agent registration and tool availability
python test_quick.py

# Test specific agents
python test_both.py

# Validate server functionality
python validate_server.py
```

## Available Agents & Tools

### 🤖 OpenAI Agent
**Status**: Available with API key  
**Tools**:
- `openai_chat`: Chat completion with GPT models
- `openai_analysis`: Text analysis and insights

**Setup**: Add `OPENAI_API_KEY` to `.env` file

### 🦙 Ollama Agent  
**Status**: Available with local Ollama server  
**Tools**:
- `ollama_chat`: Chat with local Ollama models
- `ollama_generate`: Text generation

**Setup**: Install and run Ollama locally, configure `OLLAMA_BASE_URL` and `OLLAMA_MODEL`

### 📁 File Agent
**Status**: Always available  
**Tools**:
- `file_read`: Read file contents
- `file_write`: Write content to files
- `file_list`: List directory contents

**Setup**: No configuration needed

## API Usage

### MCP Protocol (Claude Desktop)

Tools are automatically available in Claude Desktop once the server is configured. Ask Claude to:
- "Read the contents of file.txt"
- "Generate text using Ollama"  
- "Analyze this text with OpenAI"

### HTTP API (Web/Streamlit)

```bash
# List available tools
curl http://localhost:8000/tools

# Call a specific tool
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "file_read",
    "arguments": {
      "file_path": "example.txt"
    }
  }'
```

## Architecture

### Core Components

- **`pure_mcp_server.py`**: Main MCP JSON-RPC server for Claude Desktop integration
- **`simple_mcp_host.py`**: HTTP wrapper that exposes MCP tools via REST API
- **`registry.py`**: Dynamic agent and tool registration system
- **`run_mcp_server.py`**: Entry point script for Claude Desktop configuration
- **`config.py`**: Environment-based configuration management
- **`protocol.py`**: MCP protocol models and types

### Agents

- **`agents/base.py`**: Base agent interface that all agents implement
- **`agents/openai_agent.py`**: OpenAI API integration agent  
- **`agents/ollama_agent.py`**: Local Ollama model integration agent
- **`agents/file_agent.py`**: File system operations agent

### User Interfaces

- **`streamlit_app.py`**: Modern web UI for interactive tool usage
- **Claude Desktop**: Direct MCP protocol integration

### Agent Registration Flow

```python
# Each agent registers its tools dynamically
class YourAgent(BaseAgent):
    def get_tools(self) -> Dict[str, Any]:
        return {
            "your_tool": {
                "description": "What your tool does",
                "inputSchema": {...}
            }
        }
    
    async def handle_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Any:
        # Handle the tool call
        pass

# Registry automatically discovers and routes tools
registry.register_agent("your_agent", YourAgent(config))
```

## Development

### Project Structure

```
mcp_server_full/
├── agents/                    # Agent implementations
│   ├── base.py               # Base agent interface
│   ├── openai_agent.py       # OpenAI integration
│   ├── ollama_agent.py       # Ollama integration
│   └── file_agent.py         # File operations
├── pure_mcp_server.py        # Main MCP server for Claude Desktop
├── simple_mcp_host.py        # HTTP host for web interfaces
├── registry.py               # Dynamic tool registration
├── run_mcp_server.py         # Claude Desktop entry point
├── streamlit_app.py          # Web UI
├── config.py                 # Configuration management
├── protocol.py               # MCP protocol models
├── requirements.txt          # Dependencies
├── .env                      # Environment variables (create this)
├── ADDING_NEW_AGENTS.md      # Detailed agent development guide
└── README.md                 # This file
```

### Adding New Agents

For a complete step-by-step guide on adding new agents, see **[ADDING_NEW_AGENTS.md](ADDING_NEW_AGENTS.md)**.

**Quick Overview:**
1. Create agent file in `agents/` inheriting from `BaseAgent`
2. Implement `get_tools()` and `handle_tool_call()` methods
3. Register agent in both `pure_mcp_server.py` and `simple_mcp_host.py`
4. Add configuration and test your agent

The guide includes complete code examples, best practices, and troubleshooting tips.

### Adding New Tools

To add new tools to existing agents:

1. Edit the agent's `get_tools()` method to define new tool schema
2. Add handler method in agent's `handle_tool_call()` method  
3. Test the new tool functionality
4. Update documentation

Example:
```python
# In your agent
def get_tools(self):
    return {
        "new_tool": {
            "description": "Description of new tool",
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "param": {"type": "string", "description": "Parameter description"}
                },
                "required": ["param"]
            }
        }
    }

async def handle_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Any:
    if tool_name == "new_tool":
        return await self._handle_new_tool(params)
```

## Troubleshooting

### Common Issues

1. **Agent Not Available**: Check API keys and service connectivity
   ```bash
   # Test agent registration
   python test_quick.py
   ```

2. **Claude Desktop Not Connecting**: Verify config path and entry point
   ```json
   # Check claude_desktop_config.json
   {
     "mcpServers": {
       "agentic-mcp": {
         "command": "python",
         "args": ["run_mcp_server.py"],
         "cwd": "d:\\AI Lab\\MCP research\\mcp_server_full"
       }
     }
   }
   ```

3. **Streamlit UI Issues**: Ensure HTTP host is running
   ```bash
   # Start HTTP host first
   python simple_mcp_host.py
   # Then start Streamlit  
   streamlit run streamlit_app.py
   ```

4. **OpenAI Errors**: Check API key and quota
   ```bash
   # Test OpenAI directly
   python openai_test.py
   ```

5. **Ollama Not Working**: Verify Ollama server is running
   ```bash
   # Check Ollama status
   curl http://localhost:11434/api/tags
   ```

### Debug Mode

Enable detailed logging:
```bash
# Set environment variable
export LOG_LEVEL=DEBUG
python run_mcp_server.py
```

### Health Checks

```bash
# Check HTTP API health
curl http://localhost:8000/health

# List registered tools
curl http://localhost:8000/tools

# Test tool call
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "file_list", "arguments": {"directory_path": "."}}'
```

## Dependencies

### Core Runtime
- **pydantic**: Configuration and data validation
- **asyncio**: Async operation support
- **httpx**: HTTP client for external APIs
- **aiofiles**: Async file operations

### Agent-Specific
- **openai**: OpenAI API client (for OpenAI agent)
- **ollama**: Ollama API client (for Ollama agent)

### Web Interface
- **streamlit**: Modern web UI framework
- **requests**: HTTP requests for Streamlit

### Development & Testing
- **pytest**: Testing framework
- **logging**: Debug and monitoring

All dependencies are automatically installed via `requirements.txt`.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Add your agent following the [agent development guide](ADDING_NEW_AGENTS.md)
4. Test your changes: `python test_quick.py`
5. Submit a pull request

### Agent Development Workflow

1. **Plan**: Define what tools your agent will provide
2. **Implement**: Create agent class inheriting from `BaseAgent`
3. **Register**: Add agent registration to both server files
4. **Test**: Verify agent works in both MCP and HTTP modes
5. **Document**: Update README and create usage examples

## License

MIT

## Streamlit Web Interface

The Streamlit app provides an intuitive web interface for all MCP tools.

### Features

- **🔧 Real-time Tool Discovery**: Automatically displays all available tools from registered agents
- **💬 Interactive Interface**: Easy-to-use forms for tool parameters
- **📊 Response Display**: Formatted display of tool results
- **� Agent Status**: Real-time monitoring of agent availability
- **⚙️ Configuration**: Environment-based setup with clear status indicators

### Usage

1. **Start the backend**: `python simple_mcp_host.py`
2. **Launch Streamlit**: `streamlit run streamlit_app.py`
3. **Open browser**: Navigate to http://localhost:8501
4. **Select tools**: Choose from available agent tools
5. **Execute**: Fill parameters and run tools interactively

### Tool Integration

The Streamlit UI automatically discovers and creates forms for any tools registered by agents, making it easy to test and use new functionality as agents are added.
