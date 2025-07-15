import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
from collections import defaultdict
from ..config import GITHUB_TOKEN, GITHUB_HEADERS, TIMEOUT


def get_user_contribution_analytics(username: str, days: int = 30, include_private: bool = False) -> Dict[str, Any]:
    """
    Get comprehensive contribution analytics for a user
    """
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Get user info
            user_url = f"https://api.github.com/users/{username}"
            user_response = client.get(user_url, headers=GITHUB_HEADERS)
            user_response.raise_for_status()
            user_data = user_response.json()
            
            # Get user's repositories
            repos_url = f"https://api.github.com/users/{username}/repos"
            repos_params = {
                "per_page": 100,
                "sort": "updated",
                "type": "all" if include_private else "public"
            }
            repos_response = client.get(repos_url, headers=GITHUB_HEADERS, params=repos_params)
            repos_response.raise_for_status()
            repos_data = repos_response.json()
            
            # Get user's events (recent activity)
            events_url = f"https://api.github.com/users/{username}/events"
            events_response = client.get(events_url, headers=GITHUB_HEADERS, params={"per_page": 100})
            events_response.raise_for_status()
            events_data = events_response.json()
            
            # Get user's starred repos
            starred_url = f"https://api.github.com/users/{username}/starred"
            starred_response = client.get(starred_url, headers=GITHUB_HEADERS, params={"per_page": 100})
            starred_response.raise_for_status()
            starred_data = starred_response.json()
        
        # Analyze the data
        return _analyze_user_contributions(user_data, repos_data, events_data, starred_data, days)
        
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}",
            "details": e.response.text
        }
    except Exception as e:
        return {
            "error": "Exception occurred while fetching contribution data",
            "details": str(e)
        }


def get_repository_contribution_analytics(owner: str, repo: str, days: int = 30) -> Dict[str, Any]:
    """
    Get contribution analytics for a specific repository
    """
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Get repository info
            repo_url = f"https://api.github.com/repos/{owner}/{repo}"
            repo_response = client.get(repo_url, headers=GITHUB_HEADERS)
            repo_response.raise_for_status()
            repo_data = repo_response.json()
            
            # Get contributors
            contributors_url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
            contributors_response = client.get(contributors_url, headers=GITHUB_HEADERS, params={"per_page": 100})
            contributors_response.raise_for_status()
            contributors_data = contributors_response.json()
            
            # Get recent commits
            since_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
            commits_response = client.get(commits_url, headers=GITHUB_HEADERS, 
                                        params={"since": since_date, "per_page": 100})
            commits_response.raise_for_status()
            commits_data = commits_response.json()
            
            # Get pull requests
            prs_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            prs_response = client.get(prs_url, headers=GITHUB_HEADERS, 
                                    params={"state": "all", "per_page": 100})
            prs_response.raise_for_status()
            prs_data = prs_response.json()
            
            # Get issues
            issues_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
            issues_response = client.get(issues_url, headers=GITHUB_HEADERS, 
                                       params={"state": "all", "per_page": 100})
            issues_response.raise_for_status()
            issues_data = issues_response.json()
        
        # Analyze repository contributions
        return _analyze_repository_contributions(repo_data, contributors_data, commits_data, prs_data, issues_data, days)
        
    except httpx.HTTPStatusError as e:
        return {
            "error": f"HTTP error {e.response.status_code}",
            "details": e.response.text
        }
    except Exception as e:
        return {
            "error": "Exception occurred while fetching repository data",
            "details": str(e)
        }


# Helper functions for analysis
def _analyze_user_contributions(user_data: Dict, repos_data: List, events_data: List, 
                              starred_data: List, days: int) -> Dict[str, Any]:
    """
    Analyze user contribution data
    """
    # User profile info
    profile = {
        "username": user_data.get("login"),
        "name": user_data.get("name"),
        "bio": user_data.get("bio"),
        "location": user_data.get("location"),
        "company": user_data.get("company"),
        "blog": user_data.get("blog"),
        "public_repos": user_data.get("public_repos", 0),
        "public_gists": user_data.get("public_gists", 0),
        "followers": user_data.get("followers", 0),
        "following": user_data.get("following", 0),
        "created_at": user_data.get("created_at"),
        "updated_at": user_data.get("updated_at")
    }
    
    # Repository analytics
    repo_analytics = _analyze_user_repositories(repos_data)
    
    # Activity analytics
    activity_analytics = _analyze_user_activity(events_data, days)
    
    # Language analytics
    language_analytics = _analyze_user_languages(repos_data)
    
    # Collaboration analytics
    collaboration_analytics = _analyze_collaboration_metrics(repos_data, events_data)
    
    # Starred repositories analysis
    starred_analytics = _analyze_starred_repos(starred_data)
    
    return {
        "profile": profile,
        "repositories": repo_analytics,
        "activity": activity_analytics,
        "languages": language_analytics,
        "collaboration": collaboration_analytics,
        "starred": starred_analytics,
        "analysis_period_days": days
    }


