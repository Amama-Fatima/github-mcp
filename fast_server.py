import contextlib
from fastapi import FastAPI
from main import create_app
import os

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

@app.get("/debug/env")
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

# Mount the MCP server at the root path
app.mount("/", github_mcp.streamable_http_app())

PORT = int(os.environ.get("PORT", 10000))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)