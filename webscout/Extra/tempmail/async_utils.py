"""
Async utilities for temporary email generation
"""
import asyncio
from typing import Dict, List, Optional, Tuple

from litprinter import ic

from .temp_mail_io import TempMailIOAsync as TempMailAPI


class AsyncTempMailHelper:
    """
    Async helper class for TempMail.io API
    Provides simplified methods for async usage of TempMail.io
    """

    def __init__(self):
        self.api = None
        self.email = None
        self.token = None

    async def create(self, alias: Optional[str] = None, domain: Optional[str] = None) -> Tuple[str, str]:
        """
        Create a new temporary email

        Args:
            alias: Optional alias for the email
            domain: Optional domain for the email

        Returns:
            Tuple containing the email address and token
        """
        self.api = TempMailAPI()
        await self.api.initialize()

        try:
            self.email, self.token = await self.api.create_email(alias, domain)
            return self.email, self.token
        except Exception as e:
            ic.configureOutput(prefix='ERROR| ')
            ic(f"Error creating email: {e}")
            await self.close()
            raise

    async def get_messages(self) -> List[Dict]:
        """
        Get messages for the current email

        Returns:
            List of message dictionaries
        """
        if not self.api or not self.email:
            raise ValueError("No email created yet")

        try:
            messages = await self.api.get_messages()
            if not messages:
                return []

            return [
                {
                    "id": msg.get("id") or msg.get("msg_id"),
                    "from": msg.get("from") or msg.get("email_from"),
                    "to": msg.get("to") or msg.get("email_to"),
                    "subject": msg.get("subject"),
                    "created_at": msg.get("created_at") or msg.get("createdAt"),
                    "body": msg.get("body_text") or msg.get("body_html") or msg.get("body"),
                    "has_attachments": bool(msg.get("attachments") or msg.get("has_attachments") or msg.get("hasAttachments"))
                }
                for msg in messages
            ]
        except Exception as e:
            ic.configureOutput(prefix='ERROR| ')
            ic(f"Error getting messages: {e}")
            return []

    async def delete(self) -> bool:
        """
        Delete the current temporary email

        Returns:
            True if deletion was successful, False otherwise
        """
        if not self.api or not self.email or not self.token:
            ic.configureOutput(prefix='WARNING| ')
            ic("No email to delete")
            return False

        try:
            result = await self.api.delete_email()
            return result
        except Exception as e:
            ic.configureOutput(prefix='ERROR| ')
            ic(f"Error deleting email: {e}")
            return False
        finally:
            await self.close()

    async def close(self) -> None:
        """Close the API connection"""
        if self.api:
            await self.api.close()
            self.api = None


async def get_temp_email(alias: Optional[str] = None, domain: Optional[str] = None) -> Tuple[str, AsyncTempMailHelper]:
    """
    Get a temporary email address asynchronously

    Args:
        alias: Optional alias for the email
        domain: Optional domain for the email

    Returns:
        Tuple containing the email address and the TempMail helper instance
    """
    helper = AsyncTempMailHelper()
    email, _ = await helper.create(alias, domain)
    return email, helper


async def wait_for_message(helper: AsyncTempMailHelper, timeout: int = 60, check_interval: int = 5) -> Optional[Dict]:
    """
    Wait for a message to arrive in the inbox

    Args:
        helper: The TempMail helper instance
        timeout: Maximum time to wait in seconds
        check_interval: Time between checks in seconds

    Returns:
        The first message if one arrives, None otherwise
    """
    start_time = asyncio.get_event_loop().time()

    while asyncio.get_event_loop().time() - start_time < timeout:
        messages = await helper.get_messages()
        if messages:
            return messages[0]
        await asyncio.sleep(check_interval)

    return None
