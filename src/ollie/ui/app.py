import streamlit as st
import requests
import os
from datetime import datetime

# Configuration
API_URL = os.getenv("OLLIE_API_URL", "http://core:8000")
# If running locally (not in docker), use localhost
if os.getenv("OLLIE_ENV") == "dev":
    API_URL = "http://localhost:8000"

st.set_page_config(page_title="Ollie", page_icon="🧠", layout="wide")

st.title("Ollie 🧠")

# Sidebar for navigation
page = st.sidebar.selectbox("Navigation", ["Chat", "Voice", "History", "Settings"])

if page == "Chat":
    st.header("Conversation")
    
    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "editing_message_id" not in st.session_state:
        st.session_state.editing_message_id = None
    if "message_counter" not in st.session_state:
        st.session_state.message_counter = 0
    
    # Ensure all existing messages have IDs (backward compatibility)
    for idx, msg in enumerate(st.session_state.messages):
        if "id" not in msg:
            msg["id"] = f"msg_{st.session_state.message_counter}"
            st.session_state.message_counter += 1

    # Initialize copy state
    if "copy_trigger" not in st.session_state:
        st.session_state.copy_trigger = None
    if "copy_text" not in st.session_state:
        st.session_state.copy_text = None

    # Display messages with edit and copy buttons
    for idx, msg in enumerate(st.session_state.messages):
        msg_id = msg.get("id", f"msg_{idx}")
        role = msg["role"]
        content = msg["content"]
        
        with st.chat_message(role):
            # Create columns for message content and buttons
            col1, col2, col3 = st.columns([10, 1, 1])
            
            with col1:
                # Show edit input if this message is being edited
                if st.session_state.editing_message_id == msg_id and role == "user":
                    edited_text = st.text_area(
                        "Edit message:",
                        value=content,
                        key=f"edit_{msg_id}",
                        height=100
                    )
                    save_col1, save_col2 = st.columns([1, 1])
                    with save_col1:
                        if st.button("💾 Save", key=f"save_{msg_id}"):
                            # Update message content
                            msg["content"] = edited_text
                            # Find message index
                            msg_idx = next((i for i, m in enumerate(st.session_state.messages) if m.get("id") == msg_id), None)
                            if msg_idx is not None:
                                # Remove all messages after this one
                                st.session_state.messages = st.session_state.messages[:msg_idx + 1]
                                # Clear editing state
                                st.session_state.editing_message_id = None
                                # Set flag to re-send the message
                                st.session_state.pending_resend = edited_text
                                st.rerun()
                    with save_col2:
                        if st.button("❌ Cancel", key=f"cancel_{msg_id}"):
                            st.session_state.editing_message_id = None
                            st.rerun()
                else:
                    st.write(content)
            
            with col2:
                # Copy button for all messages
                if st.button("📋", key=f"copy_{msg_id}", help="Copy message"):
                    st.session_state.copy_trigger = msg_id
                    st.session_state.copy_text = content
                    st.rerun()
            
            with col3:
                # Edit button only for user messages
                if role == "user" and st.session_state.editing_message_id != msg_id:
                    if st.button("✏️", key=f"edit_{msg_id}", help="Edit message"):
                        st.session_state.editing_message_id = msg_id
                        st.rerun()

    # Audio Input
    audio_value = st.audio_input("Record Voice")
    
    if audio_value:
        st.info("Transcribing...")
        try:
            # Send to upload endpoint to get transcription
            # We need a specific endpoint for "transcribe only" or use the existing upload
            # Let's assume we want to chat with it directly
            
            files = {"file": ("voice.wav", audio_value, "audio/wav")}
            resp = requests.post(f"{API_URL}/transcribe", files=files)
            
            if resp.status_code == 200:
                data = resp.json()
                # Combine segments
                transcript = " ".join([s["text"] for s in data["segments"]])
                
                # Show transcript
                st.success(f"You said: {transcript}")
                
                # Automatically send to chat if not empty
                if transcript.strip():
                    msg_id = f"msg_{st.session_state.message_counter}"
                    st.session_state.message_counter += 1
                    st.session_state.messages.append({"role": "user", "content": transcript, "id": msg_id})
                    with st.chat_message("user"):
                        st.write(transcript)
                    
                    # Call Chat API
                    with st.chat_message("assistant"):
                        message_placeholder = st.empty()
                        
                        chat_resp = requests.post(f"{API_URL}/chat", json={"message": transcript})
                        if chat_resp.status_code == 200:
                            response_text = chat_resp.json()["response"]
                            message_placeholder.write(response_text)
                            assistant_msg_id = f"msg_{st.session_state.message_counter}"
                            st.session_state.message_counter += 1
                            st.session_state.messages.append({"role": "assistant", "content": response_text, "id": assistant_msg_id})
                        else:
                            st.error("Chat Error")
            else:
                st.error("Transcription Failed")
                
        except Exception as e:
            st.error(f"Error: {e}")

    # Handle copy to clipboard
    if st.session_state.copy_trigger and st.session_state.copy_text:
        copy_text = st.session_state.copy_text
        st.session_state.copy_trigger = None
        
        # Use JavaScript to copy to clipboard
        copy_html = f"""
        <script>
        navigator.clipboard.writeText({repr(copy_text)}).then(function() {{
            console.log('Copied to clipboard');
        }}).catch(function(err) {{
            console.error('Failed to copy:', err);
        }});
        </script>
        """
        st.components.v1.html(copy_html, height=0)
        st.toast("Message copied to clipboard!", icon="✅")
    
    # Handle re-sending edited message
    if "pending_resend" in st.session_state and st.session_state.pending_resend:
        prompt = st.session_state.pending_resend
        st.session_state.pending_resend = None
        
        # Call API to get response
        try:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                
                resp = requests.post(f"{API_URL}/chat", json={"message": prompt})
                if resp.status_code == 200:
                    data = resp.json()
                    full_response = data["response"]
                    message_placeholder.write(full_response)
                    assistant_msg_id = f"msg_{st.session_state.message_counter}"
                    st.session_state.message_counter += 1
                    st.session_state.messages.append({"role": "assistant", "content": full_response, "id": assistant_msg_id})
                else:
                    st.error(f"Error: {resp.status_code} - {resp.text}")
            
        except Exception as e:
            st.error(f"Error communicating with Ollie Core: {e}")

    # Input
    prompt = st.chat_input("Say something...")
    if prompt:
        # Add user message
        msg_id = f"msg_{st.session_state.message_counter}"
        st.session_state.message_counter += 1
        st.session_state.messages.append({"role": "user", "content": prompt, "id": msg_id})
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
                    assistant_msg_id = f"msg_{st.session_state.message_counter}"
                    st.session_state.message_counter += 1
                    st.session_state.messages.append({"role": "assistant", "content": full_response, "id": assistant_msg_id})
                else:
                     st.error(f"Error: {resp.status_code} - {resp.text}")
                
        except Exception as e:
            st.error(f"Error communicating with Ollie Core: {e}")


