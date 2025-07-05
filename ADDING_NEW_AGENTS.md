# Adding New Agents to Pure Agentic MCP Server

## Complete Step-by-Step Guide

This guide walks you through adding new agents to the Pure Agentic MCP Server, following the established agentic architecture pattern.

## Table of Contents

1. [Overview](#overview)
2. [Step 1: Create Agent File](#step-1-create-agent-file)
3. [Step 2: Implement Base Agent Interface](#step-2-implement-base-agent-interface)
4. [Step 3: Define MCP Tools](#step-3-define-mcp-tools)
5. [Step 4: Implement Tool Handlers](#step-4-implement-tool-handlers)
6. [Step 5: Register Agent](#step-5-register-agent)
7. [Step 6: Update Configuration](#step-6-update-configuration)
8. [Step 7: Test Your Agent](#step-7-test-your-agent)
9. [Example: Weather Agent](#example-weather-agent)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The Pure Agentic MCP Server uses an agent-based architecture where each agent:
- Inherits from `BaseAgent`
- Defines its own MCP tools with JSON schemas
- Handles tool calls independently
- Manages its own dependencies and availability

**Agent Flow:**
```
User Request → Registry → Agent → Tool Handler → External Service → Response
```

---

## Step 1: Create Agent File

Create a new file in the `agents/` directory:

```bash
# Navigate to agents directory
cd agents/

# Create new agent file
touch your_agent_name.py
```

**File naming convention:** `{service}_agent.py` (e.g., `weather_agent.py`, `database_agent.py`)

---

## Step 2: Implement Base Agent Interface

Every agent must inherit from `BaseAgent` and implement required methods:

```python
import logging
import asyncio
from typing import Optional, Dict, Any, List
from agents.base import BaseAgent

logger = logging.getLogger(__name__)

class YourAgent(BaseAgent):
    """
    Your Agent Description
    Provides MCP tools for [describe functionality]
    """
    
    def __init__(self, config):
        self.config = config
        self.client = None  # Your service client/connection
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize your service client"""
        try:
            # Initialize your external service connection
            # self.client = YourServiceClient(api_key=self.config.your_api_key)
            logger.info("Your agent client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize your agent client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if agent is available"""
        # Return True if your service is accessible
        return self.client is not None
    
    def get_tools(self) -> Dict[str, Any]:
        """Define MCP tools provided by this agent"""
        if not self.is_available():
            return {}
        
        return {
            # Define your tools here (Step 3)
        }
    
    async def handle_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Handle tool calls for this agent"""
        if not self.is_available():
            raise ValueError("Your agent is not available")
        
        try:
            # Route to appropriate handler (Step 4)
            if tool_name == "your_tool_name":
                return await self._handle_your_tool(params)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
        except Exception as e:
            logger.error(f"Error in your agent tool {tool_name}: {e}")
            raise
```

---

## Step 3: Define MCP Tools

Define your tools in the `get_tools()` method using proper JSON Schema:

```python
def get_tools(self) -> Dict[str, Any]:
    """Define MCP tools provided by this agent"""
    if not self.is_available():
        return {}
    
    return {
        "your_tool_name": {
            "description": "Clear description of what this tool does",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "required_param": {
                        "type": "string",
                        "description": "Description of required parameter"
                    },
                    "optional_param": {
                        "type": "string",
                        "description": "Description of optional parameter",
                        "default": "default_value"
                    },
                    "numeric_param": {
                        "type": "number",
                        "description": "Numeric parameter",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "enum_param": {
                        "type": "string",
                        "enum": ["option1", "option2", "option3"],
                        "description": "Parameter with predefined options"
                    }
                },
                "required": ["required_param"]
            }
        },
        "another_tool": {
            "description": "Another tool description",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Data to process"
                    }
                },
                "required": ["data"]
            }
        }
    }
```

**JSON Schema Types:**
- `string` - Text values
- `number` - Numeric values (int/float)
- `integer` - Integer values only
- `boolean` - True/false
- `array` - Lists of values
- `object` - Nested objects

**Common Properties:**
- `description` - Always include clear descriptions
- `required` - List required parameters
- `default` - Set default values
- `enum` - Restrict to specific values
- `minimum`/`maximum` - Numeric constraints

---

## Step 4: Implement Tool Handlers

Create handler methods for each tool:

```python
async def _handle_your_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle your specific tool"""
    # Extract parameters
    required_param = params.get("required_param")
    optional_param = params.get("optional_param", "default_value")
    
    # Validate parameters
    if not required_param:
        raise ValueError("required_param is required")
    
    try:
        # Call your external service
        result = await self._call_external_service(required_param, optional_param)
        
        # Return structured response
        return {
            "success": True,
            "data": result,
            "metadata": {
                "processed_at": "2025-07-04T00:00:00Z",
                "service": "your_service"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in your tool: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }

async def _call_external_service(self, param1: str, param2: str) -> Any:
    """Helper method to call external service"""
    # For blocking calls, use asyncio.to_thread
    if hasattr(self.client, 'blocking_method'):
        return await asyncio.to_thread(self.client.blocking_method, param1, param2)
    
    # For async clients, call directly
    return await self.client.async_method(param1, param2)
```

**Handler Best Practices:**
- Always validate input parameters
- Use try/catch for error handling
- Return structured responses
- Use `asyncio.to_thread()` for blocking operations
- Log errors appropriately

---

## Step 5: Register Agent

Add your agent to both MCP servers:

### 5.1 Update Pure MCP Server (Claude Desktop)

Edit `pure_mcp_server.py`:

```python
# Add import at top
from agents.your_agent import YourAgent

class PureAgenticMCPServer:
    def _register_agents(self):
        """Register all available agents with the tool registry"""
        logger.info("Registering agents...")
        
        # ...existing agents...
        
        # Register Your Agent
        try:
            your_agent = YourAgent(self.config)
            if your_agent.is_available():
                self.registry.register_agent("your_agent", your_agent)
                logger.info("Your agent registered successfully")
            else:
                logger.info("Your agent not available - skipping registration")
        except Exception as e:
            logger.error(f"Failed to register your agent: {e}")
        
        # ...rest of method...
```

### 5.2 Update Simple MCP Host (HTTP/Streamlit)

Edit `simple_mcp_host.py`:

```python
# Add import at top
from agents.your_agent import YourAgent

class SimpleMCPHost:
    def _register_agents(self):
        """Register all available agents with the tool registry"""
        logger.info("Registering agents...")
        
        # ...existing agents...
        
        # Register Your Agent
        try:
            your_agent = YourAgent(self.config)
            if your_agent.is_available():
                self.registry.register_agent("your_agent", your_agent)
                logger.info("Your agent registered successfully")
            else:
                logger.info("Your agent not available - skipping registration")
        except Exception as e:
            logger.error(f"Failed to register your agent: {e}")
        
        # ...rest of method...
```

---

## Step 6: Update Configuration

### 6.1 Add Configuration Options

Edit `config.py`:

```python
class Config(BaseSettings):
    # ...existing config...
    
    # Your Agent configuration
    your_agent_api_key: Optional[str] = Field(default=None)
    your_agent_base_url: str = Field(default="https://api.yourservice.com")
    your_agent_timeout: int = Field(default=30)
    
    class Config:
        env_file = ".env"
```

### 6.2 Add Environment Variables

Edit `.env`:

```bash
# Your Agent configuration
YOUR_AGENT_API_KEY=your_api_key_here
YOUR_AGENT_BASE_URL=https://api.yourservice.com
YOUR_AGENT_TIMEOUT=30
```

### 6.3 Update Dependencies

Edit `requirements.txt`:

```txt
# Add your agent's dependencies
your-service-client>=1.0.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Step 7: Test Your Agent

### 7.1 Create Test Script

```python
#!/usr/bin/env python3
"""Test your new agent"""
import asyncio
import logging
from config import Config
from agents.your_agent import YourAgent

async def test_your_agent():
    config = Config()
    agent = YourAgent(config)
    
    print(f"Agent available: {agent.is_available()}")
    
    if agent.is_available():
        tools = agent.get_tools()
        print(f"Tools: {list(tools.keys())}")
        
        # Test a tool call
        result = await agent.handle_tool_call("your_tool_name", {
            "required_param": "test_value"
        })
        print(f"Result: {result}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_your_agent())
```

### 7.2 Test via HTTP API

Start the HTTP server:

```bash
python simple_mcp_host.py
```

Test via curl:

```bash
# List tools
curl http://localhost:8000/tools

# Call your tool
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "your_tool_name",
    "arguments": {
      "required_param": "test_value"
    }
  }'
```

### 7.3 Test via Claude Desktop

1. Restart Claude Desktop
2. Your agent tools should appear in the MCP server
3. Test by asking Claude to use your tools

---

## Example: Weather Agent

Here's a complete example implementing a weather agent:

```python
import logging
import asyncio
import httpx
from typing import Optional, Dict, Any
from agents.base import BaseAgent

logger = logging.getLogger(__name__)

class WeatherAgent(BaseAgent):
    """
    Weather Agent for current weather and forecasts
    Provides MCP tools for weather information retrieval
    """
    
    def __init__(self, config):
        self.config = config
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize weather API client"""
        if self.config.weather_api_key:
            try:
                # Using httpx for HTTP requests
                self.client = httpx.AsyncClient(
                    base_url="https://api.openweathermap.org/data/2.5",
                    timeout=30.0
                )
                logger.info("Weather agent initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize weather client: {e}")
                self.client = None
        else:
            logger.warning("Weather API key not provided")
    
    def is_available(self) -> bool:
        """Check if weather agent is available"""
        return self.client is not None and self.config.weather_api_key
    
    def get_tools(self) -> Dict[str, Any]:
        """Define MCP tools for weather"""
        if not self.is_available():
            return {}
        
        return {
            "weather_current": {
                "description": "Get current weather for a location",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or coordinates (lat,lon)"
                        },
                        "units": {
                            "type": "string",
                            "enum": ["metric", "imperial", "kelvin"],
                            "description": "Temperature units",
                            "default": "metric"
                        }
                    },
                    "required": ["location"]
                }
            },
            "weather_forecast": {
                "description": "Get weather forecast for a location",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or coordinates"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of forecast days",
                            "minimum": 1,
                            "maximum": 5,
                            "default": 3
                        },
                        "units": {
                            "type": "string",
                            "enum": ["metric", "imperial"],
                            "default": "metric"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    
    async def handle_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Handle weather tool calls"""
        if not self.is_available():
            raise ValueError("Weather agent not available. Please configure WEATHER_API_KEY.")
        
        try:
            if tool_name == "weather_current":
                return await self._handle_current_weather(params)
            elif tool_name == "weather_forecast":
                return await self._handle_forecast(params)
            else:
                raise ValueError(f"Unknown weather tool: {tool_name}")
        except Exception as e:
            logger.error(f"Error in weather tool {tool_name}: {e}")
            raise
    
    async def _handle_current_weather(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get current weather"""
        location = params.get("location")
        units = params.get("units", "metric")
        
        if not location:
            raise ValueError("Location is required")
        
        try:
            response = await self.client.get("/weather", params={
                "q": location,
                "appid": self.config.weather_api_key,
                "units": units
            })
            response.raise_for_status()
            
            data = response.json()
            return {
                "location": data["name"],
                "country": data["sys"]["country"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"],
                "wind_speed": data["wind"]["speed"],
                "units": units
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Location '{location}' not found")
            else:
                raise ValueError(f"Weather API error: {e.response.status_code}")
        except Exception as e:
            raise ValueError(f"Failed to get weather: {str(e)}")
    
    async def _handle_forecast(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get weather forecast"""
        location = params.get("location")
        days = params.get("days", 3)
        units = params.get("units", "metric")
        
        try:
            response = await self.client.get("/forecast", params={
                "q": location,
                "appid": self.config.weather_api_key,
                "units": units,
                "cnt": days * 8  # 8 forecasts per day (3-hour intervals)
            })
            response.raise_for_status()
            
            data = response.json()
            forecast_data = []
            
            for item in data["list"][:days * 8:8]:  # One per day
                forecast_data.append({
                    "date": item["dt_txt"].split()[0],
                    "temperature": item["main"]["temp"],
                    "description": item["weather"][0]["description"],
                    "humidity": item["main"]["humidity"]
                })
            
            return {
                "location": data["city"]["name"],
                "country": data["city"]["country"],
                "forecast": forecast_data,
                "units": units
            }
            
        except Exception as e:
            raise ValueError(f"Failed to get forecast: {str(e)}")
```

**Configuration for Weather Agent:**

Add to `config.py`:
```python
weather_api_key: Optional[str] = Field(default=None)
```

Add to `.env`:
```bash
WEATHER_API_KEY=your_openweather_api_key
```

---

## Best Practices

### 1. Error Handling
- Always validate input parameters
- Use specific error messages
- Log errors with context
- Handle external service failures gracefully

### 2. Async Operations
- Use `async/await` for all I/O operations
- Use `asyncio.to_thread()` for blocking calls
- Don't block the event loop

### 3. Configuration
- Use environment variables for secrets
- Provide sensible defaults
- Document all configuration options

### 4. Tool Design
- Keep tools focused and single-purpose
- Use clear, descriptive names
- Provide comprehensive JSON schemas
- Include examples in descriptions

### 5. Testing
- Test agent initialization
- Test tool availability
- Test each tool with various inputs
- Test error conditions

### 6. Documentation
- Document all parameters clearly
- Provide usage examples
- Explain error conditions
- Keep README updated

---

## Troubleshooting

### Common Issues

**1. Agent Not Registering**
```python
# Check logs for registration errors
# Ensure is_available() returns True
# Verify imports are correct
```

**2. Tools Not Appearing**
```python
# Check get_tools() returns non-empty dict
# Verify agent is available
# Check JSON schema validity
```

**3. Tool Calls Failing**
```python
# Check handle_tool_call() method
# Verify parameter validation
# Check external service connectivity
```

**4. Import Errors**
```python
# Ensure all dependencies are installed
# Check file paths and naming
# Verify __init__.py exists in agents/
```

**5. Configuration Issues**
```python
# Check .env file exists and is loaded
# Verify environment variable names match
# Ensure sensitive data is not committed
```

### Debugging Tips

1. **Enable Debug Logging**
```python
logging.basicConfig(level=logging.DEBUG)
```

2. **Test Agent Individually**
```python
# Create standalone test script
# Test without MCP server integration
```

3. **Check Agent Status**
```bash
curl http://localhost:8000/agents/status
```

4. **Validate JSON Schema**
```python
import jsonschema
jsonschema.validate(instance, schema)
```

---

## Next Steps

After successfully adding your agent:

1. **Update Documentation** - Add your agent to the main README
2. **Create Examples** - Add usage examples to guides
3. **Add Tests** - Create unit tests for your agent
4. **Monitor Performance** - Add metrics and monitoring
5. **Share** - Contribute back to the community!

---

## Support

If you encounter issues:

1. Check the logs for error messages
2. Verify your configuration
3. Test individual components
4. Review existing agent implementations
5. Check the MCP specification

The agentic architecture makes it easy to add new capabilities while maintaining clean separation of concerns. Happy coding! 🚀
