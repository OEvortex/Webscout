from typing import Any, Dict, List, Optional, Union, cast
from urllib.parse import quote

from .utils import request


class Repository:
    """Class for interacting with GitHub repositories"""

    def __init__(self, owner: str, repo: str):
        """
        Initialize repository client

        Args:
            owner: Repository owner
            repo: Repository name
        """
        if not owner or not repo:
            raise ValueError("Owner and repository name are required")
        if not isinstance(owner, str) or not isinstance(repo, str):
            raise ValueError("Owner and repository name must be strings")

        self.owner = owner.strip()
        self.repo = repo.strip()
        self.base_url = f"https://api.github.com/repos/{self.owner}/{self.repo}"

    def get_info(self) -> Dict[str, Any]:
        """Get basic repository information"""
        return request(self.base_url)

    def get_commits(self, page: int = 1, per_page: int = 30, sha: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get repository commits

        Args:
            page: Page number
            per_page: Items per page
            sha: SHA or branch name to start listing commits from
        """
        url = f"{self.base_url}/commits?page={page}&per_page={per_page}"
        if sha:
            url += f"&sha={quote(sha, safe='')}"
        return request(url)

    def get_commit(self, sha: str) -> Dict[str, Any]:
        """Get a specific commit details"""
        url = f"{self.base_url}/commits/{quote(sha, safe='')}"
        return request(url)

    def get_pull_requests(self, state: str = "all", page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """
        Get repository pull requests

        Args:
            state: State of PRs to return (open/closed/all)
            page: Page number
            per_page: Items per page
        """
        url = f"{self.base_url}/pulls?state={state}&page={page}&per_page={per_page}"
        return request(url)

    def get_pull_request(self, pr_number: int) -> Dict[str, Any]:
        """Get specific pull request details"""
        url = f"{self.base_url}/pulls/{pr_number}"
        return request(url)

    def get_pull_request_commits(self, pr_number: int) -> List[Dict[str, Any]]:
        """Get commits in a specific pull request"""
        url = f"{self.base_url}/pulls/{pr_number}/commits"
        return request(url)

    def get_pull_request_files(self, pr_number: int) -> List[Dict[str, Any]]:
        """Get files changed in a specific pull request"""
        url = f"{self.base_url}/pulls/{pr_number}/files"
        return request(url)

    def get_issues(self, state: str = "all", page: int = 1, per_page: int = 30, labels: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get repository issues

        Args:
            state: State of issues to return (open/closed/all)
            page: Page number
            per_page: Items per page
            labels: Comma-separated list of label names
        """
        url = f"{self.base_url}/issues?state={state}&page={page}&per_page={per_page}"
        if labels:
            url += f"&labels={quote(labels, safe='')}"
        return request(url)

    def get_issue(self, issue_number: int) -> Dict[str, Any]:
        """Get specific issue details"""
        url = f"{self.base_url}/issues/{issue_number}"
        return request(url)

    def get_issue_comments(self, issue_number: int) -> List[Dict[str, Any]]:
        """Get comments on a specific issue"""
        url = f"{self.base_url}/issues/{issue_number}/comments"
        return request(url)

    def get_labels(self) -> List[Dict[str, Any]]:
        """Get repository labels"""
        url = f"{self.base_url}/labels"
        return request(url)

    def get_milestones(self, state: str = "all") -> List[Dict[str, Any]]:
        """Get repository milestones"""
        url = f"{self.base_url}/milestones?state={state}"
        return request(url)

    def get_contributors(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get repository contributors"""
        url = f"{self.base_url}/contributors?page={page}&per_page={per_page}"
        return request(url)

    def get_languages(self) -> Dict[str, int]:
        """Get repository language breakdown"""
        url = f"{self.base_url}/languages"
        return request(url)

    def get_teams(self) -> List[Dict[str, Any]]:
        """Get teams with access to repository"""
        url = f"{self.base_url}/teams"
        return request(url)

    def get_tags(self) -> List[Dict[str, Any]]:
        """Get repository tags"""
        url = f"{self.base_url}/tags"
        return request(url)

    def get_releases(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get repository releases"""
        url = f"{self.base_url}/releases?page={page}&per_page={per_page}"
        return request(url)

    def get_release(self, release_id: str) -> Dict[str, Any]:
        """Get specific release details"""
        url = f"{self.base_url}/releases/{release_id}"
        return request(url)

    def get_latest_release(self) -> Dict[str, Any]:
        """Get latest release"""
        url = f"{self.base_url}/releases/latest"
        return cast(Dict[str, Any], request(url))

    def get_branches(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get repository branches"""
        url = f"{self.base_url}/branches?page={page}&per_page={per_page}"
        return request(url)

    def get_branch(self, branch: str) -> Dict[str, Any]:
        """Get specific branch details"""
        url = f"{self.base_url}/branches/{quote(branch, safe='')}"
        return request(url)

    def get_contents(self, path: str = "", ref: Optional[str] = None) -> Dict[str, Any]:
        """Get contents of file or directory"""
        url = f"{self.base_url}/contents/{quote(path)}"
        if ref:
            url += f"?ref={quote(ref, safe='')}"
        return request(url)

    def get_collaborators(self) -> List[Dict[str, Any]]:
        """Get repository collaborators"""
        url = f"{self.base_url}/collaborators"
        return request(url)

    def get_workflows(self) -> List[Dict[str, Any]]:
        """Get repository GitHub Actions workflows"""
        url = f"{self.base_url}/actions/workflows"
        return request(url)

    def get_workflow_runs(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get workflow runs for a specific workflow"""
        url = f"{self.base_url}/actions/workflows/{workflow_id}/runs"
        return request(url)

    def get_deployments(self) -> List[Dict[str, Any]]:
        """Get repository deployments"""
        url = f"{self.base_url}/deployments"
        return request(url)

    def get_traffic(self) -> Dict[str, Any]:
        """Get repository traffic data"""
        url = f"{self.base_url}/traffic/views"
        return request(url)

    def get_code_frequency(self) -> List[List[int]]:
        """Get weekly commit activity"""
        url = f"{self.base_url}/stats/code_frequency"
        return request(url)

    def get_commit_activity(self) -> List[Dict[str, Any]]:
        """Get last year of commit activity"""
        url = f"{self.base_url}/stats/commit_activity"
        return request(url)

    def get_community_profile(self) -> Dict[str, Any]:
        """Get community profile metrics"""
        url = f"{self.base_url}/community/profile"
        return request(url)

    def get_readme(self, ref: Optional[str] = None) -> Dict[str, Any]:
        """
        Get repository README.

        Args:
            ref: The name of the commit/branch/tag (default: repo default branch)

        Returns:
            README content with encoding and download_url
        """
        url = f"{self.base_url}/readme"
        if ref:
            url += f"?ref={quote(ref, safe='')}"
        return request(url)

    def get_license(self) -> Dict[str, Any]:
        """
        Get repository license.

        Returns:
            License information including name, key, spdx_id, and content
        """
        url = f"{self.base_url}/license"
        return request(url)

    def get_topics(self) -> Dict[str, Any]:
        """
        Get repository topics.

        Returns:
            Dict with 'names' key containing list of topic strings
        """
        url = f"{self.base_url}/topics"
        return request(url)

    def get_forks(self, sort: str = "newest", page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """
        List repository forks.

        Args:
            sort: Sort by (newest, oldest, stargazers, watchers)
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            List of forked repositories
        """
        url = f"{self.base_url}/forks?sort={sort}&page={page}&per_page={per_page}"
        return request(url)

    def get_stargazers(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """
        List users who have starred the repository.

        Args:
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            List of users who starred the repo
        """
        url = f"{self.base_url}/stargazers?page={page}&per_page={per_page}"
        return request(url)

    def get_watchers(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """
        List users watching the repository (subscribers).

        Args:
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            List of users watching the repo
        """
        url = f"{self.base_url}/subscribers?page={page}&per_page={per_page}"
        return request(url)

    def compare(self, base: str, head: str) -> Dict[str, Any]:
        """
        Compare two commits, branches, or tags.

        Args:
            base: Base commit/branch/tag
            head: Head commit/branch/tag

        Returns:
            Comparison data including commits, files, and diff stats
        """
        url = f"{self.base_url}/compare/{quote(base, safe='')}...{quote(head, safe='')}"
        return request(url)

    def get_events(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """
        List repository events.

        Args:
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            List of repository events
        """
        url = f"{self.base_url}/events?page={page}&per_page={per_page}"
        return request(url)
