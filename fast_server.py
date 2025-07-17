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

# Mount the MCP server at the root path
app.mount("/", github_mcp.streamable_http_app())

PORT = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)