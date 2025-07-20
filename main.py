from mcp.server.fastmcp import FastMCP
from src.tools import register_tools

def create_app():
    """Create and configure the MCP server"""
    mcp = FastMCP("GitHubManager")
    register_tools(mcp)
    return mcp

app = create_app()

def main():
    """Main entry point"""
    print("📡 GitHubManager MCP server starting...")
    app.run()
    print("🚧 GitHubManager has shut down.")

if __name__ == "__main__":
    main()