import os
import folium
from dotenv import load_dotenv

def getAPIKeyFromEnv():
        load_dotenv(".env")
        return os.getenv("web_api_key")

city_lat = 52.52
city_lon = 13.405
api_key = getAPIKeyFromEnv()

m = folium.Map(location=[city_lat, city_lon], zoom_start=7)

# OpenWeatherMap Tile Layer
tiles_url = f'https://tile.openweathermap.org/map/pressure_new/{{z}}/{{x}}/{{y}}.png?appid={api_key}'

folium.TileLayer(
    tiles=tiles_url,
    attr='OpenWeatherMap',
    name='Weather Pressure'
).add_to(m)

m.save('./static/weather_map.html')


"""
from datetime import datetime, timedelta

# Create a datetime object
#date = datetime.now().strftime("%d/%m/%Y")
date = datetime.now()

print(date.strftime("%d/%m/%Y"))

date = date + timedelta(days=4)

print(date.strftime("%d/%m/%Y"))
"""