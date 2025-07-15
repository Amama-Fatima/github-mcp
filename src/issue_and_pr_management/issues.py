import httpx
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

def get_issue_with_comments(owner: str, repo: str, issue_number: int) -> dict:
    """
    Get issue details along with all comments for comprehensive analysis
    """
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Fetch the issue details
            issue_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
            issue_r = client.get(issue_url, headers=GITHUB_HEADERS)
            issue_r.raise_for_status()
            issue_data = issue_r.json()
            
            # Fetch the comments
            comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
            comments_r = client.get(comments_url, headers=GITHUB_HEADERS)
            comments_r.raise_for_status()
            comments = comments_r.json()
            
            # Format issue data
            formatted_issue = {
                "number": issue_data.get("number"),
                "title": issue_data.get("title"),
                "body": issue_data.get("body", ""),
                "state": issue_data.get("state"),
                "author": issue_data.get("user", {}).get("login"),
                "created_at": issue_data.get("created_at"),
                "updated_at": issue_data.get("updated_at"),
                "closed_at": issue_data.get("closed_at"),
                "labels": [label.get("name") for label in issue_data.get("labels", [])],
                "assignees": [assignee.get("login") for assignee in issue_data.get("assignees", [])],
                "milestone": issue_data.get("milestone", {}).get("title") if issue_data.get("milestone") else None,
                "comments_count": issue_data.get("comments", 0),
                "reactions": {
                    "total": issue_data.get("reactions", {}).get("total_count", 0),
                    "thumbs_up": issue_data.get("reactions", {}).get("+1", 0),
                    "thumbs_down": issue_data.get("reactions", {}).get("-1", 0),
                    "laugh": issue_data.get("reactions", {}).get("laugh", 0),
                    "hooray": issue_data.get("reactions", {}).get("hooray", 0),
                    "confused": issue_data.get("reactions", {}).get("confused", 0),
                    "heart": issue_data.get("reactions", {}).get("heart", 0),
                    "rocket": issue_data.get("reactions", {}).get("rocket", 0),
                    "eyes": issue_data.get("reactions", {}).get("eyes", 0)
                },
                "html_url": issue_data.get("html_url"),
                "locked": issue_data.get("locked", False),
                "active_lock_reason": issue_data.get("active_lock_reason")
            }
            
            # Format comments
            formatted_comments = []
            for comment in comments:
                formatted_comments.append({
                    "id": comment.get("id"),
                    "author": comment.get("user", {}).get("login"),
                    "body": comment.get("body", ""),
                    "created_at": comment.get("created_at"),
                    "updated_at": comment.get("updated_at"),
                    "reactions": {
                        "total": comment.get("reactions", {}).get("total_count", 0),
                        "thumbs_up": comment.get("reactions", {}).get("+1", 0),
                        "thumbs_down": comment.get("reactions", {}).get("-1", 0),
                        "laugh": comment.get("reactions", {}).get("laugh", 0),
                        "hooray": comment.get("reactions", {}).get("hooray", 0),
                        "confused": comment.get("reactions", {}).get("confused", 0),
                        "heart": comment.get("reactions", {}).get("heart", 0),
                        "rocket": comment.get("reactions", {}).get("rocket", 0),
                        "eyes": comment.get("reactions", {}).get("eyes", 0)
                    },
                    "html_url": comment.get("html_url")
                })
            
            return {
                "owner": owner,
                "repo": repo,
                "issue_number": issue_number,
                "issue": formatted_issue,
                "comments": formatted_comments,
                "total_comments": len(formatted_comments),
                "claude_analysis_prompt": """
                You have both the original issue and all its comments. Please analyze this complete thread to:

                1. **Issue Summary**: Provide a concise summary of what the issue is about
                2. **Current Status**: Based on the issue state, labels, and comment thread, what's the current status?
                3. **Key Participants**: Who are the main contributors to this discussion?
                4. **Resolution Progress**: Has progress been made? Are there proposed solutions?
                5. **Community Engagement**: How much interest/activity is there around this issue?
                6. **Priority Assessment**: Based on reactions, labels, and discussion, how urgent/important is this?
                7. **Next Steps**: What actions would move this issue forward?
                8. **Classification**: What type of issue is this (bug, feature request, documentation, etc.)?

                Consider both the original issue content and the evolution of the discussion in the comments.
                """
            }
            
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}",
            "details": e.response.text,
            "owner": owner,
            "repo": repo,
            "issue_number": issue_number
        }
    except Exception as e:
        return {
            "error": "Exception occurred while fetching issue and comments",
            "details": str(e),
            "owner": owner,
            "repo": repo,
            "issue_number": issue_number
        }    
    