"""
Repository health checker functionality for GitHub MCP server.
"""
import httpx
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from ..config import GITHUB_TOKEN, GITHUB_HEADERS, TIMEOUT


def check_repository_health(owner: str, repo: str) -> dict:
    """
    Comprehensive repository health check (returns JSON)
    """
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            repo_url = f"https://api.github.com/repos/{owner}/{repo}"
            contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
            community_url = f"https://api.github.com/repos/{owner}/{repo}/community/profile"

            repo_data = client.get(repo_url, headers=GITHUB_HEADERS).json()
            contents = client.get(contents_url, headers=GITHUB_HEADERS).json()
            community_r = client.get(community_url, headers=GITHUB_HEADERS)
            community_profile = community_r.json() if community_r.status_code == 200 else {}

        health_score = 0
        max_score = 100
        issues = []
        good_practices = []

        # Description
        description = repo_data.get("description")
        if description:
            health_score += 10
            good_practices.append("Repository has a description")
        else:
            issues.append("Missing repository description")

        # Activity
        updated_at = repo_data.get("updated_at")
        days_since_update = None
        if updated_at:
            last_update = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            days_since_update = (datetime.now(timezone.utc) - last_update).days
            if days_since_update <= 30:
                health_score += 10
                good_practices.append("Recently updated (within 30 days)")
            elif days_since_update <= 90:
                health_score += 5
                good_practices.append("Updated within 90 days")
            else:
                issues.append(f"Not updated in {days_since_update} days")

        # Files & Metadata
        readme_check = _check_readme(contents)
        license_check = _check_license(contents, repo_data)
        security_check = _check_security_files(contents)
        contrib_check = _check_contribution_files(contents)
        ci_check = _check_ci_cd(contents)
        deps_check = _check_dependencies(owner, repo, contents)
        settings_check = _check_repository_settings(repo_data)

        def apply_check(check_result):
            nonlocal health_score
            health_score += check_result.get("score", 0)
            good_practices.extend(check_result.get("good", []))
            issues.extend(check_result.get("issues", []))

        if readme_check["exists"]:
            health_score += 15
            good_practices.append(f"README found: {readme_check['file']}")
        else:
            issues.append("Missing README file")

        if license_check["exists"]:
            health_score += 10
            good_practices.append(f"License found: {license_check['license']}")
        else:
            issues.append("Missing LICENSE file")

        apply_check(security_check)
        apply_check(contrib_check)
        apply_check(ci_check)
        apply_check(deps_check)
        apply_check(settings_check)

        health_percentage = min(100, (health_score / max_score) * 100)
        if health_percentage >= 90:
            status = "Excellent"
        elif health_percentage >= 70:
            status = "Good"
        elif health_percentage >= 50:
            status = "Needs Improvement"
        else:
            status = "Poor"

        # Recommendations
        recommendations = []
        if health_percentage < 90:
            recommendations.append("Address the issues listed to improve health")
        if not any("README" in p for p in good_practices):
            recommendations.append("Add a comprehensive README with setup instructions")
        if not any("License" in p for p in good_practices):
            recommendations.append("Add a LICENSE file to clarify usage rights")
        if not any("security" in p.lower() for p in good_practices):
            recommendations.append("Add security policies (SECURITY.md)")
        if not any("CI/CD" in p for p in good_practices):
            recommendations.append("Set up CI/CD workflows and automated testing")

        return {
            "owner": owner,
            "repo": repo,
            "health_score": round(health_percentage, 1),
            "status": status,
            "description": description,
            "days_since_update": days_since_update,
            "good_practices": good_practices,
            "issues": issues,
            "recommendations": recommendations,
            "details": {
                "readme": readme_check,
                "license": license_check,
                "ci_cd": ci_check,
                "security": security_check,
                "contribution": contrib_check,
                "dependencies": deps_check,
                "settings": settings_check
            }
        }

    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}", "details": e.response.text}
    except Exception as e:
        return {"error": "Exception occurred while checking repository health", "details": str(e)}

def _check_readme(contents: List[Dict]) -> Dict:
    """Check for README file"""
    readme_files = ["README.md", "readme.md", "README.txt", "readme.txt", "README.rst", "README"]
    
    for item in contents:
        if item.get("name", "").upper() in [f.upper() for f in readme_files]:
            return {"exists": True, "file": item.get("name")}
    
    return {"exists": False}


def _check_license(contents: List[Dict], repo_data: Dict) -> Dict:
    """Check for license"""
    # Check if GitHub detected a license
    license_info = repo_data.get("license")
    if license_info:
        return {"exists": True, "license": license_info.get("name", "Unknown")}
    
    # Check for LICENSE files
    license_files = ["LICENSE", "LICENSE.md", "LICENSE.txt", "license", "license.md", "license.txt"]
    
    for item in contents:
        if item.get("name", "") in license_files:
            return {"exists": True, "license": "License file found"}
    
    return {"exists": False}


