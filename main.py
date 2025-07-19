from mcp.server.fastmcp import FastMCP, Context
from fastapi import Request
from fastapi_sso.sso.github import GithubSSO
from fastapi.responses import JSONResponse
from starlette.requests import Request as StarletteRequest
from starlette.responses import JSONResponse as StarletteJSONResponse
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions, RevocationOptions
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
        name="GitHubMCP",
        lifespan=lifespan,
        auth_provider=sso,
        auth=AuthSettings(
            issuer_url=os.environ["ROOT_URL"],
            resource_server_url=os.environ["ROOT_URL"],
            required_scopes=["repo", "user"],
            client_registration_options=ClientRegistrationOptions(
                enabled=True,
                valid_scopes=["repo", "user"],
                default_scopes=["repo", "user"],
            ),
            revocation_options=RevocationOptions(
                enabled=True,
                revoke_url="https://github.com/settings/connections/applications/" + os.environ["GITHUB_CLIENT_ID"]
            )
        )
    )
    
    register_tools(mcp)
    
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request):
        return StarletteJSONResponse({"status": "healthy", "service": "GitHubManager MCP Server"})

    @mcp.custom_route("/debug", methods=["GET"])
    async def debug_env(request):
        """Debug endpoint to check environment variables"""
        github_token = os.environ.get("GITHUB_TOKEN")
        
        return StarletteJSONResponse({
            "github_token_exists": bool(github_token),
            "github_token_length": len(github_token) if github_token else 0,
            "github_token_prefix": github_token[:4] + "..." if github_token and len(github_token) > 4 else None,
            "port": os.environ.get("PORT", "10000"),
            "env_vars_count": len(os.environ),
            "all_env_vars": list(os.environ.keys())
        })

    @mcp.custom_route("/auth/login", methods=["GET"])
    async def login_redirect(request):
        """Start GitHub OAuth flow."""
        async with sso:
            return await sso.get_login_redirect()

    @mcp.custom_route("/auth/callback", methods=["GET"])
    async def auth_callback(request: Request, ctx: Context):
        """Handle GitHub OAuth callback."""
        async with sso:
            try:
                user = await sso.verify_and_process(request)
                token = sso.access_token
            except Exception as e:
                import traceback
                traceback.print_exc()
                return StarletteJSONResponse(
                    status_code=400,
                    content={"error": str(e)}
                )
        ctx.session["oauth_token"] = token
        ctx.session["user_id"] = user.id
        ctx.session["user"] = user

        user_data = {
            "id": user.id,
            "email": user.email,
            "name": user.display_name,
            "login": getattr(user, 'login', None),
            "avatar_url": getattr(user, 'avatar_url', None),  
        }
        
        return StarletteJSONResponse({
            "msg": "Auth successful",
            "user": user_data,
            "token": token
        })
    
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