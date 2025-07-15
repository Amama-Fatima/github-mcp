import httpx
from datetime import datetime, timezone
from typing import Dict, List, Any
from ..config import GITHUB_TOKEN, GITHUB_HEADERS, TIMEOUT


def get_pr_review_summary(owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
    """
    Get comprehensive PR review summary with changes analysis
    """
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Get PR details
            pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
            pr_response = client.get(pr_url, headers=GITHUB_HEADERS)
            pr_response.raise_for_status()
            pr_data = pr_response.json()
            
            # Get PR files (changed files)
            files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
            files_response = client.get(files_url, headers=GITHUB_HEADERS)
            files_response.raise_for_status()
            files_data = files_response.json()
            
            # Get PR commits
            commits_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/commits"
            commits_response = client.get(commits_url, headers=GITHUB_HEADERS)
            commits_response.raise_for_status()
            commits_data = commits_response.json()
            
            # Get PR reviews
            reviews_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
            reviews_response = client.get(reviews_url, headers=GITHUB_HEADERS)
            reviews_response.raise_for_status()
            reviews_data = reviews_response.json()
            
            # Get PR comments
            comments_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments"
            comments_response = client.get(comments_url, headers=GITHUB_HEADERS)
            comments_response.raise_for_status()
            comments_data = comments_response.json()
        
        # Process and analyze the data
        return _analyze_pr_data(pr_data, files_data, commits_data, reviews_data, comments_data)
        
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}",
            "details": e.response.text
        }
    except Exception as e:
        return {
            "error": "Exception occurred while fetching PR data",
            "details": str(e)
        }


def _analyze_pr_data(pr_data: Dict, files_data: List, commits_data: List, 
                    reviews_data: List, comments_data: List) -> Dict[str, Any]:
    """
    Analyze PR data and generate comprehensive summary
    """
    # Basic PR info
    pr_info = {
        "number": pr_data.get("number"),
        "title": pr_data.get("title"),
        "state": pr_data.get("state"),
        "merged": pr_data.get("merged", False),
        "mergeable": pr_data.get("mergeable"),
        "author": pr_data.get("user", {}).get("login"),
        "created_at": pr_data.get("created_at"),
        "updated_at": pr_data.get("updated_at"),
        "base_branch": pr_data.get("base", {}).get("ref"),
        "head_branch": pr_data.get("head", {}).get("ref"),
        "url": pr_data.get("html_url"),
        "description": pr_data.get("body", "")
    }
    
    # Analyze file changes
    file_analysis = _analyze_file_changes(files_data)
    
    # Analyze commits
    commit_analysis = _analyze_commits(commits_data)
    
    # Analyze reviews
    review_analysis = _analyze_reviews(reviews_data)
    
    # Analyze comments
    comment_analysis = _analyze_comments(comments_data)
    
    # Generate summary insights
    insights = _generate_insights(pr_info, file_analysis, commit_analysis, review_analysis)
    
    return {
        "pr_info": pr_info,
        "file_changes": file_analysis,
        "commits": commit_analysis,
        "reviews": review_analysis,
        "comments": comment_analysis,
        "insights": insights
    }


def _analyze_file_changes(files_data: List) -> Dict[str, Any]:
    """
    Analyze changed files and generate statistics
    """
    if not files_data:
        return {"total_files": 0, "changes": []}
    
    total_additions = 0
    total_deletions = 0
    file_types = {}
    languages = {}
    large_files = []
    
    changes = []
    
    for file in files_data:
        filename = file.get("filename", "")
        additions = file.get("additions", 0)
        deletions = file.get("deletions", 0)
        changes_count = file.get("changes", 0)
        status = file.get("status", "")
        
        total_additions += additions
        total_deletions += deletions
        
        # File extension analysis
        if "." in filename:
            ext = filename.split(".")[-1].lower()
            file_types[ext] = file_types.get(ext, 0) + 1
        
        # Language detection (basic)
        language = _detect_language(filename)
        if language:
            languages[language] = languages.get(language, 0) + 1
        
        # Flag large changes
        if changes_count > 100:
            large_files.append({
                "filename": filename,
                "changes": changes_count,
                "status": status
            })
        
        changes.append({
            "filename": filename,
            "status": status,
            "additions": additions,
            "deletions": deletions,
            "changes": changes_count,
            "language": language
        })
    
    return {
        "total_files": len(files_data),
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "net_changes": total_additions - total_deletions,
        "file_types": file_types,
        "languages": languages,
        "large_files": large_files,
        "changes": changes
    }


