from fastapi import FastAPI, Request
from fastapi_sso.sso.github import GithubSSO
from fastapi.responses import JSONResponse
import contextlib
from main import create_app
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

github_mcp = create_app()

# Create a lifespan manager for the session
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with github_mcp.session_manager.run():
        yield

app = FastAPI(
    title="GitHub MCP Server",
    description="A Model Context Protocol server for GitHub operations",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "GitHubManager MCP Server"}

@app.get("/debug")
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

@app.get("/auth/login")
async def login_redirect():
    """Start GitHub OAuth flow."""
    async with sso:
        return await sso.get_login_redirect()
    
app.mount("/", github_mcp.streamable_http_app())

@app.get("/auth/callback")
async def auth_callback(request: Request):
    async with sso:
        try:
            user = await sso.verify_and_process(request)
            _token = sso.access_token
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    return {
        "msg": "Auth successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.display_name,
            # "access_token": user.access_token
        },
        "obj": user,
        "_token": _token
    }



# Mount the MCP server at the root path

PORT = int(os.environ.get("PORT", 10000))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)