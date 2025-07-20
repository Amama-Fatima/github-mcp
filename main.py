# main.py
import os
import contextlib
import uvicorn
from dotenv import load_dotenv
from fastapi import Request, HTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from fastapi.middleware import Middleware

from mcp.server.fastmcp import FastMCP, Context
from fastapi_sso.sso.github import GithubSSO
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions, RevocationOptions
from src.tools import register_tools  # your tools

load_dotenv()

GITHUB_CLIENT_ID = os.environ["GITHUB_CLIENT_ID"]
GITHUB_CLIENT_SECRET = os.environ["GITHUB_CLIENT_SECRET"]
REDIRECT_URI = os.environ.get("GITHUB_REDIRECT_URI")
# SESSION_SECRET = os.environ["SESSION_SECRET"]
SESSION_SECRET = "your-session-secret"

sso = GithubSSO(
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=["repo", "user"],
    allow_insecure_http=False
)

def create_app():
    @contextlib.asynccontextmanager
    async def lifespan(app):
        async with mcp.session_manager.run():
            yield

    mcp = FastMCP(
        name="GitHubMCP",
        lifespan=lifespan,
        auth_server_provider=sso,
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
                revoke_url=f"https://github.com/settings/connections/applications/{GITHUB_CLIENT_ID}"
            )
        ),
    )

    register_tools(mcp)

    @mcp.custom_route("/health")
    async def health(request: Request):
        return JSONResponse({"status": "healthy"})

    @mcp.custom_route("/auth/login")
    async def login(request: Request):
        async with sso:
            return await sso.get_login_redirect()

    @mcp.custom_route("/auth/callback")
    async def auth_callback(request: Request):
        async with sso:
            try:
                user = await sso.verify_and_process(request)
                token = sso.access_token
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=400)

        request.session["oauth_token"] = token
        request.session["user"] = {
            "id": user.id,
            "login": getattr(user, "login", None),
            "name": getattr(user, "display_name", None),
            "email": user.email,
        }

        return JSONResponse({"msg": "Auth successful", "user": request.session["user"]})

    @mcp.custom_route("/protected")
    async def protected(request: Request):
        token = request.session.get("oauth_token")
        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return JSONResponse({"msg": "You are authorized", "token": token})

    return mcp

mcp = create_app()
app = mcp.streamable_http_app()
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, https_only=True)

def main():
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
