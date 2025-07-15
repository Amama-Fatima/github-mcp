import httpx
from datetime import datetime, timezone
from typing import Dict, List, Optional
from ..config import GITHUB_TOKEN, GITHUB_HEADERS, TIMEOUT


def smart_issue_triage(owner: str, repo: str, issue_number: int) -> dict:
    """
    Fetch issue data and return it for Claude to analyze and categorize
    """
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}
    
    try:
        # Get issue details
        issue_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
        
        with httpx.Client(timeout=TIMEOUT) as client:
            issue_r = client.get(issue_url, headers=GITHUB_HEADERS)
            issue_r.raise_for_status()
            issue = issue_r.json()
            
            # Get existing labels
            existing_labels = [label["name"] for label in issue.get("labels", [])]
            
            # Get repository labels to check what's available
            labels_url = f"https://api.github.com/repos/{owner}/{repo}/labels"
            labels_r = client.get(labels_url, headers=GITHUB_HEADERS)
            labels_r.raise_for_status()
            repo_labels = [label["name"] for label in labels_r.json()]
            
            # Get recent issues for context (optional)
            recent_issues_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
            recent_r = client.get(recent_issues_url, headers=GITHUB_HEADERS, 
                                params={"state": "all", "per_page": 10})
            recent_r.raise_for_status()
            recent_issues = recent_r.json()
            
            # Format recent issues for context
            recent_context = []
            for recent in recent_issues[:5]:  # Just top 5 for context
                if recent.get("number") != issue_number:
                    recent_context.append({
                        "number": recent.get("number"),
                        "title": recent.get("title"),
                        "labels": [l["name"] for l in recent.get("labels", [])]
                    })
            
            return {
                "owner": owner,
                "repo": repo,
                "issue_number": issue_number,
                "title": issue.get("title"),
                "body": issue.get("body", ""),
                "author": issue.get("user", {}).get("login"),
                "created_at": issue.get("created_at"),
                "updated_at": issue.get("updated_at"),
                "state": issue.get("state"),
                "existing_labels": existing_labels,
                "available_repo_labels": repo_labels,
                "recent_issues_context": recent_context,
                "url": issue.get("html_url"),
                "claude_analysis_prompt": """
                Please analyze this GitHub issue and provide:

                1. **Issue Type Classification**: Categorize as 'bug', 'feature', 'question', 'documentation', or 'other'
                2. **Priority Level**: Assign 'low', 'medium', or 'high' priority
                3. **Confidence Score**: Rate your confidence in the classification (0-100%)
                4. **Suggested Labels**: Recommend specific labels from the available repository labels
                5. **Reasoning**: Explain your classification decisions
                6. **Additional Insights**: Any other relevant observations

                Consider the issue title, body content, existing labels, and the context of recent issues in the repository. Focus on the language used, problem description, and request type.

                After your analysis, if you determine labels should be applied, please call the `apply_issue_labels_tool` function with the recommended labels.
                """
            }
            
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}",
            "details": e.response.text
        }
    except Exception as e:
        return {
            "error": "Exception occurred during issue triage",
            "details": str(e)
        }


def apply_issue_labels_tool(owner: str, repo: str, issue_number: int, labels: list) -> dict:
    """
    Apply labels to an issue
    """
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}
    
    try:
        labels_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels"
        
        with httpx.Client(timeout=TIMEOUT) as client:
            # First, let's get current labels to avoid duplicates
            current_r = client.get(f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}", 
                                 headers=GITHUB_HEADERS)
            current_r.raise_for_status()
            current_labels = [label["name"] for label in current_r.json().get("labels", [])]
            
            # Add only new labels
            new_labels = [label for label in labels if label not in current_labels]
            
            if new_labels:
                # Add new labels (this appends to existing ones)
                response = client.post(labels_url, headers=GITHUB_HEADERS, json=new_labels)
                response.raise_for_status()
                
                return {
                    "owner": owner,
                    "repo": repo,
                    "issue_number": issue_number,
                    "labels_added": new_labels,
                    "existing_labels": current_labels,
                    "success": True,
                    "message": f"Successfully applied {len(new_labels)} new labels"
                }
            else:
                return {
                    "owner": owner,
                    "repo": repo,
                    "issue_number": issue_number,
                    "labels_added": [],
                    "existing_labels": current_labels,
                    "success": True,
                    "message": "No new labels to apply - all suggested labels already exist"
                }
            
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}",
            "details": e.response.text
        }
    except Exception as e:
        return {
            "error": "Exception occurred while applying labels",
            "details": str(e)
        }


