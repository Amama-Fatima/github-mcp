"""
Utility functions for the GitHub MCP server.
"""

def format_repository_info(repo_data: dict) -> str:
    """Format repository information for display"""
    name = repo_data.get("name", "Unknown")
    full_name = repo_data.get("full_name", "Unknown")
    description = repo_data.get("description") or "No description"
    private = repo_data.get("private", False)
    updated_at = repo_data.get("updated_at", "Unknown")
    
    privacy = "🔒 Private" if private else "🌐 Public"
    
    return (f"• **{name}** ({privacy})\n"
            f"  📝 {description}\n"
            f"  🔄 Updated: {updated_at}\n"
            f"  🔗 {full_name}\n\n")


def format_file_info(file_data: dict) -> str:
    """Format file information for display"""
    file_name = file_data.get("name", "Unknown")
    file_size = file_data.get("size", 0)
    file_type = file_data.get("type", "unknown")
    
    return f"📄 File: {file_name}\n📊 Size: {file_size} bytes\n📋 Type: {file_type}"


def format_directory_contents(contents: list, path: str = "") -> str:
    """Format directory contents for display"""
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


def handle_http_error(error, context: str = "operation") -> str:
    """Handle HTTP errors with appropriate messages"""
    if hasattr(error, 'response'):
        status_code = error.response.status_code
        if status_code == 404:
            return f"❌ Resource not found during {context}"
        elif status_code == 422:
            return f"❌ Invalid request during {context} - check parameters"
        elif status_code == 401:
            return f"❌ Unauthorized - check your GitHub token"
        elif status_code == 403:
            return f"❌ Forbidden - insufficient permissions"
        else:
            return f"❌ HTTP error {status_code} during {context}: {error.response.text}"
    else:
        return f"❌ Error during {context}: {str(error)}"


def validate_github_token() -> str:
    """Validate GitHub token and return appropriate message"""
    from config import GITHUB_TOKEN
    
    if not GITHUB_TOKEN:
        return "⚠️ No GITHUB_TOKEN set in environment."
    
    return None  # Token is valid