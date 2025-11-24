import streamlit as st
import requests
import os
from datetime import datetime

# Configuration
API_URL = os.getenv("AERON_API_URL", "http://core:8000")
# If running locally (not in docker), use localhost
if os.getenv("AERON_ENV") == "dev":
    API_URL = "http://localhost:8000"

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
                
                # Placeholder until streaming is fully implemented in app.py
                resp = requests.post(f"{API_URL}/chat", json={"message": prompt})
                if resp.status_code == 200:
                    data = resp.json()
                    full_response = data["response"]
                    message_placeholder.write(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                     st.error(f"Error: {resp.status_code} - {resp.text}")
                
        except Exception as e:
            st.error(f"Error communicating with Aeron Core: {e}")

elif page == "History":
    st.header("Memory Archive")
    query = st.text_input("Search memories...")
    
    if query:
        st.write(f"Searching for: {query}")
        try:
            resp = requests.get(f"{API_URL}/history", params={"query": query})
            if resp.status_code == 200:
                results = resp.json()
                for r in results:
                    with st.expander(f"{r['metadata'].get('timestamp', 'Unknown Date')} - {r['metadata'].get('speaker', 'Unknown')}"):
                        st.write(r['content'])
                        st.caption(f"Distance: {r.get('distance', 'N/A')}")
            else:
                st.error("Failed to search history")
        except Exception as e:
            st.error(f"Error: {e}")
            
    st.subheader("Recent Sessions")
    try:
        resp = requests.get(f"{API_URL}/sessions")
        if resp.status_code == 200:
            sessions = resp.json()
            for s in sessions:
                st.write(f"Session {s['id']} - {s['start_time']}")
    except:
        st.write("Could not load sessions.")

elif page == "Settings":
    st.header("System Settings")
    st.write("Configuration for voice, models, and storage.")