def _check_security_files(contents: List[Dict]) -> Dict:
    """Check for security-related files"""
    security_files = {
        "SECURITY.md": "Security policy",
        "security.md": "Security policy",
        ".github/SECURITY.md": "Security policy",
        "SECURITY.txt": "Security policy",
        "security.txt": "Security policy"
    }
    
    score = 0
    good = []
    issues = []
    
    found_security = False
    for item in contents:
        name = item.get("name", "")
        if name in security_files:
            score += 5
            good.append(f"✅ {security_files[name]} found: {name}")
            found_security = True
    
    if not found_security:
        issues.append("❌ Missing security policy (SECURITY.md)")
    
    return {"score": score, "good": good, "issues": issues}


def _check_contribution_files(contents: List[Dict]) -> Dict:
    """Check for contribution guidelines"""
    contrib_files = {
        "CONTRIBUTING.md": "Contributing guidelines",
        "contributing.md": "Contributing guidelines",
        ".github/CONTRIBUTING.md": "Contributing guidelines",
        "CONTRIBUTING.txt": "Contributing guidelines",
        "CODE_OF_CONDUCT.md": "Code of conduct",
        "code_of_conduct.md": "Code of conduct",
        ".github/CODE_OF_CONDUCT.md": "Code of conduct"
    }
    
    score = 0
    good = []
    issues = []
    
    found_contrib = False
    found_conduct = False
    
    for item in contents:
        name = item.get("name", "")
        if name in contrib_files:
            score += 3
            good.append(f"✅ {contrib_files[name]} found: {name}")
            if "CONTRIBUTING" in name.upper():
                found_contrib = True
            elif "CODE_OF_CONDUCT" in name.upper():
                found_conduct = True
    
    if not found_contrib:
        issues.append("⚠️ Missing contributing guidelines (CONTRIBUTING.md)")
    if not found_conduct:
        issues.append("⚠️ Missing code of conduct (CODE_OF_CONDUCT.md)")
    
    return {"score": score, "good": good, "issues": issues}


def _check_ci_cd(contents: List[Dict]) -> Dict:
    """Check for CI/CD configuration"""
    ci_files = {
        ".github/workflows/": "GitHub Actions workflows",
        ".travis.yml": "Travis CI",
        ".circleci/": "CircleCI",
        "Jenkinsfile": "Jenkins",
        ".gitlab-ci.yml": "GitLab CI",
        "azure-pipelines.yml": "Azure Pipelines",
        ".github/workflows/ci.yml": "GitHub Actions CI",
        ".github/workflows/test.yml": "GitHub Actions Tests"
    }
    
    score = 0
    good = []
    issues = []
    
    found_ci = False
    
    for item in contents:
        name = item.get("name", "")
        item_type = item.get("type", "")
        
        if name in ci_files:
            score += 8
            good.append(f"✅ {ci_files[name]} found: {name}")
            found_ci = True
        elif item_type == "dir" and name == ".github":
            # Check for workflows directory
            score += 2
            good.append("✅ .github directory found")
    
    if not found_ci:
        issues.append("⚠️ No CI/CD configuration found")
    
    return {"score": score, "good": good, "issues": issues}


def _check_dependencies(owner: str, repo: str, contents: List[Dict]) -> Dict:
    """Check for dependency files and potential issues"""
    dependency_files = {
        "package.json": "Node.js dependencies",
        "requirements.txt": "Python dependencies",
        "Pipfile": "Python Pipenv dependencies",
        "poetry.lock": "Python Poetry dependencies",
        "Gemfile": "Ruby dependencies",
        "pom.xml": "Maven dependencies",
        "build.gradle": "Gradle dependencies",
        "Cargo.toml": "Rust dependencies",
        "go.mod": "Go dependencies",
        "composer.json": "PHP dependencies"
    }
    
    score = 0
    good = []
    issues = []
    
    found_deps = False
    
    for item in contents:
        name = item.get("name", "")
        if name in dependency_files:
            score += 5
            good.append(f"✅ {dependency_files[name]} found: {name}")
            found_deps = True
            
            # Check for lock files
            if name == "package.json":
                lock_file = "package-lock.json"
            elif name == "Pipfile":
                lock_file = "Pipfile.lock"
            elif name == "Gemfile":
                lock_file = "Gemfile.lock"
            elif name == "composer.json":
                lock_file = "composer.lock"
            else:
                lock_file = None
            
            if lock_file:
                lock_found = any(item.get("name") == lock_file for item in contents)
                if lock_found:
                    score += 2
                    good.append(f"✅ Lock file found: {lock_file}")
                else:
                    issues.append(f"⚠️ Missing lock file: {lock_file}")
    
    if not found_deps:
        issues.append("ℹ️ No dependency files detected")
    
    return {"score": score, "good": good, "issues": issues}


