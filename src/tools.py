"""
Tool registration module for the GitHub MCP server.
"""

from mcp.server.fastmcp import FastMCP
from .repos import list_repositories, create_repository, get_repository_contents
from .files import create_file, update_file
from .git import create_pull_request, create_branch


def register_tools(mcp: FastMCP):
    """Register all GitHub tools with the MCP server"""
    
    @mcp.tool()
    def list_github_repositories(username: str, type: str = "all") -> str:
        """List user's repositories. Type can be 'all', 'owner', 'public', 'private'"""
        return list_repositories(username, type)
    
    @mcp.tool()
    def create_github_repository(name: str, description: str = "", private: bool = False, auto_init: bool = True) -> str:
        """Create a new GitHub repository"""
        return create_repository(name, description, private, auto_init)
    
    @mcp.tool()
    def get_github_repository_contents(owner: str, repo: str, path: str = "") -> str:
        """Get contents of a repository directory or file"""
        return get_repository_contents(owner, repo, path)
    
    @mcp.tool()
    def create_github_file(owner: str, repo: str, path: str, content: str, message: str, branch: str = "main") -> str:
        """Create a new file in a repository"""
        return create_file(owner, repo, path, content, message, branch)
    
    @mcp.tool()
    def update_github_file(owner: str, repo: str, path: str, content: str, message: str, branch: str = "main") -> str:
        """Update an existing file in a repository"""
        return update_file(owner, repo, path, content, message, branch)
    
    @mcp.tool()
    def create_github_pull_request(owner: str, repo: str, title: str, body: str, head: str, base: str = "main") -> str:
        """Create a pull request"""
        return create_pull_request(owner, repo, title, body, head, base)
    
    @mcp.tool()
    def create_github_branch(owner: str, repo: str, branch_name: str, from_branch: str = "main") -> str:
        """Create a new branch from an existing branch"""
        return create_branch(owner, repo, branch_name, from_branch)