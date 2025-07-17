from mcp.server.fastmcp import FastMCP
from src.tools import register_tools
import uvicorn
import os

def create_app() -> FastMCP:
    """Create and configure the MCP server"""
    mcp = FastMCP("GitHubManager")
    register_tools(mcp)
    return mcp

app = create_app()

def main():
    """Main entry point for local development"""
    print("📡 GitHubManager MCP server starting...")
    
    # Check if we're running in a deployment environment
    if os.environ.get("RENDER") or os.environ.get("RAILWAY") or os.environ.get("VERCEL"):
        # In deployment, don't run the server here - let the deployment handle it
        print("🚀 Running in deployment environment")
        return
    
    # For local development, you can choose between stdio and HTTP
    run_mode = os.environ.get("RUN_MODE", "stdio")
    
    if run_mode == "http":
        # Run as HTTP server for local testing
        port = int(os.environ.get("PORT", 8000))
        print(f"🌐 Starting HTTP server on port {port}")
        uvicorn.run(app.streamable_http_app(), host="0.0.0.0", port=port)
    else:
        # Default: run as stdio MCP server for Claude Desktop
        print("💬 Starting stdio MCP server for Claude Desktop")
        app.run()
    
    print("🚧 GitHubManager has shut down.")

if __name__ == "__main__":
    main()