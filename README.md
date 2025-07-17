# GitHub MCP Server

A Model Context Protocol (MCP) server that provides AI agents with powerful GitHub integration capabilities. This server enables **Claude Desktop** to interact with GitHub repositories, manage code, handle issues, analyze pull requests, and perform advanced repository operations.

### Demo Video

https://github.com/user-attachments/assets/751d371c-b067-492d-bdc8-84a8217e0e1c

## 🚀 Features

### Repository Management
- **Repository Operations**: List, create, and explore repositories
- **Content Management**: Browse repository contents and directory structures
- **Repository Health Check**: Comprehensive analysis of repository best practices
- **Dependency Analysis**: Detailed dependency scanning for multiple languages
- **Repository Search**: Advanced search with filters for language, topics, and more

### File Management
- **File Operations**: Create, update, and read individual files
- **Multi-format Support**: Handle various file types including source code, documentation, and configuration files
- **Branch-aware Operations**: Work with files across different branches

### Git Operations
- **Branch Management**: Create branches, compare branches, and get branch status overviews
- **Pull Request Management**: Create pull requests and manage PR workflows
- **Git Flow Support**: Complete support for standard Git workflows

### Issue & PR Management
- **Smart Issue Triage**: AI-powered issue analysis and categorization
- **Label Management**: Automated label application based on issue content
- **PR Review Analysis**: Comprehensive pull request review summaries
- **Comment Analysis**: Full context understanding through issue/PR comments

### Analytics & Insights
- **User Analytics**: Detailed contribution analytics for GitHub users
- **Repository Analytics**: Comprehensive repository activity and contribution analysis
- **Trend Analysis**: Track contribution patterns over customizable time periods


## Project Structure 

```
github-mcp/
├── src/
│   ├── tools.py                    # Main tool registration module
│   ├── repo_management/
│   │   ├── repos.py               # Repository operations
│   │   ├── git.py                 # Git operations
│   │   ├── search.py              # Repository search
│   │   ├── branches.py            # Branch management
│   │   └── health.py              # Repository health checks
│   ├── file_management/
│   │   └── files.py               # File operations
│   ├── issue_and_pr_management/
│   │   ├── issues.py              # Issue management
│   │   └── pr_reviews.py          # Pull request reviews
│   └── contribution/
│       └── contribution_analytics.py # Contribution analytics
├── main.py
├── __init__.py
└── README.md
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- GitHub Personal Access Token
- MCP-compatible AI system (e.g., Claude Desktop)

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/Amama-Fatima/github-mcp.git
cd github-mcp
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure GitHub Authentication**
Set up your GitHub Personal Access Token as an environment variable:
```bash
export GITHUB_TOKEN="your_github_token_here"
```

4. **Run the MCP Server**
```bash
python main.py
```

## 🔧 Available Tools

### Repository Tools
- `list_github_repositories` - List user repositories with filtering options
- `create_github_repository` - Create new repositories with customizable settings
- `get_github_repository_contents` - Browse repository contents and structure
- `search_github_repositories` - Advanced repository search with multiple filters
- `get_github_starred_repositories` - Retrieve starred repositories
- `check_github_repository_health` - Comprehensive repository health analysis
- `analyze_github_repository_dependencies` - Detailed dependency analysis

### File Management Tools
- `create_github_file` - Create new files in repositories
- `update_github_file` - Update existing files
- `get_github_Individual_file_contents` - Read specific file contents

### Git & Branch Tools
- `create_github_branch` - Create new branches from existing ones
- `get_github_branch_status_overview` - Get comprehensive branch status information
- `compare_github_branches` - Compare differences between branches
- `create_github_pull_request` - Create pull requests with detailed information

### Issue Management Tools
- `smart_issue_triage_tool` - AI-powered issue analysis and categorization
- `apply_issue_labels` - Apply labels to issues based on analysis
- `get_issue_with_comments_tool` - Retrieve issues with full comment context

### PR Management Tools
- `create_pr_review_summary` - Generate comprehensive PR review summaries
- `list_open_prs_for_reviewing` - List open PRs that need review

### Analytics Tools
- `get_user_github_analytics` - Detailed user contribution analytics
- `get_repository_github_analytics` - Repository-specific analytics and insights


## 🙏 Acknowledgments

Built with the Model Context Protocol (MCP) framework and designed to enhance AI agent capabilities for GitHub operations.
