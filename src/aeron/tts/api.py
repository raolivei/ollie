from fastapi import FastAPI
from pydantic import BaseModel
from .voice_service import TTSService
import os

app = FastAPI()
# Initialize with CPU for now to be safe, or env var
service = TTSService(device="cpu")

class TTSRequest(BaseModel):
    text: str
    language: str = "en"
    speaker_wav: str = None

@app.post("/synthesize")
async def synthesize(req: TTSRequest):
    output_path = f"/tmp/{hash(req.text)}.wav"
    service.synthesize(req.text, output_path, req.speaker_wav, req.language)
    # In real app, upload to storage or return stream
    return {"path": output_path}

