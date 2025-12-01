"""
Custom Tool: Weather Checker
=============================
This is an example of a custom tool that integrates with external APIs.
In this demo version, it returns mock data, but shows the structure
for integrating with real weather APIs like OpenWeatherMap.

This tool demonstrates how agents can access real-time external data.
"""

from strands import tool
import json
from datetime import datetime


@tool
def check_weather(
    location: str,
    units: str = "metric"
) -> str:
    """
    Check current weather data for a specified location.
    
    Args:
        location: City name, zip code, or "city, country" (e.g., "London", "New York, US", "90210")
        units: Temperature units - "metric" (Celsius), "imperial" (Fahrenheit), or "kelvin" (default: "metric")
    
    Returns:
        A formatted string with current weather information including temperature, 
        conditions, humidity, wind speed, and more
    
    Examples:
        - check_weather("London") - Get weather for London in Celsius
        - check_weather("New York, US", "imperial") - Get weather for NYC in Fahrenheit
        - check_weather("Tokyo, JP") - Get weather for Tokyo in Celsius
    """
    try:
        import requests
    except ImportError:
        return "Error: 'requests' library not installed. Please install it with: pip install requests"
    
    # Note: In a production environment, you would use a real API key
    # For demonstration, this uses OpenWeatherMap API (requires API key)
    API_KEY = "demo"  # Replace with actual API key
    
    # Determine temperature unit symbol
    temp_units = {
        "metric": "°C",
        "imperial": "°F",
        "kelvin": "K"
    }
    temp_unit = temp_units.get(units.lower(), "°C")
    
    # For demo purposes without actual API, return mock data structure
    # In real implementation, you would make API call like:
    # url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEY}&units={units}"
    # response = requests.get(url)
    
    # Mock weather data for demonstration
    mock_weather = {
        "location": location,
        "temperature": 22 if units == "metric" else 72,
        "feels_like": 20 if units == "metric" else 68,
        "condition": "Partly Cloudy",
        "description": "scattered clouds",
        "humidity": 65,
        "pressure": 1013,
        "wind_speed": 5.2 if units == "metric" else 11.6,
        "wind_direction": 180,
        "visibility": 10,
        "cloudiness": 40,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    wind_unit = "m/s" if units == "metric" else "mph"
    visibility_unit = "km" if units == "metric" else "miles"
    
    # Format the weather report
    result = f"""Weather Report for {mock_weather['location']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌡️  Temperature:      {mock_weather['temperature']}{temp_unit}
🤔 Feels Like:       {mock_weather['feels_like']}{temp_unit}
☁️  Condition:        {mock_weather['condition']}
📝 Description:      {mock_weather['description']}

💧 Humidity:         {mock_weather['humidity']}%
🌬️  Wind Speed:       {mock_weather['wind_speed']} {wind_unit}
🧭 Wind Direction:   {mock_weather['wind_direction']}° (S)
👁️  Visibility:       {mock_weather['visibility']} {visibility_unit}
☁️  Cloudiness:       {mock_weather['cloudiness']}%
🔽 Pressure:         {mock_weather['pressure']} hPa

⏰ Updated:          {mock_weather['timestamp']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ️  Note: This is a demo version. To use real weather data:
   1. Get a free API key from https://openweathermap.org/api
   2. Replace the API_KEY variable in the code
   3. Uncomment the API call section"""
    
    return result
