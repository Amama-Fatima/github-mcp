"""
Tool registration module for the GitHub MCP server.
"""
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any
from .repos import list_repositories, create_repository, get_repository_contents
from .files import create_file, update_file
from .git import create_pull_request, create_branch
from .repo_management.search import (
    search_repositories, 
    get_starred_repositories, 
    get_recent_repositories,
    search_repositories_by_language,
    search_repositories_by_topic
)
from .repo_management.branches import (
    get_branch_status_overview,
    get_active_branches,
    get_branch_comparison
)

from .repo_management.health import (
    check_repository_health,
    check_repository_dependencies
)

from .issue_and_pr_management.issues import (
    smart_issue_triage,
    bulk_issue_triage,
    apply_issue_labels_tool,
    get_issue_comments
)

from .issue_and_pr_management.pr_reviews import (
    get_pr_review_summary,
    get_pr_diff_summary,
    list_open_prs_for_review
)


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

    @mcp.tool()
    def search_github_repositories(query: str = "", language: str = "", topic: str = "", 
                                 sort: str = "updated", order: str = "desc", 
                                 limit: int = 10, user: str = "") -> dict:
        """
        Smart repository search across GitHub.
        
        Args:
            query: Search query string
            language: Filter by programming language (e.g., 'python', 'javascript')
            topic: Filter by topic (e.g., 'machine-learning', 'web-development')
            sort: Sort by 'stars', 'forks', 'updated', 'created'
            order: 'desc' or 'asc'
            limit: Number of results (max 100)
            user: Filter by specific user/organization
        """
        return search_repositories(query, language, topic, sort, order, limit, user)

    @mcp.tool()
    def get_github_starred_repositories(username: str, limit: int = 10) -> dict:
        """Get user's starred repositories"""
        return get_starred_repositories(username, limit)

    @mcp.tool()
    def get_github_recent_repositories(username: str, limit: int = 10) -> dict:
        """Get user's recently updated repositories"""
        return get_recent_repositories(username, limit)

    @mcp.tool()
    def search_github_repositories_by_language(language: str, limit: int = 10, sort: str = "stars") -> dict:
        """Search repositories by programming language"""
        return search_repositories_by_language(language, limit, sort)

    @mcp.tool()
    def search_github_repositories_by_topic(topic: str, limit: int = 10, sort: str = "stars") -> dict:
        """Search repositories by topic"""
        return search_repositories_by_topic(topic, limit, sort)

    @mcp.tool()
    def get_github_branch_status_overview(owner: str, repo: str, limit: int = 10) -> dict:
        """
        Get comprehensive branch status overview for a repository.
        Shows all branches with their last commit info, PR status, and merge status.
        
        Args:
            owner: Repository owner
            repo: Repository name
            limit: Maximum number of branches to show
        """
        return get_branch_status_overview(owner, repo, limit)

    @mcp.tool()
    def get_github_active_branches(owner: str, repo: str, days: int = 30) -> dict:
        """
        Get branches that have been active within the specified number of days.
        
        Args:
            owner: Repository owner
            repo: Repository name
            days: Number of days to look back for activity
        """
        return get_active_branches(owner, repo, days)

    @mcp.tool()
    def compare_github_branches(owner: str, repo: str, base_branch: str, compare_branch: str) -> dict:
        """
        Compare two branches and show the differences.
        
        Args:
            owner: Repository owner
            repo: Repository name
            base_branch: Base branch to compare against
            compare_branch: Branch to compare
        """
        return get_branch_comparison(owner, repo, base_branch, compare_branch)
    

    @mcp.tool()
    def check_github_repository_health(owner: str, repo: str) -> dict:
        """
        Comprehensive repository health check.
        Scans for missing README, license, security policies, CI/CD setup,
        dependency management, and other best practices.
        
        Args:
            owner: Repository owner
            repo: Repository name
        """
        return check_repository_health(owner, repo)

    @mcp.tool()
    def analyze_github_repository_dependencies(owner: str, repo: str) -> dict:
        """
        Detailed dependency analysis for supported languages.
        Analyzes dependency files like package.json, requirements.txt, etc.
        
        Args:
            owner: Repository owner
            repo: Repository name
        """
        return check_repository_dependencies(owner, repo)
    

    @mcp.tool()
    def smart_issue_triage_tool(owner: str, repo: str, issue_number: int) -> dict:
        """
        Fetch issue details and provide them to Claude for intelligent analysis and categorization.
        Returns issue data with available labels and analysis prompt for Claude to process.
        
        Args:
            owner: Repository owner
            repo: Repository name  
            issue_number: Issue number to analyze
        """
        return smart_issue_triage(owner, repo, issue_number)

    @mcp.tool()
    def bulk_issue_triage_tool(owner: str, repo: str, limit: int = 10, state: str = "open") -> dict:
        """
        Fetch multiple issues for Claude to analyze in bulk. Provides structured data for 
        comprehensive repository issue analysis and triage recommendations.
        
        Args:
            owner: Repository owner
            repo: Repository name
            limit: Maximum number of issues to fetch
            state: Issue state ('open', 'closed', 'all')
        """
        return bulk_issue_triage(owner, repo, limit, state)

    @mcp.tool()
    def apply_issue_labels(owner: str, repo: str, issue_number: int, labels: list) -> dict:
        """
        Apply labels to an issue. This is typically called by Claude after analyzing an issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            labels: List of label names to apply
        """
        return apply_issue_labels_tool(owner, repo, issue_number, labels)

    @mcp.tool()
    def get_issue_comments_tool(owner: str, repo: str, issue_number: int) -> dict:
        """
        Get comments for an issue to provide additional context for analysis.
        Useful for understanding the full conversation and current status.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
        """
        return get_issue_comments(owner, repo, issue_number)
    

    @mcp.tool()
    def create_pr_review_summary(owner: str, repo: str, pr_number: int) -> str:
        """
        Get comprehensive PR review summary with changes analysis, insights, and recommendations.
        Analyzes files, commits, reviews, and provides actionable feedback.
        """
        return get_pr_review_summary(owner, repo, pr_number)
    
    @mcp.tool()
    def create_pr_diff_summary(owner: str, repo: str, pr_number: int) -> str:
        """
        Get concise diff summary of PR changes with patch previews
        """
        return get_pr_diff_summary(owner, repo, pr_number)
    
    @mcp.tool()
    def list_open_prs_for_reviewing(owner: str, repo: str, limit: int = 10) -> str:
        """
        List open PRs that need review with basic info
        """
        return list_open_prs_for_review(owner, repo, limit)