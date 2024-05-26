import inspect
import re

import streamlit as st
#from streamlit_chat import message
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
import python_weather
import argparse
import asyncio
from emoji import emojize
import os
from openai import OpenAI
import json

#from transformers import pipeline
from datetime import datetime
import time
from functools import wraps


def json_error_handler(max_retries=3, delay_seconds=8, spec=''):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (json.JSONDecodeError, IndexError, ValueError, AssertionError) as e:
                    print(f"Error: {type(e).__name__} - {e}")
                    print(f"Error decoding {spec} JSON on attempt {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        print(f"Retrying in {delay_seconds} seconds...")
                        time.sleep(delay_seconds)
                    else:
                        print("Max retries exceeded. Run Canceled")
                        break
            # return none?
            # return None
        return wrapper
    return decorator


class WeatherBot:
    def __init__(self):
        self.weather_client = None
        #self.openai_token = os.getenv("OPENAI_API_KEY")
        #OpenAI.api_key = streamlit.secrets.api_keys.OPENAI_API_KEY
        os.environ["OPENAI_API_KEY"] = st.secrets.api_keys.OPENAI_API_KEY
        self.model = "gpt-4o"

       # self.intent_classifier = pipeline('text-classification', model='distilbert-base-uncased-finetuned-sst-2-english')
        self.todays_date = datetime.now()


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

        #self.hourly_times = ['00:00:00', '03:00:00', '06:00:00', '09:00:00', '12:00:00', '15:00:00', '18:00:00', '21:00:00']
        self.time_of_day_mapping = {
            'Midnight': {'time': '00:00:00', 'index': 0},
            'Early Morning': {'time': '03:00:00', 'index': 1},
            'Morning': {'time': '06:00:00', 'index': 2},
            'Late Morning': {'time': '09:00:00', 'index': 3},
            'Noon': {'time': '12:00:00', 'index': 4},
            'Afternoon': {'time': '15:00:00', 'index': 5},
            'Evening': {'time': '18:00:00', 'index': 6},
            'Night': {'time': '21:00:00', 'index': 7}
        }

        self.parsed_query_data = {
                                #  "query_format":
                                  "ontology_labels": [],
                                  "intent": "",
                                  "date": "",
                                  "time": "",
                                  "location": "",
                                  "complete": False,
                                  "response": ""
        }

        self.pw_ontology = {
            "hourly": {
                "chances_of_fog": "int (percent)",
                "chances_of_frost": "int (percent)",
                "chances_of_high_temperature": "int (percent)",
                "chances_of_overcast": "int (percent)",
                "chances_of_rain": "int (percent)",
                "chances_of_remaining_dry": "int (percent)",
                "chances_of_snow": "int (percent)",
                "chances_of_sunshine": "int (percent)",
                "chances_of_thunder": "int (percent)",
                "chances_of_windy": "int (percent)",
                "cloud_cover": "int (percent)",
                "current_forecast_description": "str",
                "dew_point": "int (Celsius/Fahrenheit)",
                "feels_like": "int (Celsius/Fahrenheit)",
                "heat_index": "HeatIndex",
                "heat_rating": "HeatIndex",
                "humidity": "int (percent)",
                "weather_kind_object": "Kind",
                "weather_kind_emoji": "str",
                "weather_kind": "str",
                "weather_kind_value": "str",  # emoji value???
                "precipitation": "float (Millimeters/Inches)",
                "pressure": "float (Pascal/Inches)",
                "temperature": "int (Celsius/Fahrenheit)",
                "time": "time",
                "ultraviolet_object": "UltraViolet",
                "ultraviolet_index": "int",
                "ultraviolet_rating": "UltraViolet",
                "unit_object": "auto",
                "visibility": "int (Kilometers/Miles)",
                "wind_chill": "int (Celsius/Fahrenheit)",
                "wind_direction": "WindDirection",
                "wind_gust": "int (Kilometers_per_hour/Miles_per_hour)",
                "wind_speed": "int (Kilometers_per_hour/Miles_per_hour)"
            },
            "daily": {
                "date": "date",
                "highest_temperature": "int (Celsius/Fahrenheit)",
                "hourly_forecast_generator": "Iterable[HourlyForecast]",
                "language": "Locale",
                "language_value": "Locale",
                "lowest_temperature": "int (Celsius/Fahrenheit)",
                "moon_illumination": "int (percent)",
                "moon_phase_object": "Phase",
                "moon_phase_emoji": "str",
                "moon_phase_value": "str",
                "moonrise_time": "time | None",
                "moonset_time": "time | None",
                "total_snowfall": "float (Centimeters/Inches)",
                "sunlight_hours": "float (hours)",
                "sunrise_time": "time | None",
                "sunset_time": "time | None",
                "average_daily_temperature": "int (Celsius/Fahrenheit)",
                "measuring_unit_object": "auto"
            },
            "general": {
                "coordinates": "Tuple[float, float]",
                "country": "str",
                "daily_forecasts_generator": "Iterable[DailyForecast]",
                "datetime": "datetime",
                "current_forecast_description": "str",
                "feels_like": "int (Celsius/Fahrenheit)",
                "humidity": "int (percent)",
                "forecast_kind": "Kind",
                "forecast_kind_emoji": "str",
                "forecast_kind_value": "str",
                "local_population": "int",
                "language": "Locale",
                "location": "str",
                "precipitation": "float (Millimeters/Inches)",
                "pressure": "float (Pascal/Inches)",
                "region": "str",
                "temperature": "int (Celsius/Fahrenheit)",
                "uv_index": "UltraViolet",
                "uv_rate": "str",
                "forecast_unit_object": "auto",
                "visibility": "int (Kilometers/Miles)",
                "wind_direction_degrees": "int (degrees)",
                "wind_direction_emoji": "str",
                "wind_cardinal_direction": "str",
                "wind_direction_abbr": "str",
                "wind_speed": "int (KPH/MPH)"
            }
        }

        self.old_pw_ontology = {
                            #class python_weather.forecast.HourlyForecast
                            # HourlyForecast properties
                            "hourly": {
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
                                            "current forecast description": "description",
                                            "dew point": "dew_point",
                                            "feels like": "feels_like",
                                            "heat index": "heat_index.index",
                                            "heat rating": "heat_index.name",
                                            "humidity": "humidity",
                                            "weather kind object": "kind",
                                            "weather kind emoji": "kind.emoji",
                                            "weather kind": "kind.name",
                                            "weather kind value": "kind.value",  # emoji value???
                                            #"language": "locale",
                                            "precipitation": "precipitation",
                                            "pressure": "pressure",
                                            "temperature": "temperature",
                                            "time": "time",
                                            "ultraviolet object": "ultraviolet",
                                            "ultraviolet index": "ultraviolet.index",
                                            "ultraviolet rating": "ultraviolet.name",
                                            "unit object": "unit",
                                            "visibility": "visibility",
                                            "wind chill": "wind_chill",
                                            "wind direction": "wind_direction",
                                            "wind gust": "wind_gust",
                                            "wind speed": "wind_speed"
                            },
                            "daily": {

                                            #class python_weather.forecast.DailyForecast
                                            # DailyForecast properties
                                            "date": "date",
                                            "highest temperature": "highest_temperature",
                                            "hourly forecast generator": "hourly_forecasts",
                                            "language": "locale",
                                            "language value": "locale.value",
                                            "lowest temperature": "lowest_temperature",
                                            "moon illumination": "moon_illumination",
                                            "moon phase object": "moon_phase",
                                            "moon phase emoji": "moon_phase.emoji",
                                            "moon phase value": "moon_phase.value",
                                            "moonrise time": "moonrise",
                                            "moonset time": "moonset",
                                            "total snowfall": "snowfall",
                                            "sunlight hours": "sunlight",
                                            "sunrise time": "sunrise",
                                            "sunset time": "sunset",
                                            "average daily temperature": "temperature",
                                            "measuring unit object": "unit"
                            },
                            "general": {
                                            #class python_weather.forecast.Forecast
                                            # Forecast properties (general)
                                            "coordinates": "coordinates",
                                            "country": "country",
                                            "daily forecasts generator": "daily_forecasts",
                                            "datetime": "datetime",
                                            "current forecast description": "description",
                                            "feels like": "feels_like",
                                            "humidity": "humidity",
                                            "forecast kind": "kind.name",
                                            "forecast kind emoji": "kind.emoji",
                                            "forecast kind value": "kind.value",
                                            "local population": "local_population",
                                            "language": "locale",
                                            "location": "location",
                                            "precipitation": "precipitation",
                                            "pressure": "pressure",
                                            "region": "region",
                                            "temperature": "temperature",
                                            "uv index": "ultraviolet.index",
                                            "uv rate": "ultraviolet.name",
                                            "forecast unit object": "unit",
                                            "visibility": "visibility",
                                            "wind direction degrees": "wind_direction.degrees",
                                            "wind direction emoji": "wind_direction.emoji",
                                            "wind cardinal direction ": "wind_direction.name",
                                            "wind direction abbr.": "wind_direction.value",
                                            "wind speed": "wind_speed"
                            }
                        }



    async def init_weather_client(self):
        if 'weather_client' not in st.session_state:
            #new_loop = asyncio.new_event_loop()
            #asyncio.set_event_loop(new_loop)
            st.session_state.weather_client = python_weather.Client(unit=python_weather.METRIC)
        self.weather_client = st.session_state.weather_client
        #return streamlit.session_state.weather_client

    async def get_weather(self, location):
        async with self.weather_client:
            weather = await self.weather_client.get(location)
        return weather

    async def get_general_forecasts(self, weather):
        #general_forecasts = []
        forecast_info = {
            "coordinates": weather.coordinates,
            "country": weather.country,
            "datetime": weather.datetime.strftime("%H:%M:%S") if weather.datetime else "N/A",
            "current_forecast_description": weather.description,
            "feels_like": weather.feels_like,
            "humidity": weather.humidity,
            "forecast_kind": weather.kind.name,
            "forecast_kind_emoji": weather.kind.emoji,
            "forecast_kind_value": weather.kind.value,
            "local_population": weather.local_population,
            "language": weather.locale,
            "location": weather.location,
            "precipitation": weather.precipitation,
            "pressure": weather.pressure,
            "region": weather.region,
            "temperature": weather.temperature,
            "uv_index": weather.ultraviolet.index,
            "uv_rate": weather.ultraviolet.name,
            "forecast_unit_object": weather.unit,
            "visibility": weather.visibility,
            "wind_direction_degrees": weather.wind_direction.degrees,
            "wind_direction_emoji": weather.wind_direction.emoji,
            "wind_cardinal_direction": weather.wind_direction.name,
            "wind_direction_abbr": weather.wind_direction.value,
            "wind_speed": weather.wind_speed
        }

        #moonrise_time_str = DailyForecast.moonrise.strftime("%H:%M:%S")
        #general_forecasts.append(forecast_info)
        #print(day_counts)
        return forecast_info

    async def get_daily_forecasts(self, weather):
        daily_forecasts = []
        day_counts = 0
        for DailyForecast in weather.daily_forecasts:
            day_counts += 1
            forecast_info = {
                "date": DailyForecast.date,
                "highest_temperature": DailyForecast.highest_temperature,
                "hourly_forecast_generator": DailyForecast.hourly_forecasts,
                "language": DailyForecast.locale.name,
                "language_value": DailyForecast.locale.value,
                "lowest_temperature": DailyForecast.lowest_temperature,
                "moon_illumination": DailyForecast.moon_illumination,
                "moon_phase_object": DailyForecast.moon_phase,
                "moon_phase_emoji": DailyForecast.moon_phase.emoji,
                "moon_phase_value": DailyForecast.moon_phase.value,
                "moonrise_time": DailyForecast.moonrise.strftime("%H:%M:%S") if DailyForecast.moonrise else "N/A",
                "moonset_time": DailyForecast.moonset.strftime("%H:%M:%S") if DailyForecast.moonset else "N/A",
                "total_snowfall": DailyForecast.snowfall,
                "sunlight_hours": DailyForecast.sunlight,
                "sunrise_time": DailyForecast.sunrise.strftime("%H:%M:%S") if DailyForecast.sunrise else "N/A",
                "sunset_time": DailyForecast.sunset.strftime("%H:%M:%S") if DailyForecast.sunset else "N/A",
                "average_daily_temperature": DailyForecast.temperature,
                "measuring_unit_object": DailyForecast.unit
            }

            #moonrise_time_str = DailyForecast.moonrise.strftime("%H:%M:%S")
            daily_forecasts.append(forecast_info)
        #print(day_counts)
        return daily_forecasts

    async def get_hourly_forecasts(self, weather):
        hourly_forecasts = [[], [], []]
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
                    "chances_of_fog": HourlyForecast.chances_of_fog,
                    "chances_of_frost": HourlyForecast.chances_of_frost,
                    "chances_of_high_temperature": HourlyForecast.chances_of_high_temperature,
                    "chances_of_overcast": HourlyForecast.chances_of_overcast,
                    "chances_of_rain": HourlyForecast.chances_of_rain,
                    "chances_of_remaining_dry": HourlyForecast.chances_of_remaining_dry,
                    "chances_of_snow": HourlyForecast.chances_of_snow,
                    "chances_of_sunshine": HourlyForecast.chances_of_sunshine,
                    "chances_of_thunder": HourlyForecast.chances_of_thunder,
                    "chances_of_windy": HourlyForecast.chances_of_windy,
                    "cloud_cover": HourlyForecast.cloud_cover,
                    "current_forecast_description": HourlyForecast.description,
                    "dew_point": HourlyForecast.dew_point,
                    "feels_like": HourlyForecast.feels_like,
                    "heat_index": HourlyForecast.heat_index.index,
                    "heat_rating": HourlyForecast.heat_index.name,
                    "humidity": HourlyForecast.humidity,

                    "weather_kind_object": HourlyForecast.kind,
                    "weather_kind_emoji": HourlyForecast.kind.emoji,
                    "weather_kind": HourlyForecast.kind.name,
                    "weather_kind_value": HourlyForecast.kind.value, #emoji value???

                    #"locale": "forecast.hourly_forecasts.locale",
                    "precipitation": HourlyForecast.precipitation, #Millimeters or Inches
                    "pressure": HourlyForecast.pressure, #Pascal or Inches
                    "temperature": HourlyForecast.temperature, #Celsius or Fahrenheit
                    "time": HourlyForecast.time.strftime("%H:%M:%S"),
                    "ultraviolet_object": HourlyForecast.ultraviolet,
                    "ultraviolet_index": HourlyForecast.ultraviolet.index,
                    "ultraviolet_rating": HourlyForecast.ultraviolet.name,

                    "unit_object": HourlyForecast.unit,
                    "visibility": HourlyForecast.visibility,
                    "wind_chill": HourlyForecast.wind_chill,
                    "wind_direction_object": HourlyForecast.wind_direction,
                    "wind_direction_degrees": HourlyForecast.wind_direction.degrees,
                    "wind_direction_emoji": HourlyForecast.wind_direction.emoji,
                    "wind_direction_object": HourlyForecast.wind_direction.name,
                    "wind_direction_abbr": HourlyForecast.wind_direction.value,

                    "wind_gust": HourlyForecast.wind_gust,
                    "wind_speed": HourlyForecast.wind_speed
                }
                hourly_forecasts[i].append(forecast_info)

        return hourly_forecasts

    def clean_gpt_response(self, response):
        response = response.strip()
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                # Parse the JSON to ensure it's valid
                parsed_json = json.loads(json_str)
                return parsed_json
            except json.JSONDecodeError:
                print("Failed to parse JSON.")
                return None
        else:
            print("No JSON found in the response.")
            return None

    @json_error_handler(max_retries=3, delay_seconds=2, spec='Base GPT Prompt')
    async def prompt_gpt(self, role, prompt):
        """
        !!!!!!!THIS IS PAID!!!!!!!
        """
        GPTclient = OpenAI()
        completion = GPTclient.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": role},
                {"role": "user", "content": prompt}
            ]
        )
        response = completion.choices[0].message.content
        print(response)
        cleaned_response = self.clean_gpt_response(response)
        print(cleaned_response)
        #response = json.loads(cleaned_response)

        #assert isinstance(cleaned_response, dict)
        return cleaned_response

    async def extract_query(self, input):
        new_context = f'You are operating as a weather chat bot that when given: ' \
                      f'user input "{input}",' \
                      f' Todays date "{self.todays_date}",' \
                      f' available hourly data times "{self.time_of_day_mapping}",' \
                      f' the conversation state "{self.parsed_query_data}",' \
                      f' and this weather data ontology {self.pw_ontology}'

        prompt = new_context + f'Select the weather datapoint key from the ontology that would satisfy the query?'
        #role = (
        #    "You are a system that identifies what weather information the user is asking for. "
        #    "Then, leveraging the provided ontology, formulate a response string with the appropriate data keys embedded as f-string formatted string literals using curly braces {}."
        #    "Return your results as a results as a string with proper formatting and syntax. Be short and concise (up to 3 sentences) but friendly"
        #    "If the input is not a weather query, kindly explain that you cannot accomplish that task, then ask again what kind of weather information they may have."
        #    "If the expresses no interest in further queries and/or is ending the chat, have your only response be a simple one word string : 'END'."
        #    "Ensure your output contains only contains the strings mentioned about with and no additional text or characters so your response can be parsed accordingly."
        #)

        role = (
            """
            "1. Identify the single most relevant ontology parent key and weather datapoint key as a pair that satisfies each weather data request in the user input query. ex. [['hourly', 'chances_of_rain', ], ['daily', 'sunrise_time']]"
            "2. Choose the appropriate intent label from the list: ['get_weather', 'greeting', 'goodbye', 'unknown']."
            "3. Extract required data points: location (this could be a city, county, region or coordinates) and select a relative date term ['today', 'tomorrow', 'two days'] (default to 'today' if not specified).
            "4. If a time of day is specified select the appropriate label from the time_of_day_mapping. If not, it should remain an empty string."
            "5. Validate the weather request date to ensure it is within the range of today, tomorrow or in the next two days."
            "6. If all of the above points are successfully extracted set the "complete" value to true. Else remain false.
            "7. Considering the context that you extracted above formulate a chatbot response that is friendly and uses brackets where the data satifies the user request, once retrieved, 
            can be injected into the f-string and is followed by the appropriate datatype from the ontology. Use the ontological datapoint key as the injectable variable name ex. 'The percent chance of rain is "{chances_of_rain}"%.'"
            "8. If the date is not within the allowed range, formulate your chatbot_response to request the user to provide a valid date and give your apologies. The 'complete' value should remain False."
            "9. If any required data point is missing, formulate our chatbot_response to request the user to provide the missing information. The 'complete' value should remain False."
            "10. If the intent is unknown and the request is unable to be satisfied, formulate th chatbot_response to apologize and ask for different request that is within the aformentioed rules. The 'complete' value should remain False."
            "11. If the user wants to terminate the chat (intent: goodbye) say your goodbyes set 'complete' to true and fill the other JSON key values with NONE."

            "Only output a singular a structured JSON formatted array based on the example below with no extra leading or trailing text or characters:
            "{
              "ontology_labels": ["list_of_relevant_ontology_datapoint_pairs"],
              "intent": "intent_label",
              "date": "relative_date_terms",
              "time": "time_of_day_mapping",
              "location": "location_choice",
              "complete": Bool,
              "response": "chatbot_response"
            }"
            Finally check your output and remove any extra text that may be out side of the json array, check for trailing commas, missing or extra brackets, correct quotation marks, and remove special characters."
            """
        )

        response = await self.prompt_gpt(role, prompt)
        return response
    def construct_reply(self, parsed_query_data):
        print()
        dp_values = {}
        for dp in parsed_query_data['ontology_labels']:
            print()
            if dp[0] == 'general':
                print()
            elif dp[0] == 'daily':
                print()
            elif dp[0] == 'hourly':
                if parsed_query_data['date'] == 'today':
                    print()
                elif parsed_query_data['date'] == 'tomorrow':
                    tod_index = self.time_of_day_mapping[parsed_query_data['time']]['index']
                    dp_value = self.hourly_forecasts[1][tod_index][dp[1]]
                    dp_values[dp[1]] = dp_value
                else:


                    print()

        actual_response = parsed_query_data['response'].format(**dp_values)

        return actual_response
    async def run(self):
        await self.init_weather_client()
        st.title(emojize(":cloud_with_lightning::robot::cloud_with_lightning: Weather Chat Bot :cloud_with_lightning::robot::cloud_with_lightning:",
                                language='alias'))
        print('pycharm test')
        #st.markdown(self.css_bubble_style, unsafe_allow_html=True)

        #print(weather.temperature)
        #streamlit.write(f"Weather in {location}: {weather.temperature}°C")


        #self.message = st.chat_message("assistant")
        #self.message.write(f"Weather in {location}: {weather.temperature}°C")
        #self.message.write(f"The weather today in {location} is {weather.kind.name}")
        #self.message.write("Give me a location and then ask me about the weather there!")

        query = 'Will it snow tomorrow afternoon in Berlin, Germany?'

        #"'It looks like you want to know if it will rain today. Here are the relevant details:

        #- Hourly chances of rain: {hourly[chances_of_rain]}
        #- Daily precipitation: {daily[precipitation]}
        #- General precipitation: {general[precipitation]}'"

        self.parsed_query_data = await self.extract_query(query)
        if self.parsed_query_data['complete']:
            weather = await self.get_weather(self.parsed_query_data['location'])
            self.general_forecasts = await self.get_general_forecasts(weather)
            self.daily_forecasts = await self.get_daily_forecasts(weather)
            hourly_generators = [self.daily_forecasts[0]['hourly_forecast_generator'],
                                 self.daily_forecasts[1]['hourly_forecast_generator'],
                                 self.daily_forecasts[2]['hourly_forecast_generator']]
            self.hourly_forecasts = await self.get_hourly_forecasts(hourly_generators)
            print()
            out_message = self.construct_reply(self.parsed_query_data)

        else:
            print('retry')


        
        #while True:
        #    query = st.chat_input("Say Something",  key="chat_input")
        ##    if query:
         #       self.extract_query(query)
        #        break

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
