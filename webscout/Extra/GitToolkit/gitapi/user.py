from typing import Any, Dict, List, Optional

from .utils import request


class User:
    """Class for interacting with GitHub user data"""

    def __init__(self, username: str):
        """
        Initialize user client

        Args:
            username: GitHub username
        """
        if not username:
            raise ValueError("Username is required")
        if not isinstance(username, str):
            raise ValueError("Username must be a string")

        self.username = username.strip()
        self.base_url = f"https://api.github.com/users/{self.username}"

    def get_profile(self) -> Dict[str, Any]:
        """Get user profile information"""
        return request(self.base_url)

    def get_repositories(self, page: int = 1, per_page: int = 30, repo_type: str = "all") -> List[Dict[str, Any]]:
        """
        Get user's public repositories

        Args:
            page: Page number
            per_page: Items per page
            repo_type: Type of repositories (all/owner/member)
        """
        url = f"{self.base_url}/repos?page={page}&per_page={per_page}&type={repo_type}"
        return request(url)

    def get_starred(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get repositories starred by user"""
        url = f"{self.base_url}/starred?page={page}&per_page={per_page}"
        return request(url)

    def get_followers(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get user's followers"""
        url = f"{self.base_url}/followers?page={page}&per_page={per_page}"
        return request(url)

    def get_following(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get users followed by this user"""
        url = f"{self.base_url}/following?page={page}&per_page={per_page}"
        return request(url)

    def get_gists(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get user's public gists"""
        url = f"{self.base_url}/gists?page={page}&per_page={per_page}"
        return request(url)

    def get_organizations(self) -> List[Dict[str, Any]]:
        """Get user's organizations"""
        url = f"{self.base_url}/orgs"
        return request(url)

    def get_received_events(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get events received by user"""
        url = f"{self.base_url}/received_events?page={page}&per_page={per_page}"
        return request(url)

    def get_public_events(self, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get user's public events"""
        url = f"{self.base_url}/events/public?page={page}&per_page={per_page}"
        return request(url)

    def get_starred_gists(self) -> List[Dict[str, Any]]:
        """Get gists starred by user"""
        url = f"{self.base_url}/starred_gists"
        return request(url)

    def get_subscriptions(self) -> List[Dict[str, Any]]:
        """Get repositories user is watching"""
        url = f"{self.base_url}/subscriptions"
        return request(url)

    def get_hovercard(self) -> Dict[str, Any]:
        """Get user's hovercard information"""
        url = f"{self.base_url}/hovercard"
        return request(url)

    def get_installation(self) -> Dict[str, Any]:
        """Get user's GitHub App installations"""
        url = f"{self.base_url}/installation"
        return request(url)

    def get_keys(self) -> List[Dict[str, Any]]:
        """Get user's public SSH keys"""
        url = f"{self.base_url}/keys"
        return request(url)

    def get_gpg_keys(self) -> List[Dict[str, Any]]:
        """Get user's public GPG keys"""
        url = f"{self.base_url}/gpg_keys"
        return request(url)

    def get_social_accounts(self) -> List[Dict[str, Any]]:
        """
        Get user's social accounts.

        Returns:
            List of social accounts with provider and url
        """
        url = f"{self.base_url}/social_accounts"
        return request(url)

    def get_packages(self, package_type: str = "container", page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """
        Get user's public packages.

        Args:
            package_type: Type of package (container, npm, maven, rubygems, nuget, docker)
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            List of user's packages
        """
        url = f"{self.base_url}/packages?package_type={package_type}&page={page}&per_page={per_page}"
        return request(url)
