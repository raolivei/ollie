from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import httpx

app = FastAPI(title="Aeron Core")

# Service URLs
WHISPER_URL = os.getenv("WHISPER_URL", "http://whisper:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
TTS_URL = os.getenv("TTS_URL", "http://tts:8000")

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(req: ChatRequest):
    # 1. Retrieve memory (mocked for now, normally calls MemorySystem)
    context = [] 
    
    # 2. Call LLM (Ollama)
    # We can use the python client here or raw HTTP
    # Using raw HTTP to demonstrate decoupled service
    async with httpx.AsyncClient() as client:
        payload = {
            "model": "llama3.1:8b",
            "messages": [{"role": "user", "content": req.message}],
            "stream": False
        }
        try:
            resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            resp.raise_for_status()
            llm_response = resp.json()["message"]["content"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

    return {"response": llm_response}

@app.get("/health")
def health():
    return {"status": "ok"}

