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
    async def run(self):
        await self.init_weather_client()
        streamlit.title(emojize(":cloud_with_lightning::robot::cloud_with_lightning: Weather Chat Bot :cloud_with_lightning::robot::cloud_with_lightning:",
                                language='alias'))
        print('pycharm test')
        streamlit.markdown(self.css_bubble_style, unsafe_allow_html=True)
        location = 'Berlin, Germany'
        weather = await self.get_weather(location)
        #print(weather.temperature)
        #streamlit.write(f"Weather in {location}: {weather.temperature}°C")
        message(f"Weather in {location}: {weather.temperature}°C")
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
