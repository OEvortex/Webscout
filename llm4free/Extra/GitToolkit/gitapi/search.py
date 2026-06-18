from typing import Any, Dict, Optional
from urllib.parse import quote

from .utils import request


class GitSearch:
    """Class for searching GitHub content without authentication"""

    BASE_URL = "https://api.github.com/search"

    def search_repositories(
        self,
        query: str,
        sort: Optional[str] = None,
        order: str = "desc",
        page: int = 1,
        per_page: int = 30
    ) -> Dict[str, Any]:
        """
        Search for repositories.

        Args:
            query: Search query (e.g., "tetris language:python stars:>100")
            sort: Sort by (stars, forks, help-wanted-issues, updated)
            order: Sort order (asc, desc)
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            Dict with total_count, incomplete_results, and items
        """
        url = f"{self.BASE_URL}/repositories?q={quote(query)}&page={page}&per_page={per_page}&order={order}"
        if sort:
            url += f"&sort={sort}"
        return request(url)

    def search_users(
        self,
        query: str,
        sort: Optional[str] = None,
        order: str = "desc",
        page: int = 1,
        per_page: int = 30
    ) -> Dict[str, Any]:
        """
        Search for users.

        Args:
            query: Search query (e.g., "tom repos:>42 followers:>1000")
            sort: Sort by (followers, repositories, joined)
            order: Sort order (asc, desc)
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            Dict with total_count, incomplete_results, and items
        """
        url = f"{self.BASE_URL}/users?q={quote(query)}&page={page}&per_page={per_page}&order={order}"
        if sort:
            url += f"&sort={sort}"
        return request(url)

    def search_topics(
        self,
        query: str,
        page: int = 1,
        per_page: int = 30
    ) -> Dict[str, Any]:
        """
        Search for topics.

        Args:
            query: Search query
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            Dict with total_count, incomplete_results, and items
        """
        url = f"{self.BASE_URL}/topics?q={quote(query)}&page={page}&per_page={per_page}"
        return request(url)

    def search_commits(
        self,
        query: str,
        sort: Optional[str] = None,
        order: str = "desc",
        page: int = 1,
        per_page: int = 30
    ) -> Dict[str, Any]:
        """
        Search for commits.

        Args:
            query: Search query (e.g., "fix bug repo:owner/repo")
            sort: Sort by (author-date, committer-date)
            order: Sort order (asc, desc)
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            Dict with total_count, incomplete_results, and items
        """
        url = f"{self.BASE_URL}/commits?q={quote(query)}&page={page}&per_page={per_page}&order={order}"
        if sort:
            url += f"&sort={sort}"
        return request(url)

    def search_issues(
        self,
        query: str,
        sort: Optional[str] = None,
        order: str = "desc",
        page: int = 1,
        per_page: int = 30
    ) -> Dict[str, Any]:
        """
        Search for issues and pull requests.

        Args:
            query: Search query (e.g., "bug is:issue is:open label:bug")
            sort: Sort by (comments, reactions, created, updated)
            order: Sort order (asc, desc)
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            Dict with total_count, incomplete_results, and items
        """
        url = f"{self.BASE_URL}/issues?q={quote(query)}&page={page}&per_page={per_page}&order={order}"
        if sort:
            url += f"&sort={sort}"
        return request(url)

    def search_labels(
        self,
        repository_id: int,
        query: str,
        sort: Optional[str] = None,
        order: str = "desc",
        page: int = 1,
        per_page: int = 30
    ) -> Dict[str, Any]:
        """
        Search for labels in a repository.

        Args:
            repository_id: Repository ID to search in
            query: Search query
            sort: Sort by (created, updated)
            order: Sort order (asc, desc)
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            Dict with total_count, incomplete_results, and items
        """
        url = f"{self.BASE_URL}/labels?repository_id={repository_id}&q={quote(query)}&page={page}&per_page={per_page}&order={order}"
        if sort:
            url += f"&sort={sort}"
        return request(url)
