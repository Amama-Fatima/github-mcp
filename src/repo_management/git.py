import httpx
from ..config import GITHUB_TOKEN, GITHUB_HEADERS, TIMEOUT


def create_pull_request(owner: str, repo: str, title: str, body: str, head: str, base: str = "main") -> str:
    """Create a pull request"""
    if not GITHUB_TOKEN:
        return "⚠️ No GITHUB_TOKEN set in environment."
    
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    
    payload = {
        "title": title,
        "body": body,
        "head": head,
        "base": base
    }
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.post(url, headers=GITHUB_HEADERS, json=payload)
            r.raise_for_status()
            pr_data = r.json()
            
        pr_url = pr_data.get("html_url", "Unknown")
        pr_number = pr_data.get("number", "Unknown")
        
        return f"✅ Pull request created successfully!\n🔗 PR #{pr_number}: {pr_url}\n📋 Title: {title}"
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 422:
            return f"❌ Pull request could not be created - check branch names and permissions"
        return f"❌ HTTP error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"❌ Error creating pull request: {str(e)}"


def create_branch(owner: str, repo: str, branch_name: str, from_branch: str = "main") -> str:
    """Create a new branch from an existing branch"""
    if not GITHUB_TOKEN:
        return "⚠️ No GITHUB_TOKEN set in environment."
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Get SHA of the source branch
            ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{from_branch}"
            ref_r = client.get(ref_url, headers=GITHUB_HEADERS)
            ref_r.raise_for_status()
            ref_data = ref_r.json()
            
            source_sha = ref_data.get("object", {}).get("sha")
            
            # Create new branch
            create_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
            payload = {
                "ref": f"refs/heads/{branch_name}",
                "sha": source_sha
            }
            
            create_r = client.post(create_url, headers=GITHUB_HEADERS, json=payload)
            create_r.raise_for_status()
            
        return f"✅ Branch '{branch_name}' created successfully from '{from_branch}'"
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 422:
            return f"❌ Branch '{branch_name}' already exists or invalid name"
        return f"❌ HTTP error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"❌ Error creating branch: {str(e)}"