elif page == "Voice":
    st.header("🎤 Real-Time Voice Capture")
    
    st.info("""
    **How it works:**
    1. Click 'Start Recording' to begin capturing audio
    2. Speak naturally - your voice is transcribed in real-time
    3. Transcripts are automatically saved to your conversation history
    4. Click 'Stop Recording' when finished
    """)
    
    # Recording state
    if "recording" not in st.session_state:
        st.session_state.recording = False
    if "voice_transcripts" not in st.session_state:
        st.session_state.voice_transcripts = []
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("🎙️ Start Recording", disabled=st.session_state.recording, type="primary"):
            st.session_state.recording = True
            st.rerun()
        
        if st.button("⏹️ Stop Recording", disabled=not st.session_state.recording):
            st.session_state.recording = False
            st.rerun()
    
    # Status indicator
    if st.session_state.recording:
        st.warning("🔴 **Recording in progress...** Speak now!")
    else:
        st.info("⏸️ Recording stopped. Click 'Start Recording' to begin.")
    
    # Audio recorder - Streamlit's built-in audio input
    if st.session_state.recording:
        audio_data = st.audio_input("Record your voice", key="voice_recorder")
        
        if audio_data is not None:
            # Send audio to backend for transcription
            try:
                with st.spinner("Transcribing audio..."):
                    files = {"file": ("recording.wav", audio_data, "audio/wav")}
                    
                    # First, transcribe immediately for display
                    transcribe_resp = requests.post(f"{API_URL}/transcribe", files=files, timeout=30)
                    if transcribe_resp.status_code == 200:
                        transcribe_data = transcribe_resp.json()
                        transcript = " ".join([s["text"] for s in transcribe_data.get("segments", [])])
                        
                        if transcript.strip():
                            st.session_state.voice_transcripts.append({
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "text": transcript
                            })
                            
                            # Show transcript
                            st.success(f"✅ **Transcript:** {transcript}")
                            
                            # Also upload for background processing and storage
                            upload_resp = requests.post(f"{API_URL}/upload_audio", files=files, timeout=30)
                            if upload_resp.status_code == 200:
                                result = upload_resp.json()
                                st.caption(f"Saved to session: {result.get('session_id')}")
                            
                            # Optionally auto-send to chat
                            if st.button("💬 Send to Chat", key="send_to_chat"):
                                if "messages" not in st.session_state:
                                    st.session_state.messages = []
                                if "message_counter" not in st.session_state:
                                    st.session_state.message_counter = 0
                                msg_id = f"msg_{st.session_state.message_counter}"
                                st.session_state.message_counter += 1
                                st.session_state.messages.append({"role": "user", "content": transcript, "id": msg_id})
                                st.info("Message added to chat! Switch to Chat tab to see the conversation.")
                    else:
                        st.error(f"Transcription failed: {transcribe_resp.status_code}")
            except Exception as e:
                st.error(f"Error processing audio: {e}")
    
    # Show recent transcripts from this session
    if st.session_state.voice_transcripts:
        st.divider()
        st.subheader("📝 Recent Transcripts")
        for idx, transcript in enumerate(reversed(st.session_state.voice_transcripts[-10:])):
            with st.expander(f"{transcript['timestamp']}"):
                st.write(transcript['text'])

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
