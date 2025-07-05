import logging
import os
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from agents.base import BaseAgent

logger = logging.getLogger(__name__)

class FileAgent(BaseAgent):
    """
    File operations agent providing MCP tools for file management.
    Provides tools for reading, writing, listing, and searching files.
    """
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        logger.info(f"File agent initialized with base path: {self.base_path}")
    
    def is_available(self) -> bool:
        """File agent is always available"""
        return True
    
    def get_tools(self) -> Dict[str, Any]:
        """Define MCP tools provided by this agent"""
        return {
            "file_read": {
                "description": "Read contents of a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file to read"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding (default: utf-8)",
                            "default": "utf-8"
                        }
                    },
                    "required": ["path"]
                }
            },
            "file_write": {
                "description": "Write content to a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file to write"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding (default: utf-8)",
                            "default": "utf-8"
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["write", "append"],
                            "description": "Write mode (default: write)",
                            "default": "write"
                        }
                    },
                    "required": ["path", "content"]
                }
            },
            "file_list": {
                "description": "List files and directories",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path to list (default: current directory)"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "File pattern to match (e.g., '*.py')"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Include subdirectories recursively",
                            "default": False
                        },
                        "show_hidden": {
                            "type": "boolean",
                            "description": "Include hidden files",
                            "default": False
                        }
                    }
                }
            },
            "file_search": {
                "description": "Search for text within files",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Text to search for"
                        },
                        "path": {
                            "type": "string",
                            "description": "Directory to search in (default: current directory)"
                        },
                        "file_pattern": {
                            "type": "string",
                            "description": "File pattern to search in (e.g., '*.py')"
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "Case sensitive search",
                            "default": False
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 100
                        }
                    },
                    "required": ["query"]
                }
            },
            "file_info": {
                "description": "Get information about a file or directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to get information about"
                        }
                    },
                    "required": ["path"]
                }
            },
            "file_create_directory": {
                "description": "Create a new directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path of directory to create"
                        },
                        "parents": {
                            "type": "boolean",
                            "description": "Create parent directories if they don't exist",
                            "default": False
                        }
                    },
                    "required": ["path"]
                }
            }
        }
    
    async def handle_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Handle tool calls for file agent"""
        try:
            if tool_name == "file_read":
                return await self._handle_read(params)
            elif tool_name == "file_write":
                return await self._handle_write(params)
            elif tool_name == "file_list":
                return await self._handle_list(params)
            elif tool_name == "file_search":
                return await self._handle_search(params)
            elif tool_name == "file_info":
                return await self._handle_info(params)
            elif tool_name == "file_create_directory":
                return await self._handle_create_directory(params)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
                
        except Exception as e:
            logger.error(f"Error in file tool {tool_name}: {e}")
            raise
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve and validate file path"""
        resolved_path = Path(path)
        if not resolved_path.is_absolute():
            resolved_path = self.base_path / resolved_path
        return resolved_path.resolve()
    
    async def _handle_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file read requests"""
        file_path = self._resolve_path(params["path"])
        encoding = params.get("encoding", "utf-8")
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        try:
            content = file_path.read_text(encoding=encoding)
            return {
                "content": content,
                "path": str(file_path),
                "size": file_path.stat().st_size,
                "encoding": encoding
            }
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to decode file with encoding {encoding}: {e}")
    
    async def _handle_write(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file write requests"""
        file_path = self._resolve_path(params["path"])
        content = params["content"]
        encoding = params.get("encoding", "utf-8")
        mode = params.get("mode", "write")
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if mode == "append":
                with file_path.open("a", encoding=encoding) as f:
                    f.write(content)
            else:  # write mode
                file_path.write_text(content, encoding=encoding)
            
            return {
                "path": str(file_path),
                "size": file_path.stat().st_size,
                "mode": mode,
                "encoding": encoding
            }
        except Exception as e:
            raise ValueError(f"Failed to write file: {e}")
    
    async def _handle_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle directory listing requests"""
        dir_path = self._resolve_path(params.get("path", "."))
        pattern = params.get("pattern", "*")
        recursive = params.get("recursive", False)
        show_hidden = params.get("show_hidden", False)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        if not dir_path.is_dir():
            raise ValueError(f"Path is not a directory: {dir_path}")
        
        files = []
        directories = []
        
        if recursive:
            glob_pattern = f"**/{pattern}" if pattern != "*" else "**/*"
            paths = dir_path.rglob(pattern)
        else:
            paths = dir_path.glob(pattern)
        
        for path in paths:
            if not show_hidden and path.name.startswith('.'):
                continue
            
            stat_info = path.stat()
            item_info = {
                "name": path.name,
                "path": str(path.relative_to(dir_path)),
                "absolute_path": str(path),
                "size": stat_info.st_size,
                "modified": stat_info.st_mtime,
                "is_directory": path.is_dir(),
                "is_file": path.is_file()
            }
            
            if path.is_dir():
                directories.append(item_info)
            else:
                files.append(item_info)
        
        return {
            "directory": str(dir_path),
            "files": sorted(files, key=lambda x: x["name"]),
            "directories": sorted(directories, key=lambda x: x["name"]),
            "total_files": len(files),
            "total_directories": len(directories)
        }
    
    async def _handle_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file search requests"""
        query = params["query"]
        search_path = self._resolve_path(params.get("path", "."))
        file_pattern = params.get("file_pattern", "*")
        case_sensitive = params.get("case_sensitive", False)
        max_results = params.get("max_results", 100)
        
        if not search_path.exists():
            raise FileNotFoundError(f"Search path not found: {search_path}")
        
        if not search_path.is_dir():
            raise ValueError(f"Search path is not a directory: {search_path}")
        
        results = []
        search_query = query if case_sensitive else query.lower()
        
        for file_path in search_path.rglob(file_pattern):
            if not file_path.is_file():
                continue
            
            try:
                content = file_path.read_text(encoding="utf-8")
                search_content = content if case_sensitive else content.lower()
                
                if search_query in search_content:
                    lines = content.split('\n')
                    matching_lines = []
                    
                    for line_num, line in enumerate(lines, 1):
                        search_line = line if case_sensitive else line.lower()
                        if search_query in search_line:
                            matching_lines.append({
                                "line_number": line_num,
                                "line": line.strip(),
                                "match_position": search_line.find(search_query)
                            })
                    
                    results.append({
                        "file": str(file_path.relative_to(search_path)),
                        "absolute_path": str(file_path),
                        "matches": len(matching_lines),
                        "matching_lines": matching_lines[:10]  # Limit to first 10 matches per file
                    })
                
                if len(results) >= max_results:
                    break
                    
            except (UnicodeDecodeError, PermissionError):
                # Skip files that can't be read
                continue
        
        return {
            "query": query,
            "search_path": str(search_path),
            "file_pattern": file_pattern,
            "case_sensitive": case_sensitive,
            "total_matches": len(results),
            "results": results
        }
    
    async def _handle_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file/directory info requests"""
        file_path = self._resolve_path(params["path"])
        
        if not file_path.exists():
            raise FileNotFoundError(f"Path not found: {file_path}")
        
        stat_info = file_path.stat()
        
        info = {
            "path": str(file_path),
            "name": file_path.name,
            "parent": str(file_path.parent),
            "exists": True,
            "is_file": file_path.is_file(),
            "is_directory": file_path.is_dir(),
            "is_symlink": file_path.is_symlink(),
            "size": stat_info.st_size,
            "created": stat_info.st_ctime,
            "modified": stat_info.st_mtime,
            "permissions": oct(stat_info.st_mode)[-3:]
        }
        
        if file_path.is_file():
            info["extension"] = file_path.suffix
            try:
                # Try to detect if it's a text file
                sample = file_path.read_bytes()[:1024]
                info["is_text"] = all(byte < 128 or byte in [0x09, 0x0A, 0x0D] for byte in sample)
            except:
                info["is_text"] = False
        
        return info
    
    async def _handle_create_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle directory creation requests"""
        dir_path = self._resolve_path(params["path"])
        parents = params.get("parents", False)
        
        if dir_path.exists():
            if dir_path.is_dir():
                return {
                    "path": str(dir_path),
                    "created": False,
                    "message": "Directory already exists"
                }
            else:
                raise ValueError(f"Path exists but is not a directory: {dir_path}")
        
        try:
            dir_path.mkdir(parents=parents, exist_ok=False)
            return {
                "path": str(dir_path),
                "created": True,
                "parents": parents
            }
        except FileNotFoundError:
            raise ValueError(f"Parent directory doesn't exist. Use parents=True to create parent directories.")
        except Exception as e:
            raise ValueError(f"Failed to create directory: {e}")
