"""
Weather ASCII art visualization module with a simple, strongly-typed API.

This module provides a clean interface for fetching weather information
in ASCII art format using the wttr.in service.
"""

from typing import Any, Dict, Optional

from curl_cffi.requests import Session


class WeatherAscii:
    """Container for ASCII weather data with a simple API."""

    def __init__(self, content: str) -> None:
        """Initialize with ASCII weather content.

        Args:
            content: ASCII weather data or error message
        """
        self._content = content

    @property
    def content(self) -> str:
        """Get the ASCII content, similar to choices.message.content in OpenAI API."""
        return self._content

    def __str__(self) -> str:
        """String representation of ASCII weather."""
        return self.content


class WeatherAsciiClient:
    """Client for fetching weather information in ASCII art."""

    def get_weather(self, location: str, params: Optional[Dict[str, Any]] = None) -> WeatherAscii:
        """Get ASCII weather for a location.

        Args:
            location: The location for which to fetch weather data
            params: Additional parameters for the request

        Returns:
            WeatherAscii object containing ASCII art weather data
        """
        url = f"https://wttr.in/{location}"
        headers = {'User-Agent': 'curl'}

        try:
            session = Session()
            response = session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            if response.status_code == 200:
                # Remove the footer line from wttr.in
                ascii_weather = "\n".join(response.text.splitlines()[:-1])
                return WeatherAscii(ascii_weather)
            else:
                error_msg = f"Error: Unable to fetch weather data. Status code: {response.status_code}"
                return WeatherAscii(error_msg)
        except Exception as e:
            return WeatherAscii(f"Error: {str(e)}")


def get(location: str, params: Optional[Dict[str, Any]] = None) -> WeatherAscii:
    """Convenience function to get ASCII weather for a location.

    Args:
        location: Location to get weather for
        params: Additional parameters for the request

    Returns:
        WeatherAscii object containing ASCII art weather data
    """
    client = WeatherAsciiClient()
    return client.get_weather(location, params)

