"""
Branch status overview functionality for GitHub MCP server.
"""
import httpx
from datetime import datetime, timezone
from ..config import GITHUB_TOKEN, GITHUB_HEADERS, TIMEOUT


def get_branch_status_overview(owner: str, repo: str, limit: int = 10) -> dict:
    """
    Get comprehensive branch status overview for a repository (structured JSON)
    """
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}
    
    try:
        # Get all branches
        branches_url = f"https://api.github.com/repos/{owner}/{repo}/branches"
        
        with httpx.Client(timeout=TIMEOUT) as client:
            branches_r = client.get(branches_url, headers=GITHUB_HEADERS, 
                                    params={"per_page": min(limit, 100)})
            branches_r.raise_for_status()
            branches = branches_r.json()
            
            # Get default branch
            repo_url = f"https://api.github.com/repos/{owner}/{repo}"
            repo_r = client.get(repo_url, headers=GITHUB_HEADERS)
            repo_r.raise_for_status()
            repo_data = repo_r.json()
            default_branch = repo_data.get("default_branch", "main")
            
            # Get PRs for branch status
            prs_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            prs_r = client.get(prs_url, headers=GITHUB_HEADERS, 
                               params={"state": "all", "per_page": 100})
            prs_r.raise_for_status()
            prs = prs_r.json()
        
        if not branches:
            return {
                "owner": owner,
                "repo": repo,
                "branches": [],
                "default_branch": default_branch,
                "message": f"🌿 No branches found in {owner}/{repo}"
            }

        # Map PRs to branches
        pr_map = {}
        for pr in prs:
            head_ref = pr.get("head", {}).get("ref")
            if head_ref:
                pr_map[head_ref] = {
                    "number": pr.get("number"),
                    "state": pr.get("state"),
                    "merged": pr.get("merged", False),
                    "title": pr.get("title", ""),
                    "url": pr.get("html_url", "")
                }
        
        results = []

        # Sort branches: default first, then by date
        sorted_branches = sorted(branches, key=lambda b: (
            b.get("name") != default_branch,
            b.get("commit", {}).get("commit", {}).get("author", {}).get("date", "")
        ), reverse=True)

        for branch in sorted_branches:
            name = branch.get("name", "Unknown")
            commit = branch.get("commit", {})
            commit_data = commit.get("commit", {})
            
            commit_sha = commit.get("sha", "")[:7]
            commit_author = commit_data.get("author", {}).get("name", "Unknown")
            commit_date = commit_data.get("author", {}).get("date", "Unknown")
            commit_message = commit_data.get("message", "No message").split('\n')[0]

            # Format date
            try:
                if commit_date != "Unknown":
                    date_obj = datetime.fromisoformat(commit_date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
                    days_ago = (datetime.now(timezone.utc) - date_obj).days
                    date_display = {
                        "raw": commit_date,
                        "formatted": formatted_date,
                        "days_ago": days_ago
                    }
                else:
                    date_display = {"raw": "Unknown"}
            except:
                date_display = {"raw": commit_date}

            # Status indicators
            is_default = name == default_branch
            pr_info = pr_map.get(name)
            pr_summary = None
            if pr_info:
                pr_summary = {
                    "number": pr_info["number"],
                    "state": pr_info["state"],
                    "merged": pr_info["merged"],
                    "title": pr_info["title"],
                    "url": pr_info["url"]
                }

            results.append({
                "name": name,
                "is_default": is_default,
                "commit": {
                    "sha": commit_sha,
                    "author": commit_author,
                    "date": date_display,
                    "message": commit_message
                },
                "pull_request": pr_summary
            })
        
        return {
            "owner": owner,
            "repo": repo,
            "default_branch": default_branch,
            "total_branches": len(branches),
            "branches": results
        }

    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}",
            "details": e.response.text
        }
    except Exception as e:
        return {
            "error": "Exception occurred while fetching branch status",
            "details": str(e)
        }


