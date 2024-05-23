import streamlit
import python_weather
import argparse
import asyncio
from emoji import emojize
import os


class WeatherBot:
    def __int__(self, args):
       # os.environ["STREAMLIT_EMAIL"] = 'ja.harr91@gmail.com'

        self.weather_client = self.init_weather_client()
        print()

    def init_weather_client(self):
        if 'weather_client' not in streamlit.session_state:
            streamlit.session_state.weather_client = python_weather.Client(format=python_weather.METRIC)
        return streamlit.session_state.weather_client

def main():
    os.environ["STREAMLIT_EMAIL"] = ""

    streamlit.title("Initializing Weather Chat Bot :cloud_with_lightning::robot::cloud_with_lightning:")
    print()

if __name__ == "__main__":
#    parser = argparse.ArgumentParser()

#    args = parser.parse_args()
#    parser.add_argument('-c', '--config', default='./config/config.yaml', help='config file')

    main()