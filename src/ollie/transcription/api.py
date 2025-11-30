from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from .whisper_service import WhisperService
import shutil
import os

app = FastAPI()
service = WhisperService(model_size="small")

class TranscribeRequest(BaseModel):
    path: str
    language: str = None

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    temp_file = f"/tmp/{file.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        segments, info = service.transcribe(temp_file)
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    # Collect segments
    result = []
    for segment in segments:
        result.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text
        })
        
    return {"segments": result, "language": info.language}

@app.post("/transcribe_path")
async def transcribe_path(req: TranscribeRequest):
    if not os.path.exists(req.path):
        raise HTTPException(status_code=404, detail="File not found")
        
    segments, info = service.transcribe(req.path, language=req.language)
    
    result = []
    for segment in segments:
        result.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text
        })
        
    return {"segments": result, "language": info.language}