def bulk_issue_triage(owner: str, repo: str, limit: int = 10, state: str = "open") -> dict:
    """
    Fetch multiple issues for Claude to analyze in bulk
    """
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}
    
    try:
        issues_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        
        with httpx.Client(timeout=TIMEOUT) as client:
            issues_r = client.get(issues_url, headers=GITHUB_HEADERS, 
                                params={"state": state, "per_page": limit})
            issues_r.raise_for_status()
            issues = issues_r.json()
            
            # Get repository labels
            labels_url = f"https://api.github.com/repos/{owner}/{repo}/labels"
            labels_r = client.get(labels_url, headers=GITHUB_HEADERS)
            labels_r.raise_for_status()
            repo_labels = [label["name"] for label in labels_r.json()]
            
            # Filter out PRs and format issues
            issue_data = []
            for issue in issues:
                if issue.get("pull_request"):  # Skip PRs
                    continue
                    
                issue_data.append({
                    "number": issue.get("number"),
                    "title": issue.get("title"),
                    "body": issue.get("body", "")[:500],  # First 500 chars
                    "author": issue.get("user", {}).get("login"),
                    "existing_labels": [label["name"] for label in issue.get("labels", [])],
                    "created_at": issue.get("created_at"),
                    "url": issue.get("html_url")
                })
            
            return {
                "owner": owner,
                "repo": repo,
                "total_issues": len(issue_data),
                "available_repo_labels": repo_labels,
                "issues": issue_data,
                "claude_analysis_prompt": """
                Please analyze these GitHub issues in bulk and provide:

                1. **Overall Repository Health**: What patterns do you see in the issues?
                2. **Issue Breakdown**: For each issue, provide:
                - Issue type (bug/feature/question/documentation/other)
                - Priority level (low/medium/high)
                - Suggested labels from available repository labels
                - Brief reasoning
                3. **Triage Summary**: 
                - Count by type and priority
                - Most urgent issues that need immediate attention
                - Issues that could be good for new contributors
                4. **Repository Insights**: Any patterns or recommendations for the maintainers

                For issues that need labels applied, please call the `apply_issue_labels_tool` function for each one after your analysis.
                """
            }
            
    except Exception as e:
        return {
            "error": "Exception occurred during bulk triage",
            "details": str(e)
        }


def get_issue_comments(owner: str, repo: str, issue_number: int) -> dict:
    """
    Get comments for an issue to provide additional context for analysis
    """
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}
    
    try:
        comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
        
        with httpx.Client(timeout=TIMEOUT) as client:
            comments_r = client.get(comments_url, headers=GITHUB_HEADERS)
            comments_r.raise_for_status()
            comments = comments_r.json()
            
            formatted_comments = []
            for comment in comments:
                formatted_comments.append({
                    "author": comment.get("user", {}).get("login"),
                    "body": comment.get("body", ""),
                    "created_at": comment.get("created_at"),
                    "updated_at": comment.get("updated_at")
                })
            
            return {
                "owner": owner,
                "repo": repo,
                "issue_number": issue_number,
                "comments_count": len(formatted_comments),
                "comments": formatted_comments,
                "claude_analysis_prompt": """
                These are the comments on the GitHub issue. Please analyze them to:

                1. **Additional Context**: What extra information do the comments provide?
                2. **Issue Status**: Has the issue been resolved, is someone working on it, or is it stalled?
                3. **Community Engagement**: How active is the discussion?
                4. **Updated Classification**: Does the comment thread change your initial issue classification?
                5. **Action Items**: Are there specific actions mentioned that need to be taken?

                Use this information to refine your issue analysis and recommendations.
                """
            }
            
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}",
            "details": e.response.text
        }
    except Exception as e:
        return {
            "error": "Exception occurred while fetching comments",
            "details": str(e)
        }