def _analyze_user_repositories(repos_data: List) -> Dict[str, Any]:
    """
    Analyze user's repositories
    """
    if not repos_data:
        return {"total_repos": 0}
    
    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos_data)
    total_forks = sum(repo.get("forks_count", 0) for repo in repos_data)
    total_watchers = sum(repo.get("watchers_count", 0) for repo in repos_data)
    
    # Most popular repos
    popular_repos = sorted(repos_data, key=lambda x: x.get("stargazers_count", 0), reverse=True)[:10]
    
    # Recently updated repos
    recent_repos = sorted(repos_data, key=lambda x: x.get("updated_at", ""), reverse=True)[:10]
    
    # Repository languages
    languages = defaultdict(int)
    for repo in repos_data:
        lang = repo.get("language")
        if lang:
            languages[lang] += 1
    
    # Repository types
    owned_repos = [repo for repo in repos_data if not repo.get("fork", False)]
    forked_repos = [repo for repo in repos_data if repo.get("fork", False)]
    
    return {
        "total_repos": len(repos_data),
        "owned_repos": len(owned_repos),
        "forked_repos": len(forked_repos),
        "total_stars_received": total_stars,
        "total_forks_received": total_forks,
        "total_watchers": total_watchers,
        "average_stars_per_repo": round(total_stars / len(repos_data), 2) if repos_data else 0,
        "languages": dict(languages),
        "most_popular_repos": [
            {
                "name": repo.get("name"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "language": repo.get("language"),
                "description": repo.get("description", "")[:100]
            }
            for repo in popular_repos[:5]
        ],
        "recently_updated": [
            {
                "name": repo.get("name"),
                "updated_at": repo.get("updated_at"),
                "language": repo.get("language"),
                "description": repo.get("description", "")[:100]
            }
            for repo in recent_repos[:5]
        ]
    }


def _analyze_user_activity(events_data: List, days: int) -> Dict[str, Any]:
    """
    Analyze user activity patterns
    """
    if not events_data:
        return {"total_events": 0}
    
    # Filter events by date range
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    recent_events = [
        event for event in events_data
        if datetime.fromisoformat(event.get("created_at", "").replace('Z', '+00:00')) > cutoff_date
    ]
    
    # Activity by type
    activity_types = defaultdict(int)
    for event in recent_events:
        activity_types[event.get("type", "Unknown")] += 1
    
    # Activity by day
    daily_activity = defaultdict(int)
    for event in recent_events:
        date = datetime.fromisoformat(event.get("created_at", "").replace('Z', '+00:00'))
        day_key = date.strftime("%Y-%m-%d")
        daily_activity[day_key] += 1
    
    # Activity by hour (for pattern analysis)
    hourly_activity = defaultdict(int)
    for event in recent_events:
        date = datetime.fromisoformat(event.get("created_at", "").replace('Z', '+00:00'))
        hour = date.hour
        hourly_activity[hour] += 1
    
    # Most active repositories
    repo_activity = defaultdict(int)
    for event in recent_events:
        repo_name = event.get("repo", {}).get("name", "Unknown")
        repo_activity[repo_name] += 1
    
    # Calculate streaks and patterns
    activity_streak = _calculate_activity_streak(daily_activity)
    
    return {
        "total_events": len(recent_events),
        "activity_types": dict(activity_types),
        "daily_activity": dict(daily_activity),
        "hourly_patterns": dict(hourly_activity),
        "most_active_repos": dict(sorted(repo_activity.items(), key=lambda x: x[1], reverse=True)[:10]),
        "activity_streak": activity_streak,
        "average_daily_activity": round(len(recent_events) / days, 2) if days > 0 else 0,
        "most_active_hour": max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else None,
        "activity_score": _calculate_activity_score(recent_events, days)
    }


def _analyze_user_languages(repos_data: List) -> Dict[str, Any]:
    """
    Analyze programming languages used
    """
    languages = defaultdict(int)
    language_repos = defaultdict(list)
    
    for repo in repos_data:
        lang = repo.get("language")
        if lang:
            languages[lang] += 1
            language_repos[lang].append({
                "name": repo.get("name"),
                "stars": repo.get("stargazers_count", 0),
                "updated_at": repo.get("updated_at")
            })
    
    # Calculate language diversity
    total_repos = len([repo for repo in repos_data if repo.get("language")])
    language_diversity = len(languages) / total_repos if total_repos > 0 else 0
    
    # Most popular language by stars
    lang_popularity = {}
    for lang, repos in language_repos.items():
        total_stars = sum(repo["stars"] for repo in repos)
        lang_popularity[lang] = total_stars
    
    return {
        "total_languages": len(languages),
        "language_distribution": dict(languages),
        "language_diversity_score": round(language_diversity, 2),
        "most_used_language": max(languages.items(), key=lambda x: x[1])[0] if languages else None,
        "most_popular_by_stars": max(lang_popularity.items(), key=lambda x: x[1])[0] if lang_popularity else None,
        "language_repos": {
            lang: sorted(repos, key=lambda x: x["stars"], reverse=True)[:3]
            for lang, repos in language_repos.items()
        }
    }


def _analyze_collaboration_metrics(repos_data: List, events_data: List) -> Dict[str, Any]:
    """
    Analyze collaboration patterns
    """
    # Count collaborators across repositories
    fork_count = len([repo for repo in repos_data if repo.get("fork", False)])
    
    # Analyze PR and issue events
    pr_events = [event for event in events_data if event.get("type") == "PullRequestEvent"]
    issue_events = [event for event in events_data if event.get("type") == "IssuesEvent"]
    
    # Count unique repositories contributed to
    contributed_repos = set()
    for event in events_data:
        repo_name = event.get("repo", {}).get("name")
        if repo_name:
            contributed_repos.add(repo_name)
    
    return {
        "total_forks_created": fork_count,
        "recent_pr_activity": len(pr_events),
        "recent_issue_activity": len(issue_events),
        "unique_repos_contributed": len(contributed_repos),
        "collaboration_score": _calculate_collaboration_score(fork_count, pr_events, issue_events),
        "contribution_diversity": len(contributed_repos) / len(repos_data) if repos_data else 0
    }


def _analyze_starred_repos(starred_data: List) -> Dict[str, Any]:
    """
    Analyze starred repositories for interests
    """
    if not starred_data:
        return {"total_starred": 0}
    
    # Language interests
    starred_languages = defaultdict(int)
    for repo in starred_data:
        lang = repo.get("language")
        if lang:
            starred_languages[lang] += 1
    
    # Topic interests (if available)
    topics = defaultdict(int)
    for repo in starred_data:
        repo_topics = repo.get("topics", [])
        for topic in repo_topics:
            topics[topic] += 1
    
    # Most starred repositories
    popular_starred = sorted(starred_data, key=lambda x: x.get("stargazers_count", 0), reverse=True)[:10]
    
    return {
        "total_starred": len(starred_data),
        "language_interests": dict(starred_languages),
        "topic_interests": dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]),
        "most_popular_starred": [
            {
                "name": repo.get("full_name"),
                "stars": repo.get("stargazers_count", 0),
                "language": repo.get("language"),
                "description": repo.get("description", "")[:100]
            }
            for repo in popular_starred[:5]
        ]
    }


