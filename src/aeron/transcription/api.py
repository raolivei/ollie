from fastapi import FastAPI, UploadFile, File
from .whisper_service import WhisperService
import shutil
import os

app = FastAPI()
service = WhisperService(model_size="small")

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    temp_file = f"/tmp/{file.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    segments, info = service.transcribe(temp_file)
    
    # Collect segments
    result = []
    for segment in segments:
        result.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text
        })
        
    os.remove(temp_file)
    return {"segments": result, "language": info.language}

