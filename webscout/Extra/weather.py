"""
Weather information module with a clean, strongly-typed API structure.

This module provides a simple client for fetching weather data
from the wttr.in service with proper typing and a consistent interface.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from curl_cffi.requests import Session


class CurrentCondition:
    """Current weather conditions with strongly typed properties."""

    def __init__(self, data: Dict[str, Any]) -> None:
        """Initialize with current condition data.

        Args:
            data: Current condition data dictionary from wttr.in
        """
        self.temp_c: Optional[str] = data.get('temp_C')
        self.temp_f: Optional[str] = data.get('temp_F')
        self.feels_like_c: Optional[str] = data.get('FeelsLikeC')
        self.feels_like_f: Optional[str] = data.get('FeelsLikeF')
        self.weather_desc: str = data.get('weatherDesc', [{}])[0].get('value', '')
        self.weather_code: Optional[str] = data.get('weatherCode')
        self.humidity: Optional[str] = data.get('humidity')
        self.visibility: Optional[str] = data.get('visibility')
        self.pressure: Optional[str] = data.get('pressure')
        self.wind_speed_kmph: Optional[str] = data.get('windspeedKmph')
        self.wind_direction: Optional[str] = data.get('winddir16Point')
        self.wind_degree: Optional[str] = data.get('winddirDegree')


class Location:
    """Location information with strongly typed properties."""

    def __init__(self, data: Dict[str, Any]) -> None:
        """Initialize with location data.

        Args:
            data: Location data dictionary from wttr.in
        """
        self.name: str = data.get('areaName', [{}])[0].get('value', '')
        self.country: str = data.get('country', [{}])[0].get('value', '')
        self.region: str = data.get('region', [{}])[0].get('value', '')
        self.latitude: Optional[str] = data.get('latitude')
        self.longitude: Optional[str] = data.get('longitude')


class HourlyForecast:
    """Hourly forecast information with strongly typed properties."""

    def __init__(self, data: Dict[str, Any]) -> None:
        """Initialize with hourly forecast data.

        Args:
            data: Hourly forecast data dictionary from wttr.in
        """
        self.time: Optional[str] = data.get('time')
        self.temp_c: Optional[str] = data.get('tempC')
        self.temp_f: Optional[str] = data.get('tempF')
        self.weather_desc: str = data.get('weatherDesc', [{}])[0].get('value', '')
        self.weather_code: Optional[str] = data.get('weatherCode')
        self.wind_speed_kmph: Optional[str] = data.get('windspeedKmph')
        self.wind_direction: Optional[str] = data.get('winddir16Point')
        self.feels_like_c: Optional[str] = data.get('FeelsLikeC')
        self.feels_like_f: Optional[str] = data.get('FeelsLikeF')
        self.chance_of_rain: Optional[str] = data.get('chanceofrain')
        self.chance_of_snow: Optional[str] = data.get('chanceofsnow')


class DayForecast:
    """Daily forecast information with strongly typed properties."""

    def __init__(self, data: Dict[str, Any]) -> None:
        """Initialize with daily forecast data.

        Args:
            data: Daily forecast data dictionary from wttr.in
        """
        self.date: Optional[str] = data.get('date')
        self.date_formatted: Optional[str] = None
        if self.date:
            try:
                self.date_formatted = datetime.strptime(self.date, '%Y-%m-%d').strftime('%a, %b %d')
            except ValueError:
                pass

        self.max_temp_c: Optional[str] = data.get('maxtempC')
        self.max_temp_f: Optional[str] = data.get('maxtempF')
        self.min_temp_c: Optional[str] = data.get('mintempC')
        self.min_temp_f: Optional[str] = data.get('mintempF')
        self.avg_temp_c: Optional[str] = data.get('avgtempC')
        self.avg_temp_f: Optional[str] = data.get('avgtempF')
        self.sun_hour: Optional[str] = data.get('sunHour')

        # Parse astronomy data (simplified)
        if data.get('astronomy') and len(data.get('astronomy', [])) > 0:
            astro = data.get('astronomy', [{}])[0]
            self.sunrise: Optional[str] = astro.get('sunrise')
            self.sunset: Optional[str] = astro.get('sunset')
            self.moon_phase: Optional[str] = astro.get('moon_phase')
        else:
            self.sunrise = self.sunset = self.moon_phase = None

        # Parse hourly forecasts
        self.hourly: List[HourlyForecast] = []
        for hour_data in data.get('hourly', []):
            self.hourly.append(HourlyForecast(hour_data))


class Weather:
    """Weather response object with strongly typed properties."""

    def __init__(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Initialize with weather data.

        Args:
            data: Weather data dictionary from wttr.in
        """
        if not data:
            self.current_condition = None
            self.location = None
            self.forecast_days = []
            return

        # Parse current condition
        self.current_condition: Optional[CurrentCondition] = None
        if data.get('current_condition') and len(data.get('current_condition', [])) > 0:
            self.current_condition = CurrentCondition(data.get('current_condition', [{}])[0])

        # Parse location
        self.location: Optional[Location] = None
        if data.get('nearest_area') and len(data.get('nearest_area', [])) > 0:
            self.location = Location(data.get('nearest_area', [{}])[0])

        # Parse forecast days
        self.forecast_days: List[DayForecast] = []
        for day_data in data.get('weather', []):
            self.forecast_days.append(DayForecast(day_data))

    @property
    def today(self) -> Optional[DayForecast]:
        """Get today's forecast."""
        return self.forecast_days[0] if self.forecast_days else None

    @property
    def tomorrow(self) -> Optional[DayForecast]:
        """Get tomorrow's forecast."""
        return self.forecast_days[1] if len(self.forecast_days) > 1 else None

    @property
    def summary(self) -> str:
        """Get a simple text summary of current weather."""
        if not self.current_condition or not self.location:
            return "Weather data not available"

        return f"{self.location.name}, {self.location.country}: {self.current_condition.weather_desc}, {self.current_condition.temp_c}°C ({self.current_condition.temp_f}°F)"


class WeatherClient:
    """Client for fetching weather information."""

    def get_weather(self, location: str) -> Weather:
        """Get weather for the specified location.

        Args:
            location: Location to get weather for (city name, zip code, etc.)

        Returns:
            Weather object containing all weather data
        """
        try:
            session = Session()
            response = session.get(f"https://wttr.in/{location}?format=j1", timeout=10)
            response.raise_for_status()
            return Weather(response.json())
        except Exception as e:
            print(f"Error fetching weather data: {str(e)}")
            return Weather()


def get(location: str) -> Weather:
    """Convenience function to get weather for a location.

    Args:
        location: Location to get weather for

    Returns:
        Weather object containing all weather data
    """
    client = WeatherClient()
    return client.get_weather(location)
