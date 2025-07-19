from mcp.server.fastmcp import FastMCP
from fastapi import Request
from fastapi_sso.sso.github import GithubSSO
from fastapi.responses import JSONResponse
from src.tools import register_tools
import contextlib
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_CLIENT_ID = os.environ["GITHUB_CLIENT_ID"]
GITHUB_CLIENT_SECRET = os.environ["GITHUB_CLIENT_SECRET"]
REDIRECT_URI = os.environ.get("GITHUB_REDIRECT_URI",
                    "https://github-mcp-server-jeib.onrender.com/auth/callback")

sso = GithubSSO(
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=["repo", "user"],
    allow_insecure_http=False
)

def create_app() -> FastMCP:
    """Create and configure the MCP server with FastAPI routes"""
    
    # Create a lifespan manager for the session
    @contextlib.asynccontextmanager
    async def lifespan(app):
        async with mcp.session_manager.run():
            yield
    
    mcp = FastMCP(
        name="GitHubManager",
        title="GitHub MCP Server",
        description="A Model Context Protocol server for GitHub operations",
        version="1.0.0",
        lifespan=lifespan
    )
    
    register_tools(mcp)
    
    @mcp.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "GitHubManager MCP Server"}

    @mcp.get("/debug")
    async def debug_env():
        """Debug endpoint to check environment variables"""
        github_token = os.environ.get("GITHUB_TOKEN")
        
        return {
            "github_token_exists": bool(github_token),
            "github_token_length": len(github_token) if github_token else 0,
            "github_token_prefix": github_token[:4] + "..." if github_token and len(github_token) > 4 else None,
            "port": os.environ.get("PORT", "10000"),
            "env_vars_count": len(os.environ),
            "all_env_vars": list(os.environ.keys())
        }

    @mcp.get("/auth/login")
    async def login_redirect():
        """Start GitHub OAuth flow."""
        async with sso:
            return await sso.get_login_redirect()

    @mcp.get("/auth/callback")
    async def auth_callback(request: Request):
        """Handle GitHub OAuth callback."""
        async with sso:
            try:
                user = await sso.verify_and_process(request)
                _token = sso.access_token
            except Exception as e:
                import traceback
                traceback.print_exc()
                return JSONResponse(
                    status_code=400,
                    content={"error": str(e)}
                )
        
        return {
            "msg": "Auth successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.display_name,
            },
            "obj": user,
            "_token": _token
        }
    
    return mcp

# Create the app instance
app = create_app()

def main():
    """Main entry point"""
    print("📡 GitHubManager MCP server starting...")
    
    # Check if we're running in a deployment environment
    if os.environ.get("RENDER") or os.environ.get("RAILWAY") or os.environ.get("VERCEL"):
        print("🚀 Running in deployment environment")
        # For deployment, run the HTTP server
        port = int(os.environ.get("PORT", 10000))
        print(f"🌐 Starting HTTP server on port {port}")
        uvicorn.run(app.streamable_http_app(), host="0.0.0.0", port=port)
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

asgi_app = app.streamable_http_app()

if __name__ == "__main__":
    main()