def _check_repository_settings(repo_data: Dict) -> Dict:
    """Check repository settings (returns structured JSON)"""
    score = 0
    good = []
    issues = []

    if repo_data.get("has_issues"):
        score += 3
        good.append("Issues are enabled")
    else:
        issues.append("Issues are disabled")

    if repo_data.get("has_wiki"):
        score += 2
        good.append("Wiki is enabled")

    if repo_data.get("has_projects"):
        score += 2
        good.append("Projects are enabled")

    topics = repo_data.get("topics", [])
    if topics:
        score += 5
        good.append(f"Repository has topics: {', '.join(topics[:3])}{'...' if len(topics) > 3 else ''}")
    else:
        issues.append("No topics set for repository")

    if repo_data.get("archived"):
        issues.append("Repository is archived")

    if repo_data.get("fork"):
        issues.append("Repository is a fork")

    return {
        "score": score,
        "good": good,
        "issues": issues,
        "topics": topics
    }


def check_repository_dependencies(owner: str, repo: str) -> dict:
    """Returns JSON object describing dependency files and findings"""
    if not GITHUB_TOKEN:
        return {"error": "⚠️ No GITHUB_TOKEN set in environment."}

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
            contents_r = client.get(contents_url, headers=GITHUB_HEADERS)
            contents_r.raise_for_status()
            contents = contents_r.json()

            dependency_files = []
            known_files = [
                "package.json", "requirements.txt", "Pipfile",
                "Gemfile", "pom.xml", "build.gradle",
                "Cargo.toml", "go.mod", "composer.json"
            ]

            for item in contents:
                if item.get("name") in known_files:
                    dependency_files.append(item)

            if not dependency_files:
                return {
                    "owner": owner,
                    "repo": repo,
                    "dependency_files_found": [],
                    "message": "No dependency files found"
                }

            analysis_results = []
            for dep_file in dependency_files:
                file_name = dep_file.get("name")
                download_url = dep_file.get("download_url")
                if not download_url:
                    continue

                file_r = client.get(download_url)
                if file_r.status_code == 200:
                    content = file_r.text
                    analysis = _analyze_dependency_file_json(file_name, content)
                    analysis_results.append({
                        "file": file_name,
                        "analysis": analysis
                    })

            return {
                "owner": owner,
                "repo": repo,
                "dependency_files_found": [f["name"] for f in dependency_files],
                "results": analysis_results
            }

    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error {e.response.status_code}", "details": e.response.text}
    except Exception as e:
        return {"error": "Error analyzing dependencies", "details": str(e)}
def _analyze_dependency_file_json(filename: str, content: str) -> dict:
    if filename == "package.json":
        return _analyze_package_json_json(content)
    elif filename == "requirements.txt":
        return _analyze_requirements_txt_json(content)
    elif filename == "Pipfile":
        return _analyze_pipfile_json(content)
    elif filename == "Gemfile":
        return _analyze_gemfile_json(content)
    else:
        return {"note": f"No analysis implemented for {filename}"}


def _analyze_package_json_json(content: str) -> dict:
    try:
        data = json.loads(content)
        dependencies = data.get("dependencies", {})
        dev_dependencies = data.get("devDependencies", {})

        security_packages = ["helmet", "cors", "express-rate-limit", "bcrypt", "jsonwebtoken"]
        test_packages = ["jest", "mocha", "chai", "cypress", "testing-library"]

        found_security = [pkg for pkg in security_packages if pkg in dependencies]
        found_testing = [pkg for pkg in test_packages if pkg in dev_dependencies or any(test_pkg in pkg for test_pkg in test_packages)]

        return {
            "type": "node",
            "dependencies_count": len(dependencies),
            "dev_dependencies_count": len(dev_dependencies),
            "security_packages": found_security,
            "testing_frameworks": found_testing
        }

    except json.JSONDecodeError:
        return {"error": "Invalid JSON in package.json"}


def _analyze_requirements_txt_json(content: str) -> dict:
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith('#')]
    pinned = [line for line in lines if '==' in line]
    security_packages = ["cryptography", "pycryptodome", "bcrypt", "passlib"]
    test_packages = ["pytest", "unittest", "nose", "tox"]

    found_security = [line for line in lines if any(pkg in line.lower() for pkg in security_packages)]
    found_testing = [line for line in lines if any(pkg in line.lower() for pkg in test_packages)]

    return {
        "type": "python",
        "total_dependencies": len(lines),
        "pinned_versions": len(pinned),
        "security_packages": found_security,
        "testing_frameworks": found_testing
    }


def _analyze_pipfile_json(content: str) -> dict:
    return {
        "type": "pipfile",
        "contains_packages_section": "[packages]" in content,
        "contains_dev_packages_section": "[dev-packages]" in content
    }


def _analyze_gemfile_json(content: str) -> dict:
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith('#')]
    gem_lines = [line for line in lines if line.startswith('gem ')]
    rails_gems = ["rails", "devise", "sidekiq", "puma"]
    found_rails = [line for line in gem_lines if any(gem in line.lower() for gem in rails_gems)]

    return {
        "type": "ruby",
        "total_gems": len(gem_lines),
        "rails_related": found_rails
    }