def _analyze_repository_contributions(repo_data: Dict, contributors_data: List, 
                                   commits_data: List, prs_data: List, 
                                   issues_data: List, days: int) -> Dict[str, Any]:
    """
    Analyze contributions to a specific repository
    """
    # Repository info
    repo_info = {
        "name": repo_data.get("full_name"),
        "description": repo_data.get("description"),
        "language": repo_data.get("language"),
        "stars": repo_data.get("stargazers_count", 0),
        "forks": repo_data.get("forks_count", 0),
        "watchers": repo_data.get("watchers_count", 0),
        "open_issues": repo_data.get("open_issues_count", 0),
        "created_at": repo_data.get("created_at"),
        "updated_at": repo_data.get("updated_at")
    }
    
    # Contributor analysis
    contributors_analysis = _analyze_contributors(contributors_data)
    
    # Commit analysis
    commits_analysis = _analyze_recent_commits(commits_data, days)
    
    # PR analysis
    prs_analysis = _analyze_prs(prs_data, days)
    
    # Issues analysis
    issues_analysis = _analyze_issues(issues_data, days)
    
    return {
        "repository": repo_info,
        "contributors": contributors_analysis,
        "commits": commits_analysis,
        "pull_requests": prs_analysis,
        "issues": issues_analysis,
        "analysis_period_days": days
    }


def _calculate_activity_streak(daily_activity: Dict) -> Dict[str, Any]:
    """
    Calculate activity streak information
    """
    if not daily_activity:
        return {"current_streak": 0, "longest_streak": 0}
    
    sorted_days = sorted(daily_activity.keys())
    current_streak = 0
    longest_streak = 0
    temp_streak = 0
    
    # Calculate streaks
    for i, day in enumerate(sorted_days):
        if i == 0:
            temp_streak = 1
        else:
            prev_date = datetime.strptime(sorted_days[i-1], "%Y-%m-%d")
            curr_date = datetime.strptime(day, "%Y-%m-%d")
            
            if (curr_date - prev_date).days == 1:
                temp_streak += 1
            else:
                temp_streak = 1
        
        longest_streak = max(longest_streak, temp_streak)
    
    # Check current streak
    today = datetime.now().strftime("%Y-%m-%d")
    if today in daily_activity or (len(sorted_days) > 0 and 
                                  (datetime.now() - datetime.strptime(sorted_days[-1], "%Y-%m-%d")).days <= 1):
        current_streak = temp_streak
    
    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak
    }


