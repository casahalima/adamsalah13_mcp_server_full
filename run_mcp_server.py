#!/usr/bin/env python3
"""
MCP Server executable script for Claude Desktop
This script activates the virtual environment and runs the MCP server
"""
import sys
import os
from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).parent.absolute()

# Add the script directory to Python path
sys.path.insert(0, str(script_dir))

# Activate virtual environment if it exists
venv_path = script_dir / ".venv"
if venv_path.exists():
    if os.name == 'nt':  # Windows
        activate_script = venv_path / "Scripts" / "activate_this.py"
        if activate_script.exists():
            exec(open(activate_script).read(), {'__file__': str(activate_script)})
    else:  # Unix/Linux/Mac
        activate_script = venv_path / "bin" / "activate_this.py"
        if activate_script.exists():
            exec(open(activate_script).read(), {'__file__': str(activate_script)})

# Import and run the Pure Agentic MCP server
if __name__ == "__main__":
    from pure_mcp_server import main
    import asyncio
    asyncio.run(main())
