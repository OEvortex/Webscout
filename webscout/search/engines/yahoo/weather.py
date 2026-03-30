"""Yahoo weather search using embedded JSON data."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from ...http_client import HttpClient


class YahooWeather:
    """Yahoo weather search using embedded JSON extraction."""

    def __init__(self, proxy: str | None = None, timeout: int | None = None, verify: bool = True):
        self.http_client = HttpClient(proxy=proxy, timeout=timeout, verify=verify)

    def request(self, method: str, url: str, **kwargs: Any) -> str | None:
        try:
            from typing import cast

            response = self.http_client.request(cast(Any, method), url, **kwargs)
            return response.text
        except Exception:
            return None

    def run(self, *args, **kwargs) -> list[dict[str, Any]]:
        location = args[0] if args else kwargs.get("location") or kwargs.get("keywords")

        if not location:
            raise ValueError("Location is required for weather search")

        try:
            # Try multiple Yahoo Weather URL patterns
            urls = [
                f"https://weather.yahoo.com/enhanced/weather/today/l?location={location.replace(' ', '+')}",
                f"https://weather.yahoo.com/forecast/{location.replace(' ', '-').lower()}-weather",
                f"https://www.yahoo.com/news/weather/?location={location.replace(' ', '+')}",
            ]

            for url in urls:
                response = self.request("GET", url)
                if not response:
                    continue

                # Try JSON extraction
                weather_data = self._extract_json_data(response, location)
                if weather_data:
                    return [weather_data]

                # Try HTML parsing fallback
                weather_data = self._parse_weather_html(response, location)
                if weather_data:
                    return [weather_data]

            # Fallback: Use wttr.in API (reliable, no auth required)
            return self._fetch_from_wttr(location)

        except Exception as e:
            return [{"location": location, "error": f"Failed to fetch weather data: {str(e)}"}]

    def _fetch_from_wttr(self, location: str) -> list[dict[str, Any]]:
        """Fallback weather source using wttr.in."""
        try:
            url = f"https://wttr.in/{location.replace(' ', '+')}?format=j1"
            response = self.request("GET", url)
            if not response:
                return [{"location": location, "error": "Failed to fetch weather data"}]

            data = json.loads(response)
            current = data.get("current_condition", [{}])[0]

            return [
                {
                    "location": location,
                    "temperature_f": int(current.get("temp_F", 0)),
                    "temperature_c": int(current.get("temp_C", 0)),
                    "condition": current.get("weatherDesc", [{}])[0].get("value", ""),
                    "humidity_percent": int(current.get("humidity", 0)),
                    "wind_mph": float(current.get("windspeedMiles", 0)),
                    "wind_kph": float(current.get("windspeedKmph", 0)),
                    "feels_like_f": int(current.get("FeelsLikeF", 0)),
                    "feels_like_c": int(current.get("FeelsLikeC", 0)),
                    "visibility_miles": float(current.get("visibility", 0)),
                    "uv_index": float(current.get("uvIndex", 0)),
                    "precipitation_inches": float(current.get("precipMM", 0)) / 25.4,
                    "source": "wttr.in",
                    "units": "Imperial/Metric",
                }
            ]
        except Exception:
            return [{"location": location, "error": "Failed to fetch weather data"}]

    def _extract_json_data(self, html: str, location: str) -> dict[str, Any] | None:
        """Extract weather data from embedded JSON in the page."""
        try:
            json_pattern = r'self\.__next_f\.push\(\[1,"([^"]+)"\]\)'
            matches = re.findall(json_pattern, html)

            weather_info: Dict[str, Any] = {}

            for match in matches:
                try:
                    decoded = match.encode().decode("unicode_escape")

                    temp_match = re.search(r'"temperature":(\d+)', decoded)
                    if temp_match and not weather_info.get("temperature"):
                        weather_info["temperature"] = int(temp_match.group(1))

                    condition_match = re.search(r'"iconLabel":"([^"]+)"', decoded)
                    if condition_match and not weather_info.get("condition"):
                        weather_info["condition"] = condition_match.group(1)

                    high_match = re.search(r'"highTemperature":(\d+)', decoded)
                    if high_match and not weather_info.get("high"):
                        weather_info["high"] = int(high_match.group(1))

                    low_match = re.search(r'"lowTemperature":(\d+)', decoded)
                    if low_match and not weather_info.get("low"):
                        weather_info["low"] = int(low_match.group(1))

                    humidity_match = re.search(
                        r'"value":"(\d+)%"[^}]*"category":"Humidity"', decoded
                    )
                    if humidity_match and not weather_info.get("humidity"):
                        weather_info["humidity"] = int(humidity_match.group(1))

                    precip_match = re.search(r'"probabilityOfPrecipitation":"(\d+)%"', decoded)
                    if precip_match and not weather_info.get("precipitation_chance"):
                        weather_info["precipitation_chance"] = int(precip_match.group(1))

                    location_match = re.search(
                        r'"name":"([^"]+)","code":null,"woeid":(\d+)', decoded
                    )
                    if location_match and not weather_info.get("location_name"):
                        weather_info["location_name"] = location_match.group(1)
                        weather_info["woeid"] = int(location_match.group(2))

                except Exception:
                    continue

            if weather_info and weather_info.get("temperature"):
                return {
                    "location": weather_info.get("location_name", location),
                    "woeid": weather_info.get("woeid"),
                    "temperature_f": weather_info.get("temperature"),
                    "condition": weather_info.get("condition"),
                    "high_f": weather_info.get("high"),
                    "low_f": weather_info.get("low"),
                    "humidity_percent": weather_info.get("humidity"),
                    "precipitation_chance": weather_info.get("precipitation_chance"),
                    "source": "Yahoo Weather",
                    "units": "Fahrenheit",
                }

            return None

        except Exception:
            return None

    def _parse_weather_html(self, html_content: str, location: str) -> dict[str, Any] | None:
        """Fallback: Parse weather data from HTML content using regex."""
        try:
            weather_data: dict[str, Any] = {"location": location}

            temp_patterns = [
                r'<p[^>]*class="[^"]*font-title1[^"]*"[^>]*>(\d+)°</p>',
                r">(\d+)°<",
                r'"temperature":(\d+)',
            ]
            for pattern in temp_patterns:
                match = re.search(pattern, html_content)
                if match:
                    weather_data["temperature_f"] = int(match.group(1))
                    break

            condition_patterns = [
                r'"iconLabel":"([^"]+)"',
                r'aria-label="([^"]*(?:Cloudy|Sunny|Rain|Clear|Thunder|Shower|Fog)[^"]*)"',
            ]
            for pattern in condition_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    weather_data["condition"] = match.group(1)
                    break

            high_match = re.search(r'"highTemperature":(\d+)', html_content)
            if high_match:
                weather_data["high_f"] = int(high_match.group(1))

            low_match = re.search(r'"lowTemperature":(\d+)', html_content)
            if low_match:
                weather_data["low_f"] = int(low_match.group(1))

            humidity_match = re.search(
                r'Humidity[^>]*>(\d+)%"?|"value":"(\d+)%"', html_content, re.IGNORECASE
            )
            if humidity_match:
                weather_data["humidity_percent"] = int(
                    humidity_match.group(1) or humidity_match.group(2)
                )

            weather_data["source"] = "Yahoo Weather"
            weather_data["units"] = "Fahrenheit"

            weather_data = {k: v for k, v in weather_data.items() if v is not None}

            if len(weather_data) > 3:
                return weather_data

            return None

        except Exception:
            return None
