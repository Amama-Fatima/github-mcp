import base64
import httpx
from ..config import GITHUB_TOKEN, GITHUB_HEADERS, TIMEOUT

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

def get_individual_file_contents(owner: str, repo: str, file_path: str, branch: str = "main") -> dict:
    """
    Get the actual contents of a specific file from a GitHub repository.
    Returns the raw file content as text.
    
    Args:
        owner: Repository owner
        repo: Repository name  
        file_path: Path to the file (e.g., "src/tool.py", "README.md")
        branch: Branch name (default: "main")
    """
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Use the contents API to get file info and download URL
            contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
            params = {"ref": branch}
            
            contents_r = client.get(contents_url, headers=GITHUB_HEADERS, params=params)
            contents_r.raise_for_status()
            file_info = contents_r.json()
            
            # Check if it's actually a file (not a directory)
            if file_info.get("type") != "file":
                return {
                    "error": f"'{file_path}' is not a file",
                    "type": file_info.get("type"),
                    "owner": owner,
                    "repo": repo,
                    "file_path": file_path,
                    "branch": branch
                }
            
            # Get the download URL for the raw file content
            download_url = file_info.get("download_url")
            if not download_url:
                return {
                    "error": "No download URL available for this file",
                    "owner": owner,
                    "repo": repo,
                    "file_path": file_path,
                    "branch": branch
                }
            
            # Fetch the actual file contents
            file_r = client.get(download_url)
            file_r.raise_for_status()
            
            # Try to decode as text, handle binary files gracefully
            try:
                content = file_r.text
                is_binary = False
            except UnicodeDecodeError:
                content = "[Binary file - cannot display as text]"
                is_binary = True
            
            # Extract file extension for context
            file_extension = file_path.split('.')[-1] if '.' in file_path else ""
            
            return {
                "owner": owner,
                "repo": repo,
                "file_path": file_path,
                "branch": branch,
                "content": content,
                "is_binary": is_binary,
                "file_extension": file_extension,
                "file_size": file_info.get("size", 0),
                "encoding": file_info.get("encoding"),
                "sha": file_info.get("sha"),
                "html_url": file_info.get("html_url"),
                "download_url": download_url,
                "last_modified": file_info.get("last_modified")
            }
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "error": f"File '{file_path}' not found in repository",
                "status_code": 404,
                "owner": owner,
                "repo": repo,
                "file_path": file_path,
                "branch": branch
            }
        else:
            return {
                "error": f"HTTP error {e.response.status_code}",
                "details": e.response.text,
                "owner": owner,
                "repo": repo,
                "file_path": file_path,
                "branch": branch
            }
    except Exception as e:
        return {
            "error": "Exception occurred while fetching file",
            "details": str(e),
            "owner": owner,
            "repo": repo,
            "file_path": file_path,
            "branch": branch
        }