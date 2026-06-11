import requests

from config import (
    WEATHER_API_KEY,
    CITY,
    COUNTRY
)

weather_data = {
    "rain": False,
    "humidity": 0,
    "temperature": 0
}


def update_weather():

    try:

        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={CITY},{COUNTRY}"
            f"&appid={WEATHER_API_KEY}"
            f"&units=metric"
        )

        response = requests.get(url)

        data = response.json()

        humidity = data["main"]["humidity"]
        temperature = data["main"]["temp"]

        rain = "rain" in data

        weather_data["rain"] = rain
        weather_data["humidity"] = humidity
        weather_data["temperature"] = temperature

        print("Weather Updated:", weather_data)

    except Exception as e:
        print("Weather API Error:", e)
