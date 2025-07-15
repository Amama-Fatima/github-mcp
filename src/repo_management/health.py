"""
Repository health checker functionality for GitHub MCP server.
"""
import httpx
from datetime import datetime, timezone
from ..config import GITHUB_TOKEN, GITHUB_HEADERS, TIMEOUT

def check_repository_health(owner: str, repo: str) -> dict:
    """
    Gathers raw repository data for Claude to analyze health
    Returns structured data without interpretations
    """
    if not GITHUB_TOKEN:
        return {"error": "GitHub token not configured"}
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Basic repo metadata
            repo_url = f"https://api.github.com/repos/{owner}/{repo}"
            repo_data = client.get(repo_url, headers=GITHUB_HEADERS).json()
            
            # File listing (first level only)
            contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
            contents = client.get(contents_url, headers=GITHUB_HEADERS).json()
            
            # Get contents of key files if they exist
            key_files = {
                'readme': _get_file_content(client, contents, ['README.md', 'README.rst', 'README.txt']),
                'license': _get_file_content(client, contents, ['LICENSE', 'LICENSE.md']),
                'security': _get_file_content(client, contents, ['SECURITY.md']),
                'contributing': _get_file_content(client, contents, ['CONTRIBUTING.md']),
                'ci_config': _get_ci_config(client, owner, repo)
            }

            # Activity data
            updated_at = repo_data.get("updated_at")
            days_since_update = None
            if updated_at:
                last_update = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                days_since_update = (datetime.now(timezone.utc) - last_update).days

            return {
                "basic_info": {
                    "name": repo_data.get("name"),
                    "description": repo_data.get("description"),
                    "stars": repo_data.get("stargazers_count"),
                    "forks": repo_data.get("forks_count"),
                    "is_archived": repo_data.get("archived"),
                    "last_updated_days": days_since_update,
                    "topics": repo_data.get("topics", [])
                },
                "files": {
                    "directory_structure": [item.get("name") for item in contents],
                    "key_files": key_files
                },
                "settings": {
                    "has_issues": repo_data.get("has_issues"),
                    "has_wiki": repo_data.get("has_wiki"),
                    "has_discussions": repo_data.get("has_discussions")
                }
            }

    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def _get_file_content(client, contents, possible_filenames):
    """Helper to fetch content of first matching file"""
    for item in contents:
        if item.get("type") == "file" and item.get("name") in possible_filenames:
            download_url = item.get("download_url")
            if download_url:
                response = client.get(download_url)
                if response.status_code == 200:
                    return {
                        "file_name": item.get("name"),
                        "content": response.text[:5000]  # Limit size
                    }
    return None

def _get_ci_config(client, owner, repo):
    """Check for common CI config files"""
    ci_files = [
        ".github/workflows",
        ".circleci/config.yml",
        ".travis.yml",
        "Jenkinsfile"
    ]
    results = {}
    
    for path in ci_files:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        response = client.get(url, headers=GITHUB_HEADERS)
        if response.status_code == 200:
            results[path] = "exists"
        elif path == ".github/workflows":
            # Special case - check for individual workflow files
            workflows = client.get(url).json()
            if isinstance(workflows, list):
                results[path] = [f["name"] for f in workflows if f.get("type") == "file"]
    
    return results if results else None

def check_repository_dependencies(owner: str, repo: str) -> dict:
    """Returns raw dependency files content for Claude to analyze"""
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Get repository contents
            contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
            contents_r = client.get(contents_url, headers=GITHUB_HEADERS)
            contents_r.raise_for_status()
            contents = contents_r.json()

            # Common dependency file patterns to look for
            dependency_patterns = [
                # Node.js
                "package.json", "package-lock.json", "yarn.lock",
                # Python
                "requirements.txt", "Pipfile", "Pipfile.lock", "pyproject.toml", "poetry.lock",
                # Ruby
                "Gemfile", "Gemfile.lock",
                # Java
                "pom.xml", "build.gradle", "build.gradle.kts",
                # Go
                "go.mod", "go.sum",
                # Rust
                "Cargo.toml", "Cargo.lock",
                # PHP
                "composer.json", "composer.lock",
                # .NET
                "*.csproj", "packages.config",
                # General
                ".nvmrc", ".node-version", ".ruby-version", "runtime.txt"
            ]

            # Find all matching files
            dependency_files = []
            for item in contents:
                if item.get("type") == "file" and any(
                    item["name"].lower() == pattern.lower() or 
                    item["name"].endswith(pattern.lstrip('*'))
                    for pattern in dependency_patterns
                ):
                    dependency_files.append(item)

            # Fetch content of each dependency file
            results = []
            for dep_file in dependency_files:
                download_url = dep_file.get("download_url")
                if not download_url:
                    continue

                file_r = client.get(download_url)
                if file_r.status_code == 200:
                    results.append({
                        "file_path": dep_file["path"],
                        "file_name": dep_file["name"],
                        "content": file_r.text,
                        "size": dep_file.get("size"),
                        "sha": dep_file.get("sha")
                    })

            return {
                "owner": owner,
                "repo": repo,
                "dependency_files": results,
                "total_files_found": len(results)
            }

    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}",
            "details": str(e),
            "status_code": e.response.status_code
        }
    except Exception as e:
        return {
            "error": "Error fetching dependencies",
            "details": str(e)
        }
