import logging
import asyncio
from typing import Optional, Dict, Any
from agents.base import BaseAgent
from protocol import MCPRequest, MCPResponse
from config import Config

logger = logging.getLogger(__name__)

class OllamaAgent(BaseAgent):
    """
    Ollama integration agent for local AI capabilities.
    Provides MCP tools for local chat, analysis, and completion.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.client = None
        self.model = config.ollama_model or "llama3.2:latest"
        self.base_url = getattr(config, 'ollama_url', 'http://localhost:11434')
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Ollama client if service is available"""
        try:
            import ollama
            # Test connection by trying to list models
            try:
                models_response = ollama.list()
                logger.info(f"Ollama connection successful")
                
                # Check if our target model is available
                available_models = []
                if hasattr(models_response, 'models') and models_response.models:
                    for model in models_response.models:
                        if hasattr(model, 'model'):
                            available_models.append(model.model)
                        elif hasattr(model, 'name'):
                            available_models.append(model.name)
                        elif isinstance(model, dict) and 'model' in model:
                            available_models.append(model['model'])
                        elif isinstance(model, dict) and 'name' in model:
                            available_models.append(model['name'])
                        elif isinstance(model, str):
                            available_models.append(model)
                
                logger.info(f"Available models: {available_models}")
                
                # Check if our model is available, try to find a compatible one
                model_found = False
                for available_model in available_models:
                    if self.model in available_model or available_model.startswith(self.model.split(':')[0]):
                        self.model = available_model
                        model_found = True
                        break
                
                if model_found or self.model in available_models:
                    self.client = ollama
                    logger.info(f"Ollama client initialized with model: {self.model}")
                else:
                    logger.warning(f"Model {self.model} not available. Available models: {available_models}")
                    # Try with the first available model if any
                    if available_models:
                        self.model = available_models[0]
                        self.client = ollama
                        logger.info(f"Using fallback model: {self.model}")
                    else:
                        logger.error("No Ollama models available")
                        self.client = None
                        
            except Exception as e:
                logger.error(f"Failed to initialize Ollama client: {e}")
                self.client = None
                
        except ImportError:
            logger.warning("Ollama package not available - install with: pip install ollama")
            self.client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing Ollama: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Ollama agent is available"""
        return self.client is not None
    
    def get_tools(self) -> Dict[str, Any]:
        """Define MCP tools provided by this agent"""
        if not self.is_available():
            return {}
        
        return {
            "ollama_chat": {
                "description": f"Local conversational AI using Ollama ({self.model})",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string", 
                            "description": "Message for the local AI to respond to"
                        },
                        "messages": {
                            "type": "array",
                            "description": "Array of chat messages (alternative to single message)",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {"type": "string", "enum": ["user", "assistant", "system"]},
                                    "content": {"type": "string"}
                                },
                                "required": ["role", "content"]
                            }
                        },
                        "model": {
                            "type": "string", 
                            "description": f"Ollama model to use (default: {self.model})"
                        },
                        "temperature": {
                            "type": "number", 
                            "description": "Response creativity (0-1, default: 0.7)",
                            "minimum": 0,
                            "maximum": 1
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens in response (default: 1000)",
                            "minimum": 1,
                            "maximum": 4000
                        }
                    }
                }
            },
            "ollama_analysis": {
                "description": f"Local AI-powered text analysis using Ollama ({self.model})",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string", 
                            "description": "Text to analyze"
                        },
                        "analysis_type": {
                            "type": "string",
                            "enum": ["sentiment", "summary", "keywords", "general", "classification"],
                            "description": "Type of analysis to perform (default: general)"
                        },
                        "model": {
                            "type": "string",
                            "description": f"Ollama model to use (default: {self.model})"
                        }
                    },
                    "required": ["text"]
                }
            },
            "ollama_completion": {
                "description": f"Text completion using local Ollama model ({self.model})",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Text prompt to complete"
                        },
                        "model": {
                            "type": "string",
                            "description": f"Ollama model to use (default: {self.model})"
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens in completion (default: 500)",
                            "minimum": 1,
                            "maximum": 2000
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Response creativity (0-1, default: 0.7)",
                            "minimum": 0,
                            "maximum": 1
                        }
                    },
                    "required": ["prompt"]
                }
            },
            "ollama_summarize": {
                "description": f"Text summarization using local Ollama model ({self.model})",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to summarize"
                        },
                        "length": {
                            "type": "string",
                            "enum": ["short", "medium", "long"],
                            "description": "Desired summary length (default: medium)"
                        },
                        "style": {
                            "type": "string",
                            "enum": ["bullet_points", "paragraph", "abstract"],
                            "description": "Summary style (default: paragraph)"
                        },
                        "model": {
                            "type": "string",
                            "description": f"Ollama model to use (default: {self.model})"
                        }
                    },
                    "required": ["text"]
                }
            }
        }
    
    async def handle_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Handle tool calls for Ollama agent"""
        if not self.is_available():
            raise ValueError("Ollama client not available. Please ensure Ollama is running and models are installed.")
        
        try:
            if tool_name == "ollama_chat":
                return await self._handle_chat(params)
            elif tool_name == "ollama_analysis":
                return await self._handle_analysis(params)
            elif tool_name == "ollama_completion":
                return await self._handle_completion(params)
            elif tool_name == "ollama_summarize":
                return await self._handle_summarization(params)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
                
        except Exception as e:
            logger.error(f"Error in Ollama tool {tool_name}: {e}")
            raise
    
    async def _handle_chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat completion requests"""
        messages = params.get("messages", [])
        if not messages:
            # Convert single message to chat format
            user_message = params.get("message", "")
            if user_message:
                messages = [{"role": "user", "content": user_message}]
            else:
                raise ValueError("No messages provided")
        
        # Add system message if not present
        if not any(msg.get("role") == "system" for msg in messages):
            system_message = {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant running locally via Ollama. "
                    "You can help with various tasks including text analysis, information retrieval, "
                    "data validation, and general conversation. Be helpful and informative."
                )
            }
            messages.insert(0, system_message)
        
        model = params.get("model", self.model)
        
        try:
            response = await asyncio.to_thread(
                self.client.chat,
                model=model,
                messages=messages,
                options={
                    "temperature": params.get("temperature", 0.7),
                    "num_predict": params.get("max_tokens", 1000),
                }
            )
            
            return {
                "content": response.get("message", {}).get("content", ""),
                "model": model,
                "done": response.get("done", True),
                "total_duration": response.get("total_duration"),
                "prompt_eval_count": response.get("prompt_eval_count"),
                "eval_count": response.get("eval_count")
            }
            
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise ValueError(f"Chat completion failed: {str(e)}")
    
    async def _handle_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text analysis requests"""
        text = params.get("text", "")
        if not text:
            raise ValueError("No text provided for analysis")
        
        analysis_type = params.get("analysis_type", "general")
        model = params.get("model", self.model)
        
        # Create appropriate prompt based on analysis type
        if analysis_type == "sentiment":
            prompt = f"Analyze the sentiment of the following text. Provide a clear sentiment classification (positive, negative, neutral) and confidence score:\n\n{text}"
        elif analysis_type == "summary":
            prompt = f"Provide a concise summary of the following text:\n\n{text}"
        elif analysis_type == "keywords":
            prompt = f"Extract the key topics, themes, and important keywords from the following text:\n\n{text}"
        elif analysis_type == "classification":
            prompt = f"Classify the following text by category, genre, or type. Explain your classification:\n\n{text}"
        else:  # general
            prompt = f"Perform a comprehensive analysis of the following text, including sentiment, key themes, and important insights:\n\n{text}"
        
        try:
            response = await asyncio.to_thread(
                self.client.generate,
                model=model,
                prompt=prompt,
                options={
                    "temperature": 0.3,  # Lower temperature for analysis
                    "num_predict": 800,
                }
            )
            
            return {
                "analysis": response.get("response", ""),
                "analysis_type": analysis_type,
                "model": model,
                "done": response.get("done", True),
                "total_duration": response.get("total_duration"),
                "prompt_eval_count": response.get("prompt_eval_count"),
                "eval_count": response.get("eval_count")
            }
            
        except Exception as e:
            logger.error(f"Ollama analysis error: {e}")
            raise ValueError(f"Analysis failed: {str(e)}")
    
    async def _handle_completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text completion requests"""
        prompt = params.get("prompt", "")
        if not prompt:
            raise ValueError("No prompt provided for completion")
        
        model = params.get("model", self.model)
        
        try:
            response = await asyncio.to_thread(
                self.client.generate,
                model=model,
                prompt=f"Complete this text naturally and coherently: {prompt}",
                options={
                    "temperature": params.get("temperature", 0.7),
                    "num_predict": params.get("max_tokens", 500),
                }
            )
            
            return {
                "completion": response.get("response", ""),
                "prompt": prompt,
                "model": model,
                "done": response.get("done", True),
                "total_duration": response.get("total_duration"),
                "prompt_eval_count": response.get("prompt_eval_count"),
                "eval_count": response.get("eval_count")
            }
            
        except Exception as e:
            logger.error(f"Ollama completion error: {e}")
            raise ValueError(f"Completion failed: {str(e)}")
    
    async def _handle_summarization(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text summarization requests"""
        text = params.get("text", "")
        if not text:
            raise ValueError("No text provided for summarization")
        
        length = params.get("length", "medium")
        style = params.get("style", "paragraph")
        model = params.get("model", self.model)
        
        # Create appropriate prompt based on parameters
        length_instructions = {
            "short": "in 2-3 sentences",
            "medium": "in 1-2 paragraphs", 
            "long": "in 3-4 paragraphs with detailed key points"
        }
        
        style_instructions = {
            "bullet_points": "using bullet points",
            "paragraph": "in paragraph form",
            "abstract": "as an academic abstract"
        }
        
        prompt = f"Summarize the following text {length_instructions.get(length, 'concisely')} {style_instructions.get(style, '')}:\n\n{text}"
        
        try:
            response = await asyncio.to_thread(
                self.client.generate,
                model=model,
                prompt=prompt,
                options={
                    "temperature": 0.3,  # Lower temperature for summaries
                    "num_predict": 600,
                }
            )
            
            return {
                "summary": response.get("response", ""),
                "length": length,
                "style": style,
                "model": model,
                "done": response.get("done", True),
                "total_duration": response.get("total_duration"),
                "prompt_eval_count": response.get("prompt_eval_count"),
                "eval_count": response.get("eval_count")
            }
            
        except Exception as e:
            logger.error(f"Ollama summarization error: {e}")
            raise ValueError(f"Summarization failed: {str(e)}")
    
    # Legacy method for backward compatibility
    async def handle(self, request: MCPRequest) -> MCPResponse:
        """Legacy handler - converts old-style requests to new tool calls"""
        logger.warning(f"Using legacy handle method in OllamaAgent for {request.method}")
        
        if not self.is_available():
            return MCPResponse(
                id=request.id,
                error={"message": "Ollama client not available. Please ensure Ollama is running."}
            )
        
        try:
            method = request.method
            params = request.params or {}
            
            # Map old methods to new tool calls
            if method == "ollama/chat":
                result = await self.handle_tool_call("ollama_chat", params)
            elif method == "ollama/completion":
                result = await self.handle_tool_call("ollama_completion", params)
            elif method == "ollama/analyze":
                result = await self.handle_tool_call("ollama_analysis", params)
            elif method == "ollama/summarize":
                result = await self.handle_tool_call("ollama_summarize", params)
            else:
                return MCPResponse(
                    id=request.id,
                    error={"message": f"Unknown Ollama method: {method}"}
                )
            
            return MCPResponse(id=request.id, result=result)
            
        except Exception as e:
            logger.error(f"Error in Ollama legacy handler: {e}")
            return MCPResponse(
                id=request.id,
                error={"message": f"Ollama agent error: {str(e)}"}
            )
