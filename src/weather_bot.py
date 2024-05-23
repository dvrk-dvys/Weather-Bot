import streamlit
import python_weather
import argparse


def main():
    print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    args = parser.parse_args()
    parser.add_argument('-c', '--config', default='./config/config.yaml', help='config file')

    main()