from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Config(BaseSettings):
    # Database configuration
    neo4j_uri: Optional[str] = Field(default="bolt://localhost:7687")
    neo4j_user: Optional[str] = Field(default="neo4j")
    neo4j_password: Optional[str] = Field(default=None)  # Set via .env file
    
    # Local AI model configuration
    ollama_url: str = Field(default="http://localhost:11434")
    ollama_model: Optional[str] = Field(default="llama3.2:latest")
    
    # OpenAI configuration
    openai_api_key: Optional[str] = Field(default=None)  # Set via .env file
    openai_model: str = Field(default="gpt-4")
    openai_base_url: Optional[str] = Field(default="https://api.openai.com/v1")
    
    # MCP server configuration
    mcp_server_name: str = Field(default="MCP Agentic Server")
    mcp_server_version: str = Field(default="1.0.0")
    
    # Additional configuration for compatibility
    server_host: str = Field(default="localhost")
    server_port: int = Field(default=8000)
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    # File Operations
    file_max_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    file_allowed_extensions: str = Field(default=".txt,.py,.js,.json,.md,.csv,.log")

    class Config:
        env_file = ".env"
    
    @property
    def allowed_extensions(self):
        return [ext.strip() for ext in self.file_allowed_extensions.split(",")]
