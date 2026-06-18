"""
Temporary Email Generation Base Module
Abstract base classes for tempmail providers
"""

import random
import string
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Union

# Constants for email generation
EMAIL_LENGTH = 16
PASSWORD_LENGTH = 10


class TempMailProvider(ABC):
    """
    Abstract base class for synchronous temporary email providers
    """
    email: Optional[str] = None
    account_id: Optional[str] = None

    @abstractmethod
    def create_account(self) -> bool:
        """Create a new temporary email account"""
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    def get_messages(self) -> List[Dict]:
        """Get all messages in the inbox"""
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    def check_new_messages(self) -> List[Dict]:
        """Check for new messages and return only the new ones"""
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    def delete_account(self) -> bool:
        """Delete the current temporary email account"""
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    def get_account_info(self) -> Dict:
        """Get current account information"""
        raise NotImplementedError("Method needs to be implemented in subclass")

    def get_token(self) -> str:
        """Get authentication token (optional for some providers)"""
        return ""


class AsyncTempMailProvider(ABC):
    """
    Abstract base class for asynchronous temporary email providers
    """
    email: Optional[str] = None
    account_id: Optional[str] = None

    @abstractmethod
    async def initialize(self):
        """Initialize the provider session"""
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    async def close(self) -> None:
        """Close the provider session"""
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    async def create_email(self, alias: Optional[str] = None, domain: Optional[str] = None) -> Tuple[str, str]:
        """Create a new temporary email address"""
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    async def get_messages(self) -> List[Dict]:
        """Get messages for a temporary email"""
        raise NotImplementedError("Method needs to be implemented in subclass")

    @abstractmethod
    async def delete_email(self) -> bool:
        """Delete a temporary email"""
        raise NotImplementedError("Method needs to be implemented in subclass")


# Utility functions
def generate_random_string(length: int, include_digits: bool = True) -> str:
    """
    Generate a random string of specified length

    Args:
        length: Length of the string to generate
        include_digits: Whether to include digits in the string

    Returns:
        Random string of specified length
    """
    chars = string.ascii_lowercase
    if include_digits:
        chars += string.digits
    return ''.join(random.sample(chars, length))


# Factory function for getting a temporary email provider
def get_provider(provider_name: str = "mailtm", async_provider: bool = False) -> Union[TempMailProvider, AsyncTempMailProvider]:
    """
    Get a temporary email provider instance

    Args:
        provider_name: Name of the provider to use ("mailtm", "tempmailio", or "emailnator")
        async_provider: Whether to return an async provider

    Returns:
        A temporary email provider instance
    """
    if async_provider:
        if provider_name.lower() == "tempmailio":
            from .temp_mail_io import TempMailIOAsync
            return TempMailIOAsync()
        elif provider_name.lower() == "emailnator":
            raise NotImplementedError("Emailnator async provider not implemented.")
        else:
            from .mail_tm import MailTMAsync
            return MailTMAsync()
    else:
        if provider_name.lower() == "tempmailio":
            from .temp_mail_io import TempMailIO
            return TempMailIO()
        elif provider_name.lower() == "emailnator":
            from .emailnator import EmailnatorProvider
            return EmailnatorProvider()
        else:
            from .mail_tm import MailTM
            return MailTM()


# Simplified helpers for common operations
def get_random_email(provider_name: str = "mailtm") -> Tuple[str, TempMailProvider]:
    """
    Get a random temporary email address

    Args:
        provider_name: Name of the provider to use

    Returns:
        Tuple containing the email address and the provider instance
    """
    provider = get_provider(provider_name)

    if isinstance(provider, AsyncTempMailProvider):
        raise TypeError("get_random_email only supports synchronous providers")

    # For providers that require explicit initialization
    if getattr(provider, '_initialized', True) is False:
        try:
            # If there's an initialization method that needs to be called
            if hasattr(provider, 'initialize'):
                provider.initialize() # type: ignore
        except Exception as e:
            raise RuntimeError(f"Failed to initialize provider: {e}")

    # Create the account (auto-generates a random email)
    success = provider.create_account()
    if not success:
        raise RuntimeError(f"Failed to create account with provider {provider_name}")

    return getattr(provider, 'email', ""), provider


def get_disposable_email() -> Tuple[str, TempMailProvider]:
    """Alias for get_random_email"""
    return get_random_email()
