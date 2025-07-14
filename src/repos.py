import httpx
from .config import GITHUB_TOKEN, GITHUB_HEADERS, TIMEOUT


def list_repositories(username: str, type: str = "all") -> str:
    """List user's repositories. Type can be 'all', 'owner', 'public', 'private'"""
    if not GITHUB_TOKEN:
        return "⚠️ No GITHUB_TOKEN set in environment."
    
    url = f"https://api.github.com/user/repos"
    params = {"type": type, "sort": "updated", "per_page": 20}
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url, headers=GITHUB_HEADERS, params=params)
            r.raise_for_status()
            repos = r.json()
            
        if not repos:
            return f"📂 No repositories found for user {username}"
        
        result = f"📂 Found {len(repos)} repositories:\n\n"
        
        for repo in repos:
            name = repo.get("name", "Unknown")
            full_name = repo.get("full_name", "Unknown")
            description = repo.get("description") or "No description"
            private = repo.get("private", False)
            updated_at = repo.get("updated_at", "Unknown")
            
            privacy = "🔒 Private" if private else "🌐 Public"
            
            result += f"• **{name}** ({privacy})\n"
            result += f"  📝 {description}\n"
            result += f"  🔄 Updated: {updated_at}\n"
            result += f"  🔗 {full_name}\n\n"
        
        return result
        
    except httpx.HTTPStatusError as e:
        return f"❌ HTTP error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"❌ Error fetching repositories: {str(e)}"


def create_repository(name: str, description: str = "", private: bool = False, auto_init: bool = True) -> str:
    """Create a new GitHub repository"""
    if not GITHUB_TOKEN:
        return "⚠️ No GITHUB_TOKEN set in environment."
    
    url = "https://api.github.com/user/repos"
    
    payload = {
        "name": name,
        "description": description,
        "private": private,
        "auto_init": auto_init
    }
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.post(url, headers=GITHUB_HEADERS, json=payload)
            r.raise_for_status()
            repo_data = r.json()
            
        repo_url = repo_data.get("html_url", "Unknown")
        clone_url = repo_data.get("clone_url", "Unknown")
        
        return f"✅ Repository created successfully!\n🔗 URL: {repo_url}\n📋 Clone: {clone_url}"
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 422:
            return f"❌ Repository '{name}' already exists or invalid name"
        return f"❌ HTTP error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"❌ Error creating repository: {str(e)}"


def get_repository_contents(owner: str, repo: str, path: str = "") -> str:
    """Get contents of a repository directory or file"""
    if not GITHUB_TOKEN:
        return "⚠️ No GITHUB_TOKEN set in environment."
    
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url, headers=GITHUB_HEADERS)
            r.raise_for_status()
            contents = r.json()
            
        if isinstance(contents, dict):
            # Single file
            file_name = contents.get("name", "Unknown")
            file_size = contents.get("size", 0)
            file_type = contents.get("type", "unknown")
            
            return f"📄 File: {file_name}\n📊 Size: {file_size} bytes\n📋 Type: {file_type}"
            
        elif isinstance(contents, list):
            if not contents:
                return f"📂 Directory '{path}' is empty"
            
            result = f"📂 Contents of /{path} ({len(contents)} items):\n\n"
            
            for item in contents:
                name = item.get("name", "Unknown")
                item_type = item.get("type", "unknown")
                size = item.get("size", 0)
                
                icon = "📁" if item_type == "dir" else "📄"
                result += f"{icon} {name}"
                if item_type == "file":
                    result += f" ({size} bytes)"
                result += "\n"
            
            return result
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"❌ Repository '{owner}/{repo}' or path '{path}' not found"
        return f"❌ HTTP error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"❌ Error fetching contents: {str(e)}"