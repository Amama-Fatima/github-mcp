import httpx
from typing import Dict, Any
from ..config import GITHUB_TOKEN, GITHUB_HEADERS, TIMEOUT

def get_pr_review_summary(owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
    """
    Gathers raw PR data for Claude to analyze
    Returns structured data without interpretations
    """
    if not GITHUB_TOKEN:
        return {"error": "GitHub token not configured"}
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Get PR details
            pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
            pr_data = client.get(pr_url, headers=GITHUB_HEADERS).json()
            
            # Get PR files (changed files)
            files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
            files_data = client.get(files_url, headers=GITHUB_HEADERS).json()
            
            # Get PR commits (limited to most recent 10 for context)
            commits_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/commits?per_page=10"
            commits_data = client.get(commits_url, headers=GITHUB_HEADERS).json()
            
            # Get PR reviews with comments
            reviews_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
            reviews_data = client.get(reviews_url, headers=GITHUB_HEADERS).json()
            
            # Get PR comments (both review and general comments)
            comments_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments"
            comments_data = client.get(comments_url, headers=GITHUB_HEADERS).json()
            
            # Get diff content for key files
            diff_content = _get_key_file_diffs(client, owner, repo, pr_number, files_data)

        return {
            "metadata": {
                "title": pr_data.get("title"),
                "state": pr_data.get("state"),
                "created_at": pr_data.get("created_at"),
                "updated_at": pr_data.get("updated_at"),
                "merged": pr_data.get("merged"),
                "mergeable": pr_data.get("mergeable"),
                "author": pr_data.get("user", {}).get("login"),
                "base_branch": pr_data.get("base", {}).get("ref"),
                "head_branch": pr_data.get("head", {}).get("ref"),
                "description": pr_data.get("body")
            },
            "changes": {
                "total_files": len(files_data),
                "files": [
                    {
                        "filename": f.get("filename"),
                        "status": f.get("status"),
                        "changes": f.get("changes"),
                        "additions": f.get("additions"),
                        "deletions": f.get("deletions"),
                        "patch": f.get("patch")[:1000] if f.get("patch") else None
                    } 
                    for f in files_data[:10]  # Limit to first 10 files
                ],
                "diff_samples": diff_content
            },
            "activity": {
                "commits": [
                    {
                        "sha": c.get("sha")[:7],
                        "message": c.get("commit", {}).get("message"),
                        "author": c.get("commit", {}).get("author", {}).get("name")
                    }
                    for c in commits_data
                ],
                "reviews": [
                    {
                        "state": r.get("state"),
                        "reviewer": r.get("user", {}).get("login"),
                        "body": r.get("body"),
                        "comments": [
                            {
                                "body": rc.get("body"),
                                "path": rc.get("path"),
                                "line": rc.get("line")
                            }
                            for rc in r.get("comments", [])
                        ]
                    }
                    for r in reviews_data
                ],
                "comments": [
                    {
                        "author": c.get("user", {}).get("login"),
                        "body": c.get("body"),
                        "path": c.get("path"),
                        "line": c.get("line")
                    }
                    for c in comments_data
                ]
            }
        }

    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def _get_key_file_diffs(client, owner, repo, pr_number, files_data):
    """Fetch diff content for important files"""
    important_exts = ['.py', '.js', '.ts', '.go', '.rs', '.java', '.kt']
    diffs = {}
    
    for file in files_data[:5]:  # Limit to first 5 important files
        filename = file.get("filename", "")
        if any(filename.endswith(ext) for ext in important_exts):
            raw_url = f"https://github.com/{owner}/{repo}/pull/{pr_number}/files?diff=unified&file={filename}"
            try:
                response = client.get(raw_url)
                if response.status_code == 200:
                    diffs[filename] = response.text[:3000]  # Limit size
            except Exception:
                continue
    
    return diffs

def list_open_prs_for_review(owner: str, repo: str, limit: int = 10) -> Dict[str, Any]:
    """
    List open PRs that need review
    """
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            prs_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            prs_response = client.get(prs_url, headers=GITHUB_HEADERS, 
                                    params={"state": "open", "per_page": limit})
            prs_response.raise_for_status()
            prs_data = prs_response.json()
        
        prs_summary = []
        for pr in prs_data:
            pr_summary = {
                "number": pr.get("number"),
                "title": pr.get("title"),
                "author": pr.get("user", {}).get("login"),
                "created_at": pr.get("created_at"),
                "updated_at": pr.get("updated_at"),
                "url": pr.get("html_url"),
                "draft": pr.get("draft", False),
                "mergeable": pr.get("mergeable")
            }
            prs_summary.append(pr_summary)
        
        return {
            "total_prs": len(prs_data),
            "prs": prs_summary
        }
        
    except Exception as e:
        return {"error": f"Failed to list PRs: {str(e)}"}
