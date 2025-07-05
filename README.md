# MCP Agentic Server

A modular implementation of the Model Context Protocol (MCP), orchestrating multiple agents and tool handlers.

## Features

- **Multi-Agent Architecture**: NLU, Query, Validation, and Composition agents
- **Dual API Support**: Both MCP JSON-RPC and OpenAI-compatible REST APIs
- **Tool Integration**: File handling, vector operations, and graph database support
- **Async Processing**: Full async/await support for scalable operations
- **Graceful Degradation**: Optional components can fail without system failure
- **Configuration-Driven**: Environment-based configuration with sensible defaults

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

Create a `.env` file (optional - defaults are provided):

```env
# Database configuration (optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# AI Model configuration (optional)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Running the Server

#### Quick Start (All Services)

```bash
# Start everything at once
python startup.py all
```

This starts:
- MCP JSON-RPC server (port 9000)
- OpenAI-compatible API (port 8000) 
- Streamlit web UI (port 8501)

Access the web interface at: http://localhost:8501

#### Individual Services

```bash
# Check dependencies and configuration
python startup.py check

# Run functionality tests
python startup.py test

# Start MCP JSON-RPC server only (port 9000)
python startup.py mcp

# Start OpenAI-compatible API server only (port 8000)
python startup.py openai

# Start Streamlit web UI only (requires server running)
python startup.py streamlit
```

#### Direct Server Commands (Alternative)

```bash
# MCP server only
python server.py mcp

# OpenAI API server only
python server.py flask

# Streamlit UI (requires httpx and requests)
streamlit run streamlit_app.py
```

### Testing

```bash
# Run all tests
pytest

# Run specific test files
pytest tests/test_protocol.py -v

# Test basic functionality
python test_functionality.py

# Test with CLI client
python cli.py
```

## API Usage

### MCP JSON-RPC API (Port 9000)

```bash
curl -X POST http://localhost:9000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "id": "1",
    "method": "nlu/parse",
    "params": {"text": "Hello world"}
  }'
```

### OpenAI-Compatible API (Port 8000)

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello world"}]
  }'
```

## Architecture

### Components

- **`config.py`**: Configuration management using Pydantic
- **`protocol.py`**: MCP protocol models (Request, Response, Tool)
- **`agents/`**: Specialized processing agents
  - `nlu.py`: Natural Language Understanding
  - `query.py`: Data retrieval and search
  - `validation.py`: Input validation and verification
  - `composition.py`: Response generation and formatting
- **`tools/`**: External tool handlers
  - `file_handler.py`: File system operations
  - `vector_handler.py`: Text embeddings and similarity
  - `graph_handler.py`: Neo4j graph database operations
- **`manager.py`**: Central orchestration and routing
- **`server.py`**: HTTP server implementations (aiohttp + Flask)
- **`streamlit_app.py`**: Web-based chat interface

### Request Routing

- `nlu/*` → NLUAgent
- `query/*` → QueryAgent  
- `validate/*` → ValidationAgent
- `compose/*` → CompositionAgent

## Development

### Project Structure

```
mcp_server_full/
├── agents/                 # Processing agents
├── tools/                  # External tool handlers
├── tests/                  # Test files
├── diagrams/               # Architecture diagrams
├── config.py              # Configuration management
├── protocol.py            # MCP protocol models
├── manager.py             # Agent orchestration
├── server.py              # HTTP servers
├── cli.py                 # Test client
├── streamlit_app.py       # Web UI
├── startup.py             # Server management
├── test_functionality.py  # Basic functionality tests
├── requirements.txt       # Dependencies
├── DESIGN.md              # Detailed design document
└── README.md              # This file
```

### Adding New Agents

1. Create agent file in `agents/` inheriting from `BaseAgent`
2. Implement the `handle()` method
3. Add routing logic to `manager.py`
4. Add tests in `tests/agents/`

### Adding New Tools

1. Create tool file in `tools/` inheriting from `MCPToolHandler`
2. Implement the `run()` method
3. Initialize in `manager.py`
4. Add tests in `tests/tools/`

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated and dependencies installed
2. **Configuration Errors**: Check `.env` file format and environment variables
3. **Port Conflicts**: Ensure ports 8000 and 9000 are available
4. **Database Connection**: Verify Neo4j is running (optional component)
5. **Model Loading**: Ensure sufficient disk space for sentence-transformer models

### Debug Mode

```bash
python startup.py mcp --debug
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Dependencies

### Runtime
- aiohttp, flask: HTTP servers
- pydantic, pydantic-settings: Data validation and configuration
- sentence-transformers: Text embeddings
- neo4j: Graph database client
- aiofiles: Async file operations
- streamlit: Web UI

### Development
- pytest: Testing
- flake8: Code linting
- pre-commit: Git hooks

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run `pytest` and `flake8`
5. Submit a pull request

## License

[Add your license here]

## Streamlit Web Interface

The enhanced Streamlit app provides a user-friendly web interface for interacting with the MCP server.

### Features

- **🔧 Server Integration**: Connects to running MCP/OpenAI servers via HTTP
- **🏥 Health Monitoring**: Real-time server status checking
- **💬 Chat Interface**: Interactive conversation with response history
- **⚙️ Configuration**: Server type selection and URL customization
- **🔄 Dual Protocol Support**: Switch between MCP JSON-RPC and OpenAI APIs
- **📝 Smart Responses**: Enhance
d composition agent with contextual replies
- **🧹 Session Management**: Clear history and reset conversations

### Usage

1. **Start Services**: `python startup.py all`
2. **Open Browser**: Navigate to http://localhost:8501
3. **Check Status**: Use sidebar to verify server connectivity
4. **Start Chatting**: Type messages and receive intelligent responses

### Supported Message Types

- **Greetings**: "Hello", "Hi" → Welcome responses
- **Help Requests**: "What can you do?" → Capability descriptions  
- **Analysis**: "Analyze this" → NLU method recommendations
- **Search**: "Find something" → Query method suggestions
- **Validation**: "Check this" → Validation method info
- **General Chat**: Any other message → Contextual responses
