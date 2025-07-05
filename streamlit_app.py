"""
Streamlit App for Pure Agentic MCP Server
Clean interface for interacting with all MCP tools via HTTP
"""
import streamlit as st
import asyncio
import httpx
import json
import logging
from typing import Optional, Dict, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_SERVER_URL = "http://localhost:8000"

async def get_server_status(server_url: str = DEFAULT_SERVER_URL) -> Dict:
    """Get server status and available tools"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try ping first
            ping_response = await client.get(f"{server_url}/ping")
            ping_response.raise_for_status()
            
            # Get tools list
            tools_response = await client.get(f"{server_url}/tools")
            tools_response.raise_for_status()
            
            # Get agent status
            status_response = await client.get(f"{server_url}/agent/status")
            status_response.raise_for_status()
            
            return {
                "healthy": True,
                "ping": ping_response.json(),
                "tools": tools_response.json(),
                "agents": status_response.json()
            }
    except Exception as e:
        logger.error(f"Error getting server status: {e}")
        return {"healthy": False, "error": str(e)}

async def call_tool(tool_name: str, arguments: Dict, server_url: str = DEFAULT_SERVER_URL) -> Dict:
    """Call a specific MCP tool"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "tool_name": tool_name,
                "arguments": arguments
            }
            
            response = await client.post(f"{server_url}/tools/call", json=payload)
            response.raise_for_status()
            return response.json()
            
    except httpx.ConnectError:
        return {"status": "error", "message": "Cannot connect to server. Start with: python simple_mcp_host.py"}
    except httpx.TimeoutException:
        return {"status": "error", "message": "Request timed out. Please try again."}
    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {e}")
        return {"status": "error", "message": str(e)}

async def chat_with_ai(message: str, agent: str, server_url: str = DEFAULT_SERVER_URL) -> str:
    """Chat with AI agents (OpenAI or Ollama)"""
    tool_name = f"{agent}_chat"
    arguments = {"message": message}
    
    result = await call_tool(tool_name, arguments, server_url)
    
    if result.get("status") == "success":
        response_data = result.get("result", {})
        if isinstance(response_data, dict):
            content = response_data.get("content", "")
            model = response_data.get("model", agent)
            return f"{content}\n\n_({model})_"
        return str(response_data)
    else:
        return f"❌ Error: {result.get('message', 'Unknown error')}"