def _analyze_commits(commits_data: List) -> Dict[str, Any]:
    """
    Analyze commit history in the PR
    """
    if not commits_data:
        return {"total_commits": 0, "commits": []}
    
    commits = []
    authors = {}
    
    for commit in commits_data:
        commit_info = commit.get("commit", {})
        author = commit_info.get("author", {})
        author_name = author.get("name", "Unknown")
        
        authors[author_name] = authors.get(author_name, 0) + 1
        
        commits.append({
            "sha": commit.get("sha", "")[:7],
            "message": commit_info.get("message", "").split('\n')[0],
            "author": author_name,
            "date": author.get("date"),
            "url": commit.get("html_url")
        })
    
    return {
        "total_commits": len(commits_data),
        "unique_authors": len(authors),
        "authors": authors,
        "commits": commits
    }


def _analyze_reviews(reviews_data: List) -> Dict[str, Any]:
    """
    Analyze PR reviews
    """
    if not reviews_data:
        return {"total_reviews": 0, "reviews": []}
    
    reviews = []
    review_states = {}
    reviewers = {}
    
    for review in reviews_data:
        state = review.get("state", "")
        reviewer = review.get("user", {}).get("login", "Unknown")
        
        review_states[state] = review_states.get(state, 0) + 1
        reviewers[reviewer] = reviewers.get(reviewer, 0) + 1
        
        reviews.append({
            "id": review.get("id"),
            "state": state,
            "reviewer": reviewer,
            "body": review.get("body", ""),
            "submitted_at": review.get("submitted_at"),
            "url": review.get("html_url")
        })
    
    return {
        "total_reviews": len(reviews_data),
        "review_states": review_states,
        "reviewers": reviewers,
        "reviews": reviews
    }


def _analyze_comments(comments_data: List) -> Dict[str, Any]:
    """
    Analyze PR comments
    """
    if not comments_data:
        return {"total_comments": 0, "comments": []}
    
    comments = []
    commenters = {}
    
    for comment in comments_data:
        commenter = comment.get("user", {}).get("login", "Unknown")
        commenters[commenter] = commenters.get(commenter, 0) + 1
        
        comments.append({
            "id": comment.get("id"),
            "body": comment.get("body", ""),
            "author": commenter,
            "created_at": comment.get("created_at"),
            "path": comment.get("path"),
            "line": comment.get("line"),
            "url": comment.get("html_url")
        })
    
    return {
        "total_comments": len(comments_data),
        "commenters": commenters,
        "comments": comments
    }


def _detect_language(filename: str) -> str:
    """
    Simple language detection based on file extension
    """
    ext_map = {
        "py": "Python",
        "js": "JavaScript",
        "ts": "TypeScript",
        "java": "Java",
        "cpp": "C++",
        "c": "C",
        "cs": "C#",
        "php": "PHP",
        "rb": "Ruby",
        "go": "Go",
        "rs": "Rust",
        "swift": "Swift",
        "kt": "Kotlin",
        "html": "HTML",
        "css": "CSS",
        "scss": "SCSS",
        "sass": "Sass",
        "json": "JSON",
        "xml": "XML",
        "yaml": "YAML",
        "yml": "YAML",
        "md": "Markdown",
        "sh": "Shell",
        "sql": "SQL"
    }
    
    if "." in filename:
        ext = filename.split(".")[-1].lower()
        return ext_map.get(ext, "Unknown")
    
    return "Unknown"


def _generate_insights(pr_info: Dict, file_analysis: Dict, commit_analysis: Dict, review_analysis: Dict) -> Dict[str, Any]:
    """
    Generate actionable insights about the PR
    """
    insights = {
        "complexity_score": _calculate_complexity_score(file_analysis, commit_analysis),
        "review_status": _assess_review_status(review_analysis),
        "risk_factors": _identify_risk_factors(pr_info, file_analysis, commit_analysis),
        "recommendations": _generate_recommendations(pr_info, file_analysis, commit_analysis, review_analysis)
    }
    
    return insights


