"""
Smart repository search functionality for GitHub MCP server.
"""
import httpx
from ..config import GITHUB_TOKEN, GITHUB_HEADERS, TIMEOUT


def search_repositories(query: str = "", language: str = "", topic: str = "", 
                       sort: str = "updated", order: str = "desc", 
                       limit: int = 10, user: str = "") -> dict:
    """
    Smart repository search across GitHub with structured JSON output
    """
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}
    
    # Build search query
    search_parts = []
    
    if query:
        search_parts.append(query)
    if language:
        search_parts.append(f"language:{language}")
    if topic:
        search_parts.append(f"topic:{topic}")
    if user:
        search_parts.append(f"user:{user}")
    if not search_parts:
        search_parts.append("stars:>0")  # Default fallback
    
    search_query = " ".join(search_parts)
    
    url = "https://api.github.com/search/repositories"
    params = {
        "q": search_query,
        "sort": sort,
        "order": order,
        "per_page": min(limit, 100)
    }
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url, headers=GITHUB_HEADERS, params=params)
            r.raise_for_status()
            data = r.json()
        
        repos = data.get("items", [])
        total_count = data.get("total_count", 0)
        
        if not repos:
            return {
                "query": search_query,
                "repositories": [],
                "total_count": 0,
                "message": "🔍 No repositories found."
            }
        
        results = []
        for repo in repos:
            results.append({
                "name": repo.get("full_name", "Unknown"),
                "description": repo.get("description", "No description"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "language": repo.get("language", "Unknown"),
                "updated": repo.get("updated_at", "Unknown")[:10],
                "url": repo.get("html_url", "")
            })
        
        return {
            "query": search_query,
            "total_count": total_count,
            "count": len(results),
            "repositories": results
        }
    
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}",
            "details": e.response.text
        }
    except Exception as e:
        return {
            "error": "Exception occurred while searching repositories",
            "details": str(e)
        }


def get_starred_repositories(username: str, limit: int = 10) -> dict:
    """Get user's starred repositories in structured JSON"""
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}
    
    url = f"https://api.github.com/users/{username}/starred"
    params = {"per_page": min(limit, 100)}
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url, headers=GITHUB_HEADERS, params=params)
            r.raise_for_status()
            repos = r.json()
        
        if not repos:
            return {
                "username": username,
                "repositories": [],
                "message": "⭐ No starred repositories found."
            }
        
        results = []
        for repo in repos:
            results.append({
                "name": repo.get("full_name", "Unknown"),
                "description": repo.get("description", "No description"),
                "stars": repo.get("stargazers_count", 0),
                "language": repo.get("language", "Unknown"),
                "url": repo.get("html_url", "")
            })
        
        return {
            "username": username,
            "count": len(results),
            "repositories": results
        }
    
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}",
            "details": e.response.text
        }
    except Exception as e:
        return {
            "error": "Exception occurred while fetching repositories",
            "details": str(e)
        }