async def analyze_text(text: str, analysis_type: str = "general", server_url: str = DEFAULT_SERVER_URL) -> str:
    """Analyze text using available AI tools"""
    try:
        # Try the smart analyze endpoint first
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "text": text,
                "analysis_type": analysis_type
            }
            
            response = await client.post(f"{server_url}/analyze", json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") == "success":
                analysis_data = result.get("result", {})
                if isinstance(analysis_data, dict):
                    analysis = analysis_data.get("analysis", "")
                    used_tool = result.get("used_tool", "unknown")
                    return f"{analysis}\n\n_Analysis by: {used_tool}_"
                return str(analysis_data)
            else:
                return f"❌ Analysis Error: {result.get('message', 'Unknown error')}"
                
    except Exception as e:
        return f"❌ Analysis failed: {str(e)}"

# Streamlit UI Configuration
st.set_page_config(
    page_title="Agentic MCP Server",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 Pure Agentic MCP Server")
st.markdown("**Clean interface for interacting with MCP tools organized by intelligent agents**")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Server URL
    server_url = st.text_input("Server URL:", value=DEFAULT_SERVER_URL)
    
    # Check server status
    if st.button("🔍 Check Server Status"):
        with st.spinner("Checking server..."):
            status = asyncio.run(get_server_status(server_url))
            
            if status.get("healthy"):
                st.success("✅ Server is running")
                
                # Show agent status
                agent_status = status.get("agents", {}).get("agent_status", {})
                if agent_status:
                    st.subheader("🤖 Agents")
                    for agent_name, info in agent_status.get("agents", {}).items():
                        icon = "🟢" if info.get("available") else "🔴"
                        tool_count = info.get("tool_count", 0)
                        st.write(f"{icon} **{agent_name.title()}**: {tool_count} tools")
                
                # Show available tools
                tools_data = status.get("tools", {})
                if tools_data.get("tools"):
                    st.subheader("🔧 Available Tools")
                    tools = tools_data["tools"]
                    st.write(f"Total: {len(tools)} tools")
                    
                    # Group tools by agent
                    tool_groups = {}
                    for tool in tools:
                        tool_name = tool["name"]
                        agent_name = tool_name.split("_")[0]
                        if agent_name not in tool_groups:
                            tool_groups[agent_name] = []
                        tool_groups[agent_name].append(tool_name)
                    
                    for agent, agent_tools in tool_groups.items():
                        st.write(f"**{agent.title()}**: {', '.join(agent_tools)}")
            else:
                st.error("❌ Server not responding")
                st.info("Start server with: `python simple_mcp_host.py`")
                if status.get("error"):
                    st.error(f"Error: {status['error']}")

# Main Interface Tabs
tab1, tab2, tab3, tab4 = st.tabs(["💬 AI Chat", "📄 Text Analysis", "📁 File Operations", "🔧 Raw Tool Calls"])

# Tab 1: AI Chat
with tab1:
    st.header("💬 Chat with AI Agents")
    
    # Agent selection
    col1, col2 = st.columns([3, 1])
    with col1:
        agent = st.selectbox(
            "Select AI Agent:",
            ["openai", "ollama"],
            format_func=lambda x: {"openai": "🌐 OpenAI (Cloud)", "ollama": "🏠 Ollama (Local)"}[x]
        )
    
    with col2:
        if st.button("🔄 Test Agent"):
            with st.spinner(f"Testing {agent}..."):
                test_result = asyncio.run(chat_with_ai("Hello! Just testing the connection.", agent, server_url))
                st.text_area("Test Result:", test_result, height=100)
    
    # Chat interface
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Chat input
    user_message = st.text_input("Your message:", placeholder=f"Ask {agent} anything...")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📨 Send Message", disabled=not user_message.strip()):
            if user_message.strip():
                with st.spinner(f"🤔 {agent.title()} is thinking..."):
                    response = asyncio.run(chat_with_ai(user_message, agent, server_url))
                    
                    st.session_state.chat_history.append({
                        "user": user_message,
                        "agent": agent,
                        "response": response
                    })
    
    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
    
    # Display chat history
    if st.session_state.chat_history:
        st.subheader("📜 Chat History")
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            with st.expander(f"💬 {chat['agent'].title()}: {chat['user'][:50]}..."):
                st.markdown(f"**👤 You:** {chat['user']}")
                st.markdown(f"**🤖 {chat['agent'].title()}:**")
                st.markdown(chat['response'])

# Tab 2: Text Analysis
with tab2:
    st.header("📄 Intelligent Text Analysis")
    
    # Analysis input
    text_to_analyze = st.text_area(
        "Text to analyze:",
        placeholder="Enter text for AI-powered analysis...",
        height=150
    )
    
    analysis_type = st.selectbox(
        "Analysis Type:",
        ["general", "sentiment", "summary", "keywords", "classification"],
        format_func=lambda x: x.title()
    )
    
    if st.button("🔍 Analyze Text", disabled=not text_to_analyze.strip()):
        if text_to_analyze.strip():
            with st.spinner("🧠 Analyzing text..."):
                analysis = asyncio.run(analyze_text(text_to_analyze, analysis_type, server_url))
                st.subheader("📊 Analysis Result")
                st.markdown(analysis)

# Tab 3: File Operations
with tab3:
    st.header("📁 File System Operations")
    
    # File operation selector
    operation = st.selectbox(
        "Select Operation:",
        ["list", "read", "info", "search"],
        format_func=lambda x: {
            "list": "📋 List Files",
            "read": "📖 Read File", 
            "info": "ℹ️ File Info",
            "search": "🔍 Search Files"
        }[x]
    )
    
    if operation == "list":
        col1, col2 = st.columns(2)
        with col1:
            path = st.text_input("Directory path:", value=".")
            pattern = st.text_input("File pattern:", value="*", help="e.g., *.py, *.txt")
        with col2:
            recursive = st.checkbox("Recursive", value=False)
            show_hidden = st.checkbox("Show hidden files", value=False)
        
        if st.button("📋 List Files"):
            with st.spinner("📁 Reading directory..."):
                result = asyncio.run(call_tool("file_list", {
                    "path": path,
                    "pattern": pattern,
                    "recursive": recursive,
                    "show_hidden": show_hidden
                }, server_url))
                
                if result.get("status") == "success":
                    file_data = result["result"]
                    st.success(f"Found {file_data.get('total_files', 0)} files, {file_data.get('total_directories', 0)} directories")
                    
                    # Show directories
                    if file_data.get("directories"):
                        st.subheader("📁 Directories")
                        for dir_info in file_data["directories"][:10]:  # Limit display
                            st.write(f"📁 {dir_info['name']}")
                    
                    # Show files
                    if file_data.get("files"):
                        st.subheader("📄 Files")
                        for file_info in file_data["files"][:20]:  # Limit display
                            size_kb = file_info["size"] / 1024
                            st.write(f"📄 {file_info['name']} ({size_kb:.1f} KB)")
                else:
                    st.error(f"Error: {result.get('message', 'Unknown error')}")
    
    elif operation == "read":
        file_path = st.text_input("File path:", placeholder="path/to/file.txt")
        
        if st.button("📖 Read File") and file_path:
            with st.spinner("📖 Reading file..."):
                result = asyncio.run(call_tool("file_read", {"path": file_path}, server_url))
                
                if result.get("status") == "success":
                    file_data = result["result"]
                    st.success(f"File size: {file_data.get('size', 0)} bytes")
                    st.text_area("File content:", file_data.get("content", ""), height=300)
                else:
                    st.error(f"Error: {result.get('message', 'Unknown error')}")
    
    elif operation == "info":
        file_path = st.text_input("Path:", placeholder="path/to/file_or_directory")
        
        if st.button("ℹ️ Get Info") and file_path:
            with st.spinner("ℹ️ Getting file info..."):
                result = asyncio.run(call_tool("file_info", {"path": file_path}, server_url))
                
                if result.get("status") == "success":
                    info = result["result"]
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Name:** {info.get('name', 'Unknown')}")
                        st.write(f"**Type:** {'Directory' if info.get('is_directory') else 'File'}")
                        st.write(f"**Size:** {info.get('size', 0)} bytes")
                    
                    with col2:
                        st.write(f"**Exists:** {info.get('exists', False)}")
                        st.write(f"**Permissions:** {info.get('permissions', 'Unknown')}")
                        if info.get('extension'):
                            st.write(f"**Extension:** {info['extension']}")
                else:
                    st.error(f"Error: {result.get('message', 'Unknown error')}")

# Tab 4: Raw Tool Calls
with tab4:
    st.header("🔧 Raw MCP Tool Interface")
    st.markdown("Direct access to all MCP tools for advanced users")
    
    # Get available tools for dropdown
    if st.button("🔄 Refresh Tools"):
        with st.spinner("Getting available tools..."):
            status = asyncio.run(get_server_status(server_url))
            if status.get("healthy"):
                tools_data = status.get("tools", {})
                st.session_state.available_tools = tools_data.get("tools", [])
            else:
                st.error("Cannot get tools - server not responding")
    
    if "available_tools" not in st.session_state:
        st.session_state.available_tools = []
    
    if st.session_state.available_tools:
        # Tool selection
        tool_names = [tool["name"] for tool in st.session_state.available_tools]
        selected_tool = st.selectbox("Select Tool:", tool_names)
        
        # Show tool info
        if selected_tool:
            tool_info = next((tool for tool in st.session_state.available_tools if tool["name"] == selected_tool), None)
            if tool_info:
                st.subheader(f"🔧 {selected_tool}")
                st.write(f"**Description:** {tool_info.get('description', 'No description')}")
                
                # Show schema
                schema = tool_info.get("inputSchema", {})
                if schema.get("properties"):
                    st.write("**Parameters:**")
                    for prop_name, prop_info in schema["properties"].items():
                        required = "✓" if prop_name in schema.get("required", []) else " "
                        st.write(f"- `{prop_name}` ({prop_info.get('type', 'unknown')}) {required} - {prop_info.get('description', '')}")
        
        # Arguments input
        st.subheader("📝 Tool Arguments")
        arguments_json = st.text_area(
            "Arguments (JSON):",
            placeholder='{"param1": "value1", "param2": "value2"}',
            height=100
        )
        
        # Call tool
        if st.button("⚡ Execute Tool"):
            if selected_tool and arguments_json:
                try:
                    arguments = json.loads(arguments_json) if arguments_json.strip() else {}
                    
                    with st.spinner(f"⚡ Executing {selected_tool}..."):
                        result = asyncio.run(call_tool(selected_tool, arguments, server_url))
                        
                        st.subheader("📊 Result")
                        if result.get("status") == "success":
                            st.success("✅ Tool executed successfully")
                            st.json(result.get("result", {}))
                        else:
                            st.error(f"❌ Tool execution failed: {result.get('message', 'Unknown error')}")
                            
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON in arguments")
            else:
                st.warning("⚠️ Please select a tool and provide arguments")
    else:
        st.info("📡 Click 'Refresh Tools' to load available tools")

# Footer
st.markdown("---")
st.markdown("""
**Pure Agentic MCP Server** - Intelligent tool organization through domain experts  
🤖 **AI Agents**: OpenAI (cloud) and Ollama (local)  
📁 **File Agent**: Complete file system operations  
🔧 **Raw Tools**: Direct MCP tool access  
""")
