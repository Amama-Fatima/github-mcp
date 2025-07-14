import base64
import httpx
from .config import GITHUB_TOKEN, GITHUB_HEADERS, TIMEOUT


def create_file(owner: str, repo: str, path: str, content: str, message: str, branch: str = "main") -> str:
    """Create a new file in a repository"""
    if not GITHUB_TOKEN:
        return "⚠️ No GITHUB_TOKEN set in environment."
    
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    
    # Encode content to base64
    content_encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": message,
        "content": content_encoded,
        "branch": branch
    }
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.put(url, headers=GITHUB_HEADERS, json=payload)
            r.raise_for_status()
            response_data = r.json()
            
        file_url = response_data.get("content", {}).get("html_url", "Unknown")
        
        return f"✅ File created successfully!\n📄 Path: {path}\n🔗 URL: {file_url}\n💬 Commit: {message}"
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 422:
            return f"❌ File '{path}' already exists or invalid path"
        return f"❌ HTTP error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"❌ Error creating file: {str(e)}"


def update_file(owner: str, repo: str, path: str, content: str, message: str, branch: str = "main") -> str:
    """Update an existing file in a repository"""
    if not GITHUB_TOKEN:
        return "⚠️ No GITHUB_TOKEN set in environment."
    
    # First get the file to get its SHA
    get_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Get current file info
            r = client.get(get_url, headers=GITHUB_HEADERS)
            r.raise_for_status()
            file_data = r.json()
            
            file_sha = file_data.get("sha")
            
            # Encode new content
            content_encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            payload = {
                "message": message,
                "content": content_encoded,
                "sha": file_sha,
                "branch": branch
            }
            
            update_r = client.put(get_url, headers=GITHUB_HEADERS, json=payload)
            update_r.raise_for_status()
            response_data = update_r.json()
            
        file_url = response_data.get("content", {}).get("html_url", "Unknown")
        
        return f"✅ File updated successfully!\n📄 Path: {path}\n🔗 URL: {file_url}\n💬 Commit: {message}"
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"❌ File '{path}' not found in repository '{owner}/{repo}'"
        return f"❌ HTTP error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"❌ Error updating file: {str(e)}"