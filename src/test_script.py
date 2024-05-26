import streamlit as st

# Try to retrieve the OpenAI API key from the secrets
try:
    api_key = st.secrets.api_keys.OPENAI_API_KEY
    st.write("API Key found:", api_key)
except KeyError as e:
    st.error(f"KeyError: {e}")