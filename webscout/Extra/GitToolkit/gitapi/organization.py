from typing import Any, Dict, List, Optional

from .utils import request


class Organization:
    """Class for interacting with GitHub organization data without authentication"""

    def __init__(self, org: str):
        """
        Initialize organization client.

        Args:
            org: Organization login name
        """
        if not org:
            raise ValueError("Organization name is required")
        if not isinstance(org, str):
            raise ValueError("Organization name must be a string")

        self.org = org.strip()
        self.base_url = f"https://api.github.com/orgs/{self.org}"

    def get_info(self) -> Dict[str, Any]:
        """
        Get organization information.

        Returns:
            Organization details including name, description, location, etc.
        """
        return request(self.base_url)

    def get_repos(
        self,
        repo_type: str = "all",
        sort: str = "created",
        direction: str = "desc",
        page: int = 1,
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        List organization repositories.

        Args:
            repo_type: Type of repos (all, public, private, forks, sources, member)
            sort: Sort by (created, updated, pushed, full_name)
            direction: Sort direction (asc, desc)
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            List of organization repositories
        """
        url = f"{self.base_url}/repos?type={repo_type}&sort={sort}&direction={direction}&page={page}&per_page={per_page}"
        return request(url)

    def get_public_members(
        self,
        page: int = 1,
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        List public members of the organization.

        Args:
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            List of public organization members
        """
        url = f"{self.base_url}/public_members?page={page}&per_page={per_page}"
        return request(url)

    def get_events(
        self,
        page: int = 1,
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        List public organization events.

        Args:
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            List of public events
        """
        url = f"{self.base_url}/events?page={page}&per_page={per_page}"
        return request(url)
