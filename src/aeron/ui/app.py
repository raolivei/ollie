import streamlit as st
import requests
import os

# Configuration
API_URL = os.getenv("AERON_API_URL", "http://localhost:8000")

st.set_page_config(page_title="Aeron", page_icon="🧠", layout="wide")

st.title("Aeron 🧠")

# Sidebar for navigation
page = st.sidebar.selectbox("Navigation", ["Chat", "History", "Settings"])

if page == "Chat":
    st.header("Conversation")
    
    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Input
    prompt = st.chat_input("Say something...")
    if prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Call API (mocked for now if not running)
        try:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                # Streaming response from API
                # response = requests.post(f"{API_URL}/chat", json={"message": prompt}, stream=True)
                # for chunk in response...
                
                full_response = "This is a placeholder response from Aeron."
                message_placeholder.write(full_response)
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"Error communicating with Aeron Core: {e}")

elif page == "History":
    st.header("Memory Archive")
    query = st.text_input("Search memories...")
    if query:
        st.write(f"Searching for: {query}")
        # Search API call here

elif page == "Settings":
    st.header("System Settings")
    st.write("Configuration for voice, models, and storage.")

