"""
GitHubManager MCP Server

A modular MCP server for interacting with the GitHub API.
Provides tools for repository management, file operations, and git workflows.
"""

from .main import create_app, main
from src.config import GITHUB_TOKEN

__version__ = "1.0.0"
__all__ = ["create_app", "main", "GITHUB_TOKEN"]