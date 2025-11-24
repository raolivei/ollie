from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
import os
import httpx
import shutil
import uuid
from datetime import datetime
from typing import List, Optional

from aeron.memory.retrieval import MemorySystem
from aeron.storage.database import get_db, init_db
from aeron.storage.models import Session, Conversation

app = FastAPI(title="Aeron Core")

# Service URLs
WHISPER_URL = os.getenv("WHISPER_URL", "http://whisper:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
TTS_URL = os.getenv("TTS_URL", "http://tts:8000")
DATA_DIR = os.getenv("DATA_DIR", "/data")

# Initialize Memory System
memory_system = MemorySystem(persist_path=f"{DATA_DIR}/chroma")

# Ensure DB is initialized
init_db()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    audio_url: Optional[str] = None

async def process_audio_background(file_path: str, session_id: int):
    """Background task to transcribe and index audio."""
    async with httpx.AsyncClient() as client:
        try:
            # Call Whisper Service
            resp = await client.post(
                f"{WHISPER_URL}/transcribe_path", 
                json={"path": file_path}
            )
            resp.raise_for_status()
            data = resp.json()
            
            full_text = " ".join([seg["text"] for seg in data["segments"]])
            
            # Save to DB
            with get_db() as db:
                conv = Conversation(
                    session_id=session_id,
                    speaker="User",
                    transcript=full_text,
                    audio_path=file_path,
                    timestamp=datetime.utcnow()
                )
                db.add(conv)
                db.commit()
                db.refresh(conv)
                conv_id = conv.id
                
            # Index in Memory
            memory_system.add_memory(
                text=full_text,
                metadata={
                    "speaker": "User",
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "conversation"
                },
                memory_id=f"conv_{conv_id}"
            )
            
            print(f"Successfully processed audio: {file_path}")
            
        except Exception as e:
            print(f"Error processing audio {file_path}: {e}")

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # 1. Retrieve memory
    context_docs = memory_system.search_memory(req.message, n_results=3)
    context_str = "\n".join([d["content"] for d in context_docs])
    
    system_prompt = f"""You are Aeron, a helpful AI assistant. 
    Use the following context from past conversations to answer the user's question if relevant.
    
    Context:
    {context_str}
    """
    
    # 2. Call LLM (Ollama)
    async with httpx.AsyncClient() as client:
        payload = {
            "model": "llama3.1:8b",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.message}
            ],
            "stream": False
        }
        try:
            resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            resp.raise_for_status()
            llm_response = resp.json()["message"]["content"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

    # 3. Save interaction to DB (User message and AI response)
    # Note: Ideally we pass session_id. If None, create new session.
    session_id = req.session_id
    with get_db() as db:
        if not session_id:
            new_session = Session()
            db.add(new_session)
            db.commit()
            session_id = new_session.id
            
        # Save User Message
        user_conv = Conversation(
            session_id=session_id,
            speaker="User",
            transcript=req.message,
            timestamp=datetime.utcnow()
        )
        db.add(user_conv)
        
        # Save AI Response
        ai_conv = Conversation(
            session_id=session_id,
            speaker="Aeron",
            transcript=llm_response,
            timestamp=datetime.utcnow()
        )
        db.add(ai_conv)
        db.commit()
        
        # Index AI response too? Maybe. Let's skip for now to avoid loop, or index it.
        # memory_system.add_memory(...)

    return {"response": llm_response}

@app.post("/upload_audio")
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    session_id: int = None
):
    # Create directory
    save_dir = f"{DATA_DIR}/audio/{datetime.now().strftime('%Y-%m-%d')}"
    os.makedirs(save_dir, exist_ok=True)
    
    filename = f"{uuid.uuid4()}.wav"
    file_path = os.path.join(save_dir, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create session if needed
    if not session_id:
        with get_db() as db:
            new_session = Session()
            db.add(new_session)
            db.commit()
            session_id = new_session.id

    # Trigger background processing
    background_tasks.add_task(process_audio_background, file_path, session_id)
    
    return {"status": "processing", "file_path": file_path, "session_id": session_id}

@app.get("/sessions")
def get_sessions(limit: int = 10):
    with get_db() as db:
        sessions = db.query(Session).order_by(Session.start_time.desc()).limit(limit).all()
        return sessions

@app.get("/history")
def search_history(query: str):
    # Use memory system for semantic search
    results = memory_system.search_memory(query)
    return results

@app.get("/status")
async def status():
    # Check Ollama model
    model_version = "unknown"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                # Look for aeron-lora
                for m in models:
                    if m["name"].startswith("aeron-lora"):
                        model_version = m["name"]
                        break
    except:
        pass
        
    return {
        "status": "online",
        "model": model_version,
        "training_job": "Scheduled 2 AM"
    }

@app.get("/health")
def health():
    return {"status": "ok"}
