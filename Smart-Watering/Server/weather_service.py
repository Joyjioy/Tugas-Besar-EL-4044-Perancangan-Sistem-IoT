import requests

# Import credentials dan settings
from config import (
    WEATHER_API_KEY,
    CITY,
    COUNTRY
)

# Global dictionary
weather_data = {
    "rain": False,
    "humidity": 0,
    "temperature": 0
}


def update_weather():
    """
    Mengambil data cuaca terkini dari API OpenWeatherMap.
    Jika berhasil, fungsi ini akan memperbarui dictionary 'weather_data' secara in-place.
    """
    try:
        # Endpoint URL dan set parameter konfigurasi
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={CITY},{COUNTRY}"
            f"&appid={WEATHER_API_KEY}"
            f"&units=metric"
        )

        # HTTP get request ke server OpenWeather
        response = requests.get(url)

        # Parsing format JSON ke dictionary python
        data = response.json()

        # Ekstraksi data suhu humidity dan temperature
        humidity = data["main"]["humidity"]
        temperature = data["main"]["temp"]

        # Deteksi hujan
        rain = "rain" in data

        # Memperbarui nilai dictionary global
        weather_data["rain"] = rain
        weather_data["humidity"] = humidity
        weather_data["temperature"] = temperature

        print("Weather Updated:", weather_data)

    # Error Handling
    except Exception as e:
        print("Weather API Error:", e)
