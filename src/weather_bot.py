import inspect

import streamlit
from streamlit_chat import message
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
import python_weather
import argparse
import asyncio
from emoji import emojize
import os


class WeatherBot:
    def __init__(self):
        self.weather_client = None
        self.css_bubble_style = """
            <style>
            .chat-container {
                display: flex;
                flex-direction: column;
                width: 100%;
                max-width: 600px;
                margin: 0 auto;
            }

            .chat-bubble {
                border-radius: 20px;
                padding: 10px 20px;
                margin: 5px 0;
                max-width: 80%;
            }

            .user-bubble {
                align-self: flex-end;
                background-color: #DCF8C6;
                color: #000;
            }

            .bot-bubble {
                align-self: flex-start;
                background-color: #ECECEC;
                color: #000;
            }
            </style>
            """

        self.pw_ontology = {
                            #class python_weather.forecast.HourlyForecast
                            # HourlyForecast properties
                            "chances of fog": "chances_of_fog",
                            "chances of frost": "chances_of_frost",
                            "chances of high temperature": "chances_of_high_temperature",
                            "chances of overcast": "chances_of_overcast",
                            "chances of rain": "chances_of_rain",
                            "chances of remaining dry": "chances_of_remaining_dry",
                            "chances of snow": "chances_of_snow",
                            "chances of sunshine": "chances_of_sunshine",
                            "chances of thunder": "chances_of_thunder",
                            "chances of windy": "chances_of_windy",
                            "cloud cover": "cloud_cover",
                            "description": "description",
                            "dew point": "dew_point",
                            "feels like": "feels_like",
                            "heat index": "heat_index.index",
                            "humidity": "humidity",
                            "kind": "kind",
                            "locale": "locale",
                            "precipitation": "precipitation",
                            "pressure": "pressure",
                            "temperature": "temperature",
                            "time": "time",
                            "ultraviolet": "ultraviolet",
                            "unit": "unit",
                            "visibility": "visibility",
                            "wind chill": "wind_chill",
                            "wind direction": "wind_direction",
                            "wind gust": "wind_gust",
                            "wind speed": "wind_speed",

                            #class python_weather.forecast.DailyForecast
                            # DailyForecast properties
                            "date": "date",
                            "highest temperature": "highest_temperature",
                            "hourly forecasts": "hourly_forecasts",
                            "locale, language": "locale",
                            "lowest temperature": "lowest_temperature",
                            "moon illumination": "moon_illumination",
                            "moon phase object": "moon_phase",
                            "emoji": "moon_phase.emoji",
                            "value": "moon_phase.value",
                            "moonrise time": "moonrise",
                            "moonset time": "moonset",
                            "total snowfall": "snowfall",
                            "sunlight hours": "sunlight",
                            "sunrise time": "sunrise",
                            "sunset time": "sunset",
                            "average daily temperature": "temperature",
                            "measuring unit": "unit",

                            #class python_weather.forecast.Forecast
                            # Forecast properties (general)
                            "coordinates": "coordinates",
                            "country": "country",
                            "daily forecasts": "daily_forecasts",
                            "datetime": "datetime",
                            "forecast description": "description",
                            "forecast feels like": "feels_like",
                            "forecast humidity": "humidity",
                            "forecast kind, conditions, state": "kind",
                            "local population": "local_population",
                            "forecast locale, language": "locale",
                            "location": "location",
                            "forecast precipitation": "precipitation",
                            "forecast pressure": "pressure",
                            "region": "region",
                            "forecast temperature": "temperature",
                            "forecast ultraviolet": "ultraviolet",
                            "forecast unit": "unit",
                            "forecast visibility": "visibility",
                            "forecast wind direction": "wind_direction",
                            "forecast wind speed": "wind_speed",

                            # Kind
                            "cloudy": "kind",
                            "forecast kind emoji": "kind.emoji",

                            # UltraViolet
                            "uv degree": "ultraviolet",
                            "uv index": "ultraviolet.index",
                            "uv rate": "ultraviolet.name",

                            # WindDirection
                            #"wind direction": "wind_direction",
                            "wind direction degrees": "wind_direction.degrees",
                            "wind direction emoji": "wind_direction.emoji",
                            "wind cardinal direction ": "wind_direction.name",
                            "wind direction value": "wind_direction.value"
        }


    async def init_weather_client(self):
        if 'weather_client' not in streamlit.session_state:
            #new_loop = asyncio.new_event_loop()
            #asyncio.set_event_loop(new_loop)
            streamlit.session_state.weather_client = python_weather.Client(unit=python_weather.METRIC)
        self.weather_client = streamlit.session_state.weather_client
        #return streamlit.session_state.weather_client

    async def get_weather(self, location):
        async with self.weather_client:
            weather = await self.weather_client.get(location)
        return weather

    async def get_hourly_forecasts(self, weather):
        hourly_forecasts = [[], [] ,[]]
        if isinstance(weather, python_weather.forecast.Forecast):
            hourly_generators = []
            for DailyForecast in weather.daily_forecasts:
                hourly_generators.append(DailyForecast.hourly_forecasts)
        else:
            hourly_generators = weather
        for i, generator in enumerate(hourly_generators):
            for HourlyForecast in generator:
                forecast_info = {
                    # all are percentages except description obviously
                    "chances of fog": HourlyForecast.chances_of_fog,
                    "chances of frost": HourlyForecast.chances_of_frost,
                    "chances of high temperature": HourlyForecast.chances_of_high_temperature,
                    "chances of overcast": HourlyForecast.chances_of_overcast,
                    "chances of rain": HourlyForecast.chances_of_rain,
                    "chances of remaining dry": HourlyForecast.chances_of_remaining_dry,
                    "chances of snow": HourlyForecast.chances_of_snow,
                    "chances of sunshine": HourlyForecast.chances_of_sunshine,
                    "chances of thunder": HourlyForecast.chances_of_thunder,
                    "chances of windy": HourlyForecast.chances_of_windy,
                    "cloud cover": HourlyForecast.cloud_cover,
                    "description": HourlyForecast.description,
                    "dew point": HourlyForecast.dew_point,
                    "feels like": HourlyForecast.feels_like,
                    "heat index": HourlyForecast.heat_index.index,
                    "heat rating": HourlyForecast.heat_index.name,
                    "humidity": HourlyForecast.humidity,

                    "weather kind object": HourlyForecast.kind,
                    "weather kind emoji": HourlyForecast.kind.emoji,
                    "weather kind": HourlyForecast.kind.name,
                    "weather kind value": HourlyForecast.kind.value, #emoji value???

                    #"locale": "forecast.hourly_forecasts.locale",
                    "precipitation": HourlyForecast.precipitation, #Millimeters or Inches
                    "pressure": HourlyForecast.pressure, #Pascal or Inches
                    "temperature": HourlyForecast.temperature, #Celcius or Fahrenheit
                    "time": HourlyForecast.time.strftime("%H:%M:%S"),
                    "ultraviolet object": HourlyForecast.ultraviolet,
                    "ultraviolet index": HourlyForecast.ultraviolet.index,
                    "ultraviolet rating": HourlyForecast.ultraviolet.name,

                    "unit object": HourlyForecast.unit,
                    "visibility": HourlyForecast.visibility,
                    "wind chill": HourlyForecast.wind_chill,
                    "wind direction object": HourlyForecast.wind_direction,
                    "wind direction degrees": HourlyForecast.wind_direction.degrees,
                    "wind direction emoji": HourlyForecast.wind_direction.emoji,
                    "wind direction object": HourlyForecast.wind_direction.name,
                    "wind direction abbr.": HourlyForecast.wind_direction.value,

                    "wind gust": HourlyForecast.wind_gust,
                    "wind speed": HourlyForecast.wind_speed
                }
                hourly_forecasts[i].append(forecast_info)

        return hourly_forecasts


    async def get_daily_forecasts(self, weather):
        daily_forecasts = []
        day_counts = 0
        for DailyForecast in weather.daily_forecasts:
            day_counts += 1
            forecast_info = {
                "date": DailyForecast.date,
                "highest temperature": DailyForecast.highest_temperature,
                "hourly forecast generator": DailyForecast.hourly_forecasts,
                "language": DailyForecast.locale.name,
                "language value": DailyForecast.locale.value,
                "lowest temperature": DailyForecast.lowest_temperature,
                "moon illumination": DailyForecast.moon_illumination,
                "moon phase object": DailyForecast.moon_phase,
                "moon phase emoji": DailyForecast.moon_phase.emoji,
                "moon phase value": DailyForecast.moon_phase.value,
                "moonrise time": DailyForecast.moonrise.strftime("%H:%M:%S") if DailyForecast.moonrise else "N/A",
                "moonset time": DailyForecast.moonset.strftime("%H:%M:%S") if DailyForecast.moonset else "N/A",
                "total snowfall": DailyForecast.snowfall,
                "sunlight hours": DailyForecast.sunlight,
                "sunrise time": DailyForecast.sunrise.strftime("%H:%M:%S") if DailyForecast.sunrise else "N/A",
                "sunset time": DailyForecast.sunset.strftime("%H:%M:%S") if DailyForecast.sunset else "N/A",
                "average daily temperature": DailyForecast.temperature,
                "measuring unit object": DailyForecast.unit
            }

            #moonrise_time_str = DailyForecast.moonrise.strftime("%H:%M:%S")
            daily_forecasts.append(forecast_info)
        #print(day_counts)
        return daily_forecasts

    async def run(self):
        await self.init_weather_client()
        streamlit.title(emojize(":cloud_with_lightning::robot::cloud_with_lightning: Weather Chat Bot :cloud_with_lightning::robot::cloud_with_lightning:",
                                language='alias'))
        print('pycharm test')
        streamlit.markdown(self.css_bubble_style, unsafe_allow_html=True)
        location = 'Berlin, Germany'
        weather = await self.get_weather(location)
        daily_forecasts = await self.get_daily_forecasts(weather)
        hourly_generators = [daily_forecasts[0]['hourly forecast generator'], daily_forecasts[1]['hourly forecast generator'], daily_forecasts[2]['hourly forecast generator']]
        hourly_forecasts = await self.get_hourly_forecasts(hourly_generators)
        #print(weather.temperature)
        #streamlit.write(f"Weather in {location}: {weather.temperature}°C")
        message(f"Weather in {location}: {weather.temperature}°C")
        message(f"The weather today in {location} is {weather.kind.name}")

        print()

        #if 'messages' not in streamlit.session_state:
        #    streamlit.session_state.messages = []
        #streamlit.session_state.messages.append(f"Weather in {location}: {weather.temperature}°C")
        #streamlit.write(streamlit.session_state.messages)

if __name__ == "__main__":
#    parser = argparse.ArgumentParser()

#    args = parser.parse_args()
#    parser.add_argument('-c', '--config', default='./config/config.yaml', help='config file')
    w_bot = WeatherBot()
    asyncio.run(w_bot.run())
