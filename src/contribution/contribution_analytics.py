import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from ..config import GITHUB_TOKEN, GITHUB_HEADERS, TIMEOUT


def get_user_contribution_analytics(username: str, days: int = 30) -> Dict[str, Any]:
    """
    Gathers raw user contribution data for Claude to analyze
    Returns structured data
    """
    if not GITHUB_TOKEN:
        return {"error": "GitHub token not configured"}
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Get user profile
            user_url = f"https://api.github.com/users/{username}"
            user_data = client.get(user_url, headers=GITHUB_HEADERS).json()
            
            # Get recent activity (last 100 events)
            events_url = f"https://api.github.com/users/{username}/events?per_page=100"
            events_data = client.get(events_url, headers=GITHUB_HEADERS).json()
            
            # Get repositories (first 100)
            repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
            repos_data = client.get(repos_url, headers=GITHUB_HEADERS).json()
            
            # Get recent commits across all repos
            since_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            commits_url = f"https://api.github.com/search/commits?q=author:{username}+committer-date:>={since_date}"
            commits_data = client.get(commits_url, headers=GITHUB_HEADERS).json().get("items", [])
            
            # Get recent PRs
            prs_url = f"https://api.github.com/search/issues?q=author:{username}+type:pr+created:>={since_date}"
            prs_data = client.get(prs_url, headers=GITHUB_HEADERS).json().get("items", [])
            
            # Get recent issues
            issues_url = f"https://api.github.com/search/issues?q=author:{username}+type:issue+created:>={since_date}"
            issues_data = client.get(issues_url, headers=GITHUB_HEADERS).json().get("items", [])

        return {
            "profile": {
                "username": user_data.get("login"),
                "name": user_data.get("name"),
                "public_repos": user_data.get("public_repos"),
                "followers": user_data.get("followers"),
                "created_at": user_data.get("created_at")
            },
            "activity": {
                "recent_events": [
                    {
                        "type": e.get("type"),
                        "repo": e.get("repo", {}).get("name"),
                        "created_at": e.get("created_at"),
                        "payload_action": e.get("payload", {}).get("action")
                    }
                    for e in events_data[:50]  # Limit to most recent 50 events
                ],
                "recent_commits": [
                    {
                        "sha": c.get("sha"),
                        "repo": c.get("repository", {}).get("full_name"),
                        "message": c.get("commit", {}).get("message"),
                        "date": c.get("commit", {}).get("author", {}).get("date")
                    }
                    for c in commits_data[:30]  # Limit to most recent 30 commits
                ],
                "recent_prs": [
                    {
                        "title": pr.get("title"),
                        "state": pr.get("state"),
                        "repo": pr.get("repository_url").split("/repos/")[-1],
                        "created_at": pr.get("created_at"),
                        "comments": pr.get("comments")
                    }
                    for pr in prs_data[:20]  # Limit to most recent 20 PRs
                ],
                "recent_issues": [
                    {
                        "title": issue.get("title"),
                        "state": issue.get("state"),
                        "repo": issue.get("repository_url").split("/repos/")[-1],
                        "created_at": issue.get("created_at"),
                        "comments": issue.get("comments")
                    }
                    for issue in issues_data[:20]  # Limit to most recent 20 issues
                ]
            },
            "repositories": {
                "total_count": len(repos_data),
                "recently_updated": [
                    {
                        "name": r.get("name"),
                        "full_name": r.get("full_name"),
                        "language": r.get("language"),
                        "stars": r.get("stargazers_count"),
                        "updated_at": r.get("updated_at")
                    }
                    for r in sorted(repos_data, key=lambda x: x.get("updated_at"), reverse=True)[:10]
                ],
                "most_starred": [
                    {
                        "name": r.get("name"),
                        "stars": r.get("stargazers_count"),
                        "language": r.get("language")
                    }
                    for r in sorted(repos_data, key=lambda x: x.get("stargazers_count"), reverse=True)[:5]
                ]
            },
            "analysis_period_days": days
        }

    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
    
def get_repository_contribution_analytics(owner: str, repo: str, days: int = 30) -> Dict[str, Any]:
    """
    Gathers raw repository contribution data for Claude to analyze
    Returns structured data
    """
    if not GITHUB_TOKEN:
        return {"error": "GitHub token not configured"}
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Get repo info
            repo_url = f"https://api.github.com/repos/{owner}/{repo}"
            repo_data = client.get(repo_url, headers=GITHUB_HEADERS).json()
            
            # Get contributors
            contributors_url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
            contributors_data = client.get(contributors_url, headers=GITHUB_HEADERS).json()
            
            # Get recent commits
            since_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits?since={since_date}"
            commits_data = client.get(commits_url, headers=GITHUB_HEADERS).json()
            
            # Get recent PRs
            prs_url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all&since={since_date}"
            prs_data = client.get(prs_url, headers=GITHUB_HEADERS).json()
            
            # Get recent issues
            issues_url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=all&since={since_date}"
            issues_data = client.get(issues_url, headers=GITHUB_HEADERS).json()

        return {
            "repository": {
                "name": repo_data.get("full_name"),
                "description": repo_data.get("description"),
                "stars": repo_data.get("stargazers_count"),
                "forks": repo_data.get("forks_count"),
                "open_issues": repo_data.get("open_issues"),
                "created_at": repo_data.get("created_at"),
                "updated_at": repo_data.get("updated_at")
            },
            "contributors": [
                {
                    "username": c.get("login"),
                    "contributions": c.get("contributions"),
                    "avatar_url": c.get("avatar_url")
                }
                for c in contributors_data[:20]  # Limit to top 20 contributors
            ],
            "recent_activity": {
                "commits": [
                    {
                        "sha": c.get("sha"),
                        "author": c.get("commit", {}).get("author", {}).get("name"),
                        "message": c.get("commit", {}).get("message"),
                        "date": c.get("commit", {}).get("author", {}).get("date")
                    }
                    for c in commits_data[:50]  # Limit to most recent 50 commits
                ],
                "pull_requests": [
                    {
                        "title": pr.get("title"),
                        "number": pr.get("number"),
                        "state": pr.get("state"),
                        "user": pr.get("user", {}).get("login"),
                        "created_at": pr.get("created_at"),
                        "comments": pr.get("comments")
                    }
                    for pr in prs_data[:20]  # Limit to most recent 20 PRs
                ],
                "issues": [
                    {
                        "title": issue.get("title"),
                        "number": issue.get("number"),
                        "state": issue.get("state"),
                        "user": issue.get("user", {}).get("login"),
                        "created_at": issue.get("created_at"),
                        "comments": issue.get("comments")
                    }
                    for issue in issues_data if "pull_request" not in issue  # Filter out PRs
                ][:20]  # Limit to most recent 20 issues
            },
            "analysis_period_days": days
        }

    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
    