def get_active_branches(owner: str, repo: str, days: int = 30) -> dict:
    """Get branches that have been active within the specified number of days (as JSON)"""
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}
    
    try:
        branches_url = f"https://api.github.com/repos/{owner}/{repo}/branches"
        
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(branches_url, headers=GITHUB_HEADERS, params={"per_page": 100})
            r.raise_for_status()
            branches = r.json()
        
        if not branches:
            return {
                "owner": owner,
                "repo": repo,
                "days": days,
                "branches": [],
                "message": f"🌿 No branches found in {owner}/{repo}"
            }
        
        # Filter active branches
        active_branches = []
        now = datetime.now(timezone.utc)
        cutoff_timestamp = now.timestamp() - (days * 24 * 60 * 60)
        
        for branch in branches:
            commit_date = branch.get("commit", {}).get("commit", {}).get("author", {}).get("date")
            if commit_date:
                try:
                    branch_date = datetime.fromisoformat(commit_date.replace('Z', '+00:00'))
                    if branch_date.timestamp() > cutoff_timestamp:
                        active_branches.append(branch)
                except:
                    continue
        
        if not active_branches:
            return {
                "owner": owner,
                "repo": repo,
                "days": days,
                "branches": [],
                "message": f"🌿 No active branches found in the last {days} days for {owner}/{repo}"
            }

        # Sort by most recent
        sorted_branches = sorted(
            active_branches, 
            key=lambda b: b.get("commit", {}).get("commit", {}).get("author", {}).get("date", ""), 
            reverse=True
        )

        results = []
        for branch in sorted_branches:
            name = branch.get("name", "Unknown")
            commit = branch.get("commit", {})
            commit_data = commit.get("commit", {})

            commit_sha = commit.get("sha", "")[:7]
            commit_author = commit_data.get("author", {}).get("name", "Unknown")
            commit_date = commit_data.get("author", {}).get("date", "Unknown")
            commit_message = commit_data.get("message", "No message").split('\n')[0]

            # Format date
            try:
                if commit_date != "Unknown":
                    date_obj = datetime.fromisoformat(commit_date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
                    days_ago = (now - date_obj).days
                    date_display = {
                        "raw": commit_date,
                        "formatted": formatted_date,
                        "days_ago": days_ago
                    }
                else:
                    date_display = {"raw": "Unknown"}
            except:
                date_display = {"raw": commit_date}
            
            results.append({
                "name": name,
                "commit": {
                    "sha": commit_sha,
                    "author": commit_author,
                    "date": date_display,
                    "message": commit_message
                }
            })
        
        return {
            "owner": owner,
            "repo": repo,
            "days": days,
            "count": len(results),
            "branches": results
        }

    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}",
            "details": e.response.text
        }
    except Exception as e:
        return {
            "error": "Exception occurred while fetching active branches",
            "details": str(e)
        }


def get_branch_comparison(owner: str, repo: str, base_branch: str, compare_branch: str) -> dict:
    """Compare two branches and return a structured JSON summary"""
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}
    
    try:
        compare_url = f"https://api.github.com/repos/{owner}/{repo}/compare/{base_branch}...{compare_branch}"
        
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(compare_url, headers=GITHUB_HEADERS)
            r.raise_for_status()
            comparison = r.json()
        
        status = comparison.get("status", "unknown")
        ahead_by = comparison.get("ahead_by", 0)
        behind_by = comparison.get("behind_by", 0)
        total_commits = comparison.get("total_commits", 0)
        commit_items = []

        # Recent commits (limit 5)
        for commit in comparison.get("commits", [])[:5]:
            commit_data = commit.get("commit", {})
            sha = commit.get("sha", "")[:7]
            message = commit_data.get("message", "No message").split('\n')[0]
            author = commit_data.get("author", {}).get("name", "Unknown")
            date = commit_data.get("author", {}).get("date", "Unknown")

            try:
                if date != "Unknown":
                    date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
                    days_ago = (datetime.now(timezone.utc) - date_obj).days
                    date_display = {
                        "raw": date,
                        "formatted": formatted_date,
                        "days_ago": days_ago
                    }
                else:
                    date_display = {"raw": "Unknown"}
            except:
                date_display = {"raw": date}
            
            commit_items.append({
                "sha": sha,
                "message": message,
                "author": author,
                "date": date_display
            })

        return {
            "owner": owner,
            "repo": repo,
            "base_branch": base_branch,
            "compare_branch": compare_branch,
            "status": status,
            "ahead_by": ahead_by,
            "behind_by": behind_by,
            "total_commits": total_commits,
            "recent_commits": commit_items
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "error": "❌ Branch comparison not found - check if branches exist",
                "status_code": 404
            }
        return {
            "error": f"HTTP error {e.response.status_code}",
            "details": e.response.text
        }
    except Exception as e:
        return {
            "error": "Exception occurred while comparing branches",
            "details": str(e)
        }
