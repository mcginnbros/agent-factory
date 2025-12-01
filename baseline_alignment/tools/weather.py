from strands import tool
import requests
from typing import Optional


@tool
def fetch_weather(location: str, units: str = "metric") -> str:
    """
    Fetch current weather data for a specified location.
    
    Args:
        location: City name, zip code, or "city, country" format (e.g., "London", "New York, US", "90210")
        units: Temperature units - "metric" (Celsius), "imperial" (Fahrenheit), or "kelvin" (default: "metric")
    
    Returns:
        A formatted string with current weather information including temperature, 
        conditions, humidity, wind speed, and more.
    
    Examples:
        - fetch_weather("London") - Get weather for London in Celsius
        - fetch_weather("New York, US", "imperial") - Get weather for NYC in Fahrenheit
        - fetch_weather("Tokyo, JP") - Get weather for Tokyo in Celsius
    """
    try:
        # OpenWeatherMap API endpoint (free tier)
        # Note: In production, you'd need to get an API key from openweathermap.org
        # For now, this is a template that shows the structure
        
        api_key = "YOUR_API_KEY_HERE"  # Replace with actual API key
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        
        params = {
            "q": location,
            "appid": api_key,
            "units": units
        }
        
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract relevant weather information
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        temp_min = data["main"]["temp_min"]
        temp_max = data["main"]["temp_max"]
        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        description = data["weather"][0]["description"]
        wind_speed = data["wind"]["speed"]
        
        # Determine temperature unit symbol
        unit_symbol = "°C" if units == "metric" else "°F" if units == "imperial" else "K"
        speed_unit = "m/s" if units == "metric" else "mph" if units == "imperial" else "m/s"
        
        # Format the weather information
        weather_info = f"""
Weather for {data['name']}, {data['sys']['country']}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Conditions: {description.title()}
Temperature: {temp}{unit_symbol}
Feels Like: {feels_like}{unit_symbol}
Min/Max: {temp_min}{unit_symbol} / {temp_max}{unit_symbol}
Humidity: {humidity}%
Pressure: {pressure} hPa
Wind Speed: {wind_speed} {speed_unit}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return weather_info.strip()
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"Error: Location '{location}' not found. Please check the spelling or try a different format."
        elif e.response.status_code == 401:
            return "Error: Invalid API key. Please set up a valid OpenWeatherMap API key."
        else:
            return f"Error: HTTP {e.response.status_code} - {e.response.reason}"
    except requests.exceptions.RequestException as e:
        return f"Error: Network error occurred - {str(e)}"
    except KeyError as e:
        return f"Error: Unexpected response format - missing field {str(e)}"
    except Exception as e:
        return f"Error: An unexpected error occurred - {str(e)}"
