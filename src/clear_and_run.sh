#!/bin/bash

# Port to clear
PORT=8502

# Find the process using the port and kill it
PID=$(lsof -t -i:$PORT)
if [ -n "$PID" ]; then
    kill -9 $PID
    echo "Cleared port $PORT (killed process $PID)."
else
    echo "No process is using port $PORT."
fi

# Run your Streamlit app
#streamlit run weather_bot.py