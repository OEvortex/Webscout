from typing import Any, Dict, List, Optional, cast

from .utils import request


class Gist:
    """Class for interacting with GitHub Gists without authentication"""

    BASE_URL = "https://api.github.com/gists"

    def get(self, gist_id: str) -> Dict[str, Any]:
        """
        Get a specific gist by ID.

        Args:
            gist_id: The gist ID

        Returns:
            Gist data including files, description, owner, etc.
        """
        url = f"{self.BASE_URL}/{gist_id}"
        return cast(Dict[str, Any], request(url))

    def list_public(
        self,
        since: Optional[str] = None,
        page: int = 1,
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        List public gists sorted by most recently updated.

        Args:
            since: Only gists updated after this time (ISO 8601 format)
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            List of public gists
        """
        url = f"{self.BASE_URL}/public?page={page}&per_page={per_page}"
        if since:
            url += f"&since={since}"
        return cast(List[Dict[str, Any]], request(url))

    def list_for_user(
        self,
        username: str,
        since: Optional[str] = None,
        page: int = 1,
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        List public gists for a user.

        Args:
            username: GitHub username
            since: Only gists updated after this time (ISO 8601 format)
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            List of user's public gists
        """
        url = f"https://api.github.com/users/{username}/gists?page={page}&per_page={per_page}"
        if since:
            url += f"&since={since}"
        return cast(List[Dict[str, Any]], request(url))

    def get_commits(
        self,
        gist_id: str,
        page: int = 1,
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get commit history for a gist.

        Args:
            gist_id: The gist ID
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            List of commits with version, user, change_status, committed_at
        """
        url = f"{self.BASE_URL}/{gist_id}/commits?page={page}&per_page={per_page}"
        return cast(List[Dict[str, Any]], request(url))

    def get_forks(
        self,
        gist_id: str,
        page: int = 1,
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        List forks of a gist.

        Args:
            gist_id: The gist ID
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            List of gist forks
        """
        url = f"{self.BASE_URL}/{gist_id}/forks?page={page}&per_page={per_page}"
        return cast(List[Dict[str, Any]], request(url))

    def get_revision(self, gist_id: str, sha: str) -> Dict[str, Any]:
        """
        Get a specific revision of a gist.

        Args:
            gist_id: The gist ID
            sha: The revision SHA

        Returns:
            Gist data at that specific revision
        """
        url = f"{self.BASE_URL}/{gist_id}/{sha}"
        return cast(Dict[str, Any], request(url))

    def get_comments(
        self,
        gist_id: str,
        page: int = 1,
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get comments on a gist.

        Args:
            gist_id: The gist ID
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            List of comments
        """
        url = f"{self.BASE_URL}/{gist_id}/comments?page={page}&per_page={per_page}"
        return cast(List[Dict[str, Any]], request(url))
