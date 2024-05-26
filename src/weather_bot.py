import inspect
import re

import streamlit as st
from streamlit_chat import message
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space
import python_weather
import argparse
import nest_asyncio
import asyncio
from emoji import emojize
import os
from openai import OpenAI
import json
from datetime import datetime
import time
from functools import wraps

import asyncio

nest_asyncio.apply()

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
        os.environ["OPENAI_API_KEY"] = st.secrets.api_keys.OPENAI_API_KEY
        self.model = "gpt-4o"
        self.todays_date = datetime.now()
        self.day_of_week = self.todays_date.strftime('%A')


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

        self.time_of_day_mapping = {
            'midnight': {'time': '00:00:00', 'index': 0},
            'early morning': {'time': '03:00:00', 'index': 1},
            'morning': {'time': '06:00:00', 'index': 2},
            'late morning': {'time': '09:00:00', 'index': 3},
            'noon': {'time': '12:00:00', 'index': 4},
            'afternoon': {'time': '15:00:00', 'index': 5},
            'evening': {'time': '18:00:00', 'index': 6},
            'night': {'time': '21:00:00', 'index': 7}
        }

        self.parsed_query_data = {
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
                "heat_index": "Celsius/Fahrenheit",
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

    async def init_weather_client(self):
        if 'weather_client' not in st.session_state:
            st.session_state.weather_client = python_weather.Client(unit=python_weather.METRIC)
        #self.weather_client = st.session_state.weather_client
        return st.session_state.weather_client

    async def get_weather(self, location):
        weather_client = await self.init_weather_client()
        #asyncio.wait(self.weather_client.get(location))
        weather = await asyncio.wait_for(weather_client.get(location), timeout=5)
        await weather_client.close()
        return weather

    def get_general_forecasts(self, weather):
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
        return forecast_info

    def get_daily_forecasts(self, weather):
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
            daily_forecasts.append(forecast_info)
        #print(day_counts)
        return daily_forecasts

    def get_hourly_forecasts(self, weather):
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
                json_str = json_str.replace('\\', '')
                json_str = json_str.replace('//', '')

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
        new_context = f' You are operating as a weather chat bot that when given: ' \
                      f' user input "{input}",' \
                      f' Todays day of the week "{self.day_of_week}", Todays Date "{self.todays_date}",' \
                      f' available hourly data times "{self.time_of_day_mapping}",' \
                      f' the conversation state "{self.parsed_query_data}",' \
                      f' and this weather data ontology {self.pw_ontology}'

        prompt = new_context + f'Select the weather datapoint key from the ontology that would satisfy the query?'

        role = (
            """
            "1. Identify the single most relevant ontology parent key and weather datapoint key as a pair that satisfies each weather data request in the user input query. ex. [['hourly', 'chances_of_rain', ], ['daily', 'sunrise_time']]"
            "2. Choose the appropriate intent label from the list: ['get_weather', 'greeting', 'goodbye', 'unknown']."
            "3. Extract required data points: location (this could be a city, county, region or coordinates) and select a relative date term ['today', 'tomorrow', 'two days'] (default to 'today' if not specified)."
            "4. If a time of day is specified select the appropriate label from the time_of_day_mapping. If not, it should remain an empty string."
            "5. Calculate the distance between today's date and the requested date using the day of the week and/or today's date. Ensure the requested date is within the range from today to two days from today's date. 
            "If the request is out of the range, the date value should remain empty and you should apologiye and request they ask for a date that is iwthin the availability range.
            "6. If all of the above points are successfully extracted set the "complete" value to true. Else remain false."
            "7. Considering the context that you extracted above (Location, relative date, time of day, intent) formulate a chatbot response that is friendly and contains this data explicitely. 
            "Also uses brackets surrounding the selected ontological datapoint key(s) as an injectable variable(s) to satify the user data request which will be retrieved later."
            "The weather datapoints will be injected into the f-string and is followed by the appropriate datatype symbol (%, KPH, MPH, C°, F°, K, Ect.) from the ontology. EX: 'The percent chance of rain this afternoon in Berlin, Germany is "{chances_of_rain}"%.'"
            "8. If any required data point is missing, formulate our chatbot_response to request the user to provide the missing information. The 'complete' value should remain False."
            "9. If the intent is unknown and the request is unable to be satisfied, formulate th chatbot_response to apologize and ask for different request that is within the aformentioned rules. The 'complete' value should remain False."
            "10. If the user wants to terminate the chat (intent: goodbye) say your goodbyes set 'complete' to true and fill the other JSON key values with NONE."

            "Only output a singular a structured JSON formatted array based on the example below :
            "{
              "ontology_labels": ["list_of_relevant_ontology_datapoint_pairs"],
              "intent": "intent_label",
              "date": "relative_date_terms",
              "time": "time_of_day_mapping",
              "location": "location_choice",
              "complete": Bool,
              "response": "chatbot_response"
            }"
            Finally check your output and remove any extra text that may be out side of the json array, check for trailing commas, missing or extra brackets, remove unneccessary slashes, correct quotation marks."
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
                    tod_index = self.time_of_day_mapping[parsed_query_data['time'].lower()]['index']
                    dp_value = self.hourly_forecasts[0][tod_index][dp[1]]
                    dp_values[dp[1]] = dp_value
                elif parsed_query_data['date'] == 'tomorrow':
                    tod_index = self.time_of_day_mapping[parsed_query_data['time'].lower()]['index']
                    dp_value = self.hourly_forecasts[1][tod_index][dp[1]]
                    dp_values[dp[1]] = dp_value
                else:
                    tod_index = self.time_of_day_mapping[parsed_query_data['time'].lower()]['index']
                    dp_value = self.hourly_forecasts[2][tod_index][dp[1]]
                    dp_values[dp[1]] = dp_value

        actual_response = parsed_query_data['response'].format(**dp_values)
        return actual_response

    def reset_conversation_state(self):
        parsed_query_data = {
                                  "ontology_labels": [],
                                  "intent": "",
                                  "date": "",
                                  "time": "",
                                  "location": "",
                                  "complete": False,
                                  "response": ""
        }
        return parsed_query_data

    async def get_input(self):
        input_text = st.text_input("Ask me about the weather!", key="input")
       # input_text = st.chat_input("Ask me about the weather!")
        return input_text

    async def run(self):
        st.title(emojize(":cloud_with_lightning::robot::cloud_with_lightning: Weather Chat Bot :cloud_with_lightning::robot::cloud_with_lightning:",
                                language='alias'))
        print('pycharm test')
        if 'user_input' not in st.session_state:
            st.session_state['user_input'] = []

        if "bot_response" not in st.session_state:
            st.session_state['bot_response'] = []

        user_input = await self.get_input()

        # query = 'Will it snow tomorrow afternoon in Berlin, Germany?'

        if user_input:
            self.parsed_query_data = await asyncio.wait_for(self.extract_query(user_input), timeout=5)
            with st.spinner('Thinking...'):
                time.sleep(3)
            try:
                self.parsed_query_data['complete']
            except:
                print()

            if self.parsed_query_data['complete']:
                with st.spinner('Building...'):
                    time.sleep(3)
                weather = await asyncio.wait_for(self.get_weather(self.parsed_query_data['location']), timeout=5)

                self.general_forecasts = self.get_general_forecasts(weather)
                self.daily_forecasts = self.get_daily_forecasts(weather)
                hourly_generators = [self.daily_forecasts[0]['hourly_forecast_generator'],
                                     self.daily_forecasts[1]['hourly_forecast_generator'],
                                     self.daily_forecasts[2]['hourly_forecast_generator']]
                self.hourly_forecasts = self.get_hourly_forecasts(hourly_generators)
                bot_output = self.construct_reply(self.parsed_query_data)
                self.parsed_query_data = self.reset_conversation_state
            else:
                print('retry')
                bot_output = self.parsed_query_data['response']

            #with st.chat_message("assistant"):
             #   st.markdown(bot_output)

            st.session_state.user_input.append(user_input)
            st.session_state.bot_response.append(bot_output)
        message_history = st.empty()

        if st.session_state['user_input']:
            for i in range(len(st.session_state['user_input']) - 1, -1, -1):
                message(st.session_state["user_input"][i],
                        key=str(i), avatar_style="big-smile")
                message(st.session_state['bot_response'][i],
                        avatar_style="bottts-neutral", is_user=True
                        , key=str(i) + 'data_by_user')

async def main():
    wbot = WeatherBot()
    await wbot.run()
if __name__ == "__main__":
    st.set_option('server.port', 8502)
    asyncio.run(main())



# hourly questions
#'Will it snow tomorrow afternoon in Berlin, Germany?'
# What will be the heat and uv index today at noon in berlin?
# What will the weather be like monday at around noon in nyc?
#