def _calculate_complexity_score(file_analysis: Dict, commit_analysis: Dict) -> Dict[str, Any]:
    """
    Calculate PR complexity score (0-100)
    """
    score = 0
    factors = []
    
    # File count factor
    file_count = file_analysis.get("total_files", 0)
    if file_count > 20:
        score += 30
        factors.append("High file count")
    elif file_count > 10:
        score += 15
        factors.append("Moderate file count")
    
    # Changes factor
    total_changes = file_analysis.get("total_additions", 0) + file_analysis.get("total_deletions", 0)
    if total_changes > 1000:
        score += 40
        factors.append("Large number of changes")
    elif total_changes > 500:
        score += 20
        factors.append("Moderate number of changes")
    
    # Language diversity
    lang_count = len(file_analysis.get("languages", {}))
    if lang_count > 3:
        score += 15
        factors.append("Multiple languages")
    
    # Large files
    large_files = len(file_analysis.get("large_files", []))
    if large_files > 0:
        score += 15
        factors.append("Large file changes")
    
    # Commit count
    commit_count = commit_analysis.get("total_commits", 0)
    if commit_count > 10:
        score += 10
        factors.append("Many commits")
    
    return {
        "score": min(score, 100),
        "level": "High" if score > 70 else "Medium" if score > 30 else "Low",
        "factors": factors
    }


def _assess_review_status(review_analysis: Dict) -> Dict[str, Any]:
    """
    Assess the review status of the PR
    """
    states = review_analysis.get("review_states", {})
    total_reviews = review_analysis.get("total_reviews", 0)
    
    approved = states.get("APPROVED", 0)
    changes_requested = states.get("CHANGES_REQUESTED", 0)
    commented = states.get("COMMENTED", 0)
    
    if approved > 0 and changes_requested == 0:
        status = "Ready to merge"
    elif changes_requested > 0:
        status = "Changes requested"
    elif total_reviews > 0:
        status = "Under review"
    else:
        status = "Awaiting review"
    
    return {
        "status": status,
        "approved_count": approved,
        "changes_requested_count": changes_requested,
        "comment_count": commented,
        "total_reviews": total_reviews
    }


def _identify_risk_factors(pr_info: Dict, file_analysis: Dict, commit_analysis: Dict) -> List[str]:
    """
    Identify potential risk factors in the PR
    """
    risks = []
    
    # Large PR
    if file_analysis.get("total_files", 0) > 20:
        risks.append("Large PR - consider breaking into smaller PRs")
    
    # Mixed changes
    languages = file_analysis.get("languages", {})
    if len(languages) > 3:
        risks.append("Multiple languages modified - ensure consistent changes")
    
    # Large files
    if file_analysis.get("large_files"):
        risks.append("Large files modified - review carefully for maintainability")
    
    # No description
    if not pr_info.get("description", "").strip():
        risks.append("No PR description - add context for reviewers")
    
    # Many commits
    if commit_analysis.get("total_commits", 0) > 15:
        risks.append("Many commits - consider squashing")
    
    # Mergeable status
    if pr_info.get("mergeable") is False:
        risks.append("PR has merge conflicts - resolve before merging")
    
    return risks


def _generate_recommendations(pr_info: Dict, file_analysis: Dict, commit_analysis: Dict, review_analysis: Dict) -> List[str]:
    """
    Generate actionable recommendations
    """
    recommendations = []
    
    # Review recommendations
    if review_analysis.get("total_reviews", 0) == 0:
        recommendations.append("Request reviews from relevant team members")
    
    # Documentation
    if not pr_info.get("description", "").strip():
        recommendations.append("Add detailed PR description explaining changes")
    
    # Testing
    test_files = [f for f in file_analysis.get("changes", []) if "test" in f.get("filename", "").lower()]
    if not test_files and file_analysis.get("total_files", 0) > 0:
        recommendations.append("Consider adding tests for new functionality")
    
    # Size management
    if file_analysis.get("total_files", 0) > 20:
        recommendations.append("Consider breaking large PR into smaller, focused PRs")
    
    # Commit hygiene
    if commit_analysis.get("total_commits", 0) > 10:
        recommendations.append("Consider squashing commits for cleaner history")
    
    return recommendations

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