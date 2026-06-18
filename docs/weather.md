<div align="center">
  <h1>☀️ LLM4Free Weather Toolkit</h1>
  
  > Last updated: 2025-11-16  
  > Maintained by [LLM4Free](https://github.com/OEvortex/Webscout)
  <p><strong>Comprehensive weather data retrieval and visualization tools</strong></p>
  
  <!-- Badges -->
  <p>
    <a href="#-installation"><img src="https://img.shields.io/badge/Easy-Installation-success?style=flat-square" alt="Easy Installation"></a>
    <a href="#-current-weather-data"><img src="https://img.shields.io/badge/Real--time-Data-blue?style=flat-square" alt="Real-time Data"></a>
    <a href="#-ascii-art-weather"><img src="https://img.shields.io/badge/ASCII-Visualization-orange?style=flat-square" alt="ASCII Visualization"></a>
  </p>
</div>

> [!NOTE]
> LLM4Free's Weather Toolkit provides powerful tools to retrieve and display weather information in various formats, including structured data and ASCII art visualization.

## 📋 Table of Contents

- [🚀 Installation](#-installation)
- [🌡️ Current Weather Data](#-current-weather-data)
- [🔮 Weather Forecast](#-weather-forecast)
- [🎨 ASCII Art Weather](#-ascii-art-weather)
- [📊 Data Structure](#-data-structure)
- [⚙️ Advanced Usage](#-advanced-usage)

## 🚀 Installation

The Weather Toolkit is included in the LLM4Free package. Install or update LLM4Free to get access:

```bash
pip install -U llm4free
```

## 🌡️ Current Weather Data

Retrieve structured current weather information for any location worldwide.

```python
from llm4free.Extra import weather

# Get weather for a specific location
forecast = weather.get("London")

# Access current conditions
print(f"Current weather: {forecast.summary}")

# Access temperature details
if forecast.current_condition:
    print(f"Temperature: {forecast.current_condition.temp_c}°C / {forecast.current_condition.temp_f}°F")
    print(f"Feels like: {forecast.current_condition.feels_like_c}°C")
    print(f"Conditions: {forecast.current_condition.weather_desc}")
    print(f"Wind: {forecast.current_condition.wind_speed_kmph} km/h from {forecast.current_condition.wind_direction}")
    print(f"Humidity: {forecast.current_condition.humidity}%")
    print(f"Visibility: {forecast.current_condition.visibility} km")
    print(f"Pressure: {forecast.current_condition.pressure} mb")
```

## 🔮 Weather Forecast

Access detailed forecast information for today and upcoming days.

```python
from llm4free.Extra import weather

forecast = weather.get("Tokyo")

# Today's forecast
if forecast.today:
    print(f"Today ({forecast.today.date_formatted}):")
    print(f"  Temperature range: {forecast.today.min_temp_c}°C - {forecast.today.max_temp_c}°C")
    print(f"  Sunrise: {forecast.today.sunrise}, Sunset: {forecast.today.sunset}")
    
    # Access hourly forecasts
    if forecast.today.hourly and len(forecast.today.hourly) > 4:
        noon = forecast.today.hourly[4]  # Noon (12:00) is usually index 4
        print(f"  Noon conditions: {noon.weather_desc}")
        print(f"  Chance of rain: {noon.chance_of_rain}%")
        print(f"  Humidity: {noon.humidity}%")
        print(f"  UV Index: {noon.uv_index}")

# Tomorrow's forecast
if forecast.tomorrow:
    print(f"\nTomorrow ({forecast.tomorrow.date_formatted}):")
    print(f"  Temperature range: {forecast.tomorrow.min_temp_c}°C - {forecast.tomorrow.max_temp_c}°C")
    print(f"  Weather: {forecast.tomorrow.weather_desc}")
    print(f"  Sunrise: {forecast.tomorrow.sunrise}, Sunset: {forecast.tomorrow.sunset}")

# Extended forecast (next 3 days)
if forecast.days and len(forecast.days) > 2:
    print("\nExtended Forecast:")
    for day in forecast.days[2:5]:  # Days 3-5
        print(f"  {day.date_formatted}: {day.min_temp_c}°C - {day.max_temp_c}°C, {day.weather_desc}")
```

## 🎨 ASCII Art Weather

Retrieve weather information as visually appealing ASCII art.

```python
from llm4free.Extra import weather_ascii

# Get ASCII art weather 
result = weather_ascii.get("Paris")

# Display the ASCII art weather
print(result.content)

# Get ASCII art with temperature in Fahrenheit
result_f = weather_ascii.get("New York", units="imperial")
print(result_f.content)

# Get ASCII art with a specific number of forecast days
result_days = weather_ascii.get("Berlin", days=3)
print(result_days.content)
```

Example output:
```
Weather for Paris, France

     \   /     Clear
      .-.      +20°C
   ― (   ) ―   ↗ 11 km/h
      `-'      10 km
     /   \     0.0 mm
                        ┌─────────────┐
┌───────────────────────┤  Wed 14 Apr ├───────────────────────┐
│             Morning   └──────┬──────┘    Evening    Night   │
├──────────────────────────────┼──────────────────────────────┤
│               Cloudy         │               Clear          │
│      .--.     +20..+22 °C    │     \   /     +15 °C         │
│   .-(    ).   ↗ 11-13 km/h   │      .-.      ↗ 7-9 km/h     │
│  (___.__)__)  10 km          │   ― (   ) ―   10 km          │
│               0.0 mm | 0%    │      `-'      0.0 mm | 0%    │
└──────────────────────────────┴──────────────────────────────┘
```

## 📊 Data Structure

The Weather Toolkit returns structured data objects with the following key components:

<details>
<summary><strong>Forecast Object Structure</strong></summary>

```python
forecast = weather.get("London")

# Main forecast object attributes
forecast.location        # Location information (city, country, etc.)
forecast.summary         # Brief summary of current weather
forecast.current_condition  # Current weather conditions
forecast.today           # Today's forecast
forecast.tomorrow        # Tomorrow's forecast
forecast.days            # List of daily forecasts (including today and tomorrow)

# Current condition attributes
current = forecast.current_condition
current.temp_c           # Temperature in Celsius
current.temp_f           # Temperature in Fahrenheit
current.feels_like_c     # "Feels like" temperature in Celsius
current.feels_like_f     # "Feels like" temperature in Fahrenheit
current.wind_speed_kmph  # Wind speed in km/h
current.wind_speed_mph   # Wind speed in mph
current.wind_direction   # Wind direction (e.g., "NW")
current.humidity         # Humidity percentage
current.pressure         # Atmospheric pressure in millibars
current.visibility       # Visibility in kilometers
current.weather_desc     # Weather description (e.g., "Partly cloudy")
current.weather_code     # Weather code for icon mapping

# Daily forecast attributes
day = forecast.today  # or any day from forecast.days
day.date              # Date (YYYY-MM-DD)
day.date_formatted    # Formatted date (e.g., "Wed 14 Apr")
day.max_temp_c        # Maximum temperature in Celsius
day.min_temp_c        # Minimum temperature in Celsius
day.max_temp_f        # Maximum temperature in Fahrenheit
day.min_temp_f        # Minimum temperature in Fahrenheit
day.sunrise           # Sunrise time
day.sunset            # Sunset time
day.weather_desc      # Weather description
day.weather_code      # Weather code
day.hourly            # List of hourly forecasts for this day
```
</details>

<details>
<summary><strong>ASCII Weather Object Structure</strong></summary>

```python
result = weather_ascii.get("Paris")

# ASCII result attributes
result.content        # The full ASCII art weather display
result.location       # Location information
result.temperature    # Current temperature
result.conditions     # Current weather conditions
result.forecast_days  # Number of forecast days included
```
</details>

## ⚙️ Advanced Usage

<details>
<summary><strong>Custom Location Formats</strong></summary>

The Weather Toolkit supports various location formats:

```python
# City name
weather.get("London")

# City and country
weather.get("Paris, France")

# ZIP/Postal code (US)
weather.get("10001")  # New York, NY

# Latitude and Longitude
weather.get("40.7128,-74.0060")  # New York coordinates
```
</details>

<details>
<summary><strong>Temperature Units</strong></summary>

Control temperature units in ASCII weather display:

```python
# Default (metric - Celsius)
weather_ascii.get("Tokyo")

# Imperial (Fahrenheit)
weather_ascii.get("New York", units="imperial")

# Metric (Celsius)
weather_ascii.get("Berlin", units="metric")
```
</details>

<details>
<summary><strong>Forecast Days</strong></summary>

Control the number of forecast days in ASCII weather display:

```python
# Default (1 day)
weather_ascii.get("Sydney")

# 3-day forecast
weather_ascii.get("Rio de Janeiro", days=3)

# 5-day forecast (maximum)
weather_ascii.get("Moscow", days=5)
```
</details>

<details>
<summary><strong>Error Handling</strong></summary>

Implement proper error handling for robust applications:

```python
from llm4free.Extra import weather
from llm4free.exceptions import APIError

try:
    forecast = weather.get("London")
    print(f"Current temperature: {forecast.current_condition.temp_c}°C")
except APIError as e:
    print(f"API Error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
```
</details>

<div align="center">
  <p>
    <a href="https://github.com/OEvortex/Webscout"><img alt="GitHub Repository" src="https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white"></a>
    <a href="https://t.me/OEvortexAI"><img alt="Telegram Group" src="https://img.shields.io/badge/Telegram%20Group-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white"></a>
  </p>
</div>