def _calculate_activity_score(events: List, days: int) -> int:
    """
    Calculate overall activity score (0-100)
    """
    if not events or days == 0:
        return 0
    
    # Base score from event frequency
    events_per_day = len(events) / days
    base_score = min(events_per_day * 10, 50)  # Max 50 points from frequency
    
    # Bonus for diversity of activity types
    activity_types = set(event.get("type", "") for event in events)
    diversity_bonus = min(len(activity_types) * 5, 30)  # Max 30 points from diversity
    
    # Bonus for consistency
    daily_activity = defaultdict(int)
    for event in events:
        date = datetime.fromisoformat(event.get("created_at", "").replace('Z', '+00:00'))
        day_key = date.strftime("%Y-%m-%d")
        daily_activity[day_key] += 1
    
    active_days = len(daily_activity)
    consistency_bonus = min((active_days / days) * 20, 20)  # Max 20 points from consistency
    
    total_score = base_score + diversity_bonus + consistency_bonus
    return min(int(total_score), 100)


def _calculate_collaboration_score(forks: int, pr_events: List, issue_events: List) -> int:
    """
    Calculate collaboration score (0-100)
    """
    score = 0
    
    # Points for forks
    score += min(forks * 5, 30)
    
    # Points for PR activity
    score += min(len(pr_events) * 3, 40)
    
    # Points for issue activity
    score += min(len(issue_events) * 2, 30)
    
    return min(score, 100)


def _analyze_contributors(contributors_data: List) -> Dict[str, Any]:
    """
    Analyze repository contributors
    """
    if not contributors_data:
        return {"total_contributors": 0}
    
    total_contributions = sum(c.get("contributions", 0) for c in contributors_data)
    
    return {
        "total_contributors": len(contributors_data),
        "total_contributions": total_contributions,
        "top_contributors": [
            {
                "username": c.get("login"),
                "contributions": c.get("contributions", 0),
                "avatar_url": c.get("avatar_url")
            }
            for c in contributors_data[:10]
        ]
    }


def _analyze_recent_commits(commits_data: List, days: int) -> Dict[str, Any]:
    """
    Analyze recent commits
    """
    if not commits_data:
        return {"total_commits": 0}
    
    # Commit authors
    authors = defaultdict(int)
    for commit in commits_data:
        author = commit.get("commit", {}).get("author", {}).get("name", "Unknown")
        authors[author] += 1
    
    return {
        "total_commits": len(commits_data),
        "unique_authors": len(authors),
        "commits_per_day": round(len(commits_data) / days, 2) if days > 0 else 0,
        "top_committers": dict(sorted(authors.items(), key=lambda x: x[1], reverse=True)[:10])
    }


def _analyze_prs(prs_data: List, days: int) -> Dict[str, Any]:
    """
    Analyze pull requests
    """
    if not prs_data:
        return {"total_prs": 0}
    
    # Filter recent PRs
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    recent_prs = [
        pr for pr in prs_data
        if datetime.fromisoformat(pr.get("created_at", "").replace('Z', '+00:00')) > cutoff_date
    ]
    
    # PR states
    states = defaultdict(int)
    for pr in prs_data:
        states[pr.get("state", "unknown")] += 1
    
    return {
        "total_prs": len(prs_data),
        "recent_prs": len(recent_prs),
        "pr_states": dict(states),
        "prs_per_day": round(len(recent_prs) / days, 2) if days > 0 else 0
    }


def _analyze_issues(issues_data: List, days: int) -> Dict[str, Any]:
    """
    Analyze issues
    """
    if not issues_data:
        return {"total_issues": 0}
    
    # Filter actual issues (not PRs)
    actual_issues = [issue for issue in issues_data if not issue.get("pull_request")]
    
    # Filter recent issues
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    recent_issues = [
        issue for issue in actual_issues
        if datetime.fromisoformat(issue.get("created_at", "").replace('Z', '+00:00')) > cutoff_date
    ]
    
    # Issue states
    states = defaultdict(int)
    for issue in actual_issues:
        states[issue.get("state", "unknown")] += 1
    
    return {
        "total_issues": len(actual_issues),
        "recent_issues": len(recent_issues),
        "issue_states": dict(states),
        "issues_per_day": round(len(recent_issues) / days, 2) if days > 0 else 0
    }