import logging
import asyncio
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from agents.base import BaseAgent
from protocol import MCPRequest, MCPResponse
from config import Config

logger = logging.getLogger(__name__)

class OpenAIAgent(BaseAgent):
    """
    OpenAI integration agent for advanced AI capabilities.
    Provides MCP tools for chat, analysis, completion, and summarization.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.client: Optional[AsyncOpenAI] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client if API key is available"""
        if self.config.openai_api_key:
            try:
                self.client = AsyncOpenAI(
                    api_key=self.config.openai_api_key
                )
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("OpenAI API key not provided - OpenAI features disabled")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if OpenAI agent is available"""
        return self.client is not None
    
    def get_tools(self) -> Dict[str, Any]:
        """Define MCP tools provided by this agent"""
        if not self.is_available():
            return {}
        
        return {
            "openai_chat": {
                "description": "Advanced conversational AI using OpenAI GPT models",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string", 
                            "description": "Message for the AI to respond to"
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
                            "description": f"OpenAI model to use (default: {self.config.openai_model})"
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
            "openai_analysis": {
                "description": "Advanced AI-powered text analysis using OpenAI",
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
                            "description": f"OpenAI model to use (default: {self.config.openai_model})"
                        }
                    },
                    "required": ["text"]
                }
            },
            "openai_completion": {
                "description": "Text completion using OpenAI models",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Text prompt to complete"
                        },
                        "model": {
                            "type": "string",
                            "description": f"OpenAI model to use (default: {self.config.openai_model})"
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
            "openai_summarize": {
                "description": "Text summarization using OpenAI",
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
                            "description": f"OpenAI model to use (default: {self.config.openai_model})"
                        }
                    },
                    "required": ["text"]
                }
            }
        }
    
    async def handle_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Handle tool calls for OpenAI agent"""
        if not self.is_available():
            raise ValueError("OpenAI client not available. Please configure OPENAI_API_KEY.")
        
        try:
            if tool_name == "openai_chat":
                return await self._handle_chat(params)
            elif tool_name == "openai_analysis":
                return await self._handle_analysis(params)
            elif tool_name == "openai_completion":
                return await self._handle_completion(params)
            elif tool_name == "openai_summarize":
                return await self._handle_summarization(params)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
                
        except Exception as e:
            logger.error(f"Error in OpenAI tool {tool_name}: {e}")
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
                    "You are an AI assistant integrated with the MCP Agentic Server. "
                    "You can help with various tasks including text analysis, information retrieval, "
                    "data validation, and general conversation. Be helpful and informative."
                )
            }
            messages.insert(0, system_message)
        
        response = await self.client.chat.completions.create(
            model=params.get("model", self.config.openai_model),
            messages=messages,
            max_tokens=params.get("max_tokens", 1000),
            temperature=params.get("temperature", 0.7)
        )
        
        return {
            "content": response.choices[0].message.content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            } if response.usage else None
        }
    
    async def _handle_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text analysis requests"""
        text = params.get("text", "")
        if not text:
            raise ValueError("No text provided for analysis")
        
        analysis_type = params.get("analysis_type", "general")
        
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
        
        response = await self.client.chat.completions.create(
            model=params.get("model", self.config.openai_model),
            messages=[
                {"role": "system", "content": "You are an expert text analyst. Provide clear, structured analysis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.3  # Lower temperature for analysis
        )
        
        return {
            "analysis": response.choices[0].message.content,
            "analysis_type": analysis_type,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            } if response.usage else None
        }
    
    async def _handle_completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text completion requests"""
        prompt = params.get("prompt", "")
        if not prompt:
            raise ValueError("No prompt provided for completion")
        
        response = await self.client.chat.completions.create(
            model=params.get("model", self.config.openai_model),
            messages=[
                {"role": "system", "content": "You are a helpful writing assistant. Complete the given text naturally and coherently."},
                {"role": "user", "content": f"Complete this text: {prompt}"}
            ],
            max_tokens=params.get("max_tokens", 500),
            temperature=params.get("temperature", 0.7)
        )
        
        return {
            "completion": response.choices[0].message.content,
            "prompt": prompt,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            } if response.usage else None
        }
    
    async def _handle_summarization(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text summarization requests"""
        text = params.get("text", "")
        if not text:
            raise ValueError("No text provided for summarization")
        
        length = params.get("length", "medium")
        style = params.get("style", "paragraph")
        
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
        
        response = await self.client.chat.completions.create(
            model=params.get("model", self.config.openai_model),
            messages=[
                {"role": "system", "content": "You are an expert at creating clear, informative summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.3  # Lower temperature for summaries
        )
        
        return {
            "summary": response.choices[0].message.content,
            "length": length,
            "style": style,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            } if response.usage else None
        }
    
    # Legacy method for backward compatibility
    async def handle(self, request: MCPRequest) -> MCPResponse:
        """Legacy handler - converts old-style requests to new tool calls"""
        logger.warning(f"Using legacy handle method in OpenAIAgent for {request.method}")
        
        if not self.is_available():
            return MCPResponse(
                id=request.id,
                error={"message": "OpenAI client not available. Please configure OPENAI_API_KEY."}
            )
        
        try:
            method = request.method
            params = request.params or {}
            
            # Map old methods to new tool calls
            if method == "openai/chat":
                result = await self.handle_tool_call("openai_chat", params)
            elif method == "openai/completion":
                result = await self.handle_tool_call("openai_completion", params)
            elif method == "openai/analyze":
                result = await self.handle_tool_call("openai_analysis", params)
            elif method == "openai/summarize":
                result = await self.handle_tool_call("openai_summarize", params)
            else:
                return MCPResponse(
                    id=request.id,
                    error={"message": f"Unknown OpenAI method: {method}"}
                )
            
            return MCPResponse(id=request.id, result=result)
            
        except Exception as e:
            logger.error(f"Error in OpenAI legacy handler: {e}")
            return MCPResponse(
                id=request.id,
                error={"message": f"OpenAI agent error: {str(e)}"}
            )
