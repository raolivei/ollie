from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from .whisper_service import WhisperService
from .streaming import StreamingTranscriptionService
import shutil
import os

app = FastAPI()
service = WhisperService(model_size="small")
streaming_service = StreamingTranscriptionService(model_size="small")

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

@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """
    WebSocket endpoint for real-time streaming transcription with rolling window.
    Receives audio chunks and sends transcription updates.
    """
    await websocket.accept()
    session_id = None
    
    try:
        # Initialize streaming session - first message should be session ID
        session_id = await websocket.receive_text()
        print(f"WebSocket session started: {session_id}")
        await streaming_service.start_session(session_id, websocket)
        
        # Keep connection alive and process audio chunks
        chunk_count = 0
        while True:
            try:
                # Receive audio chunk (binary data)
                data = await websocket.receive_bytes()
                chunk_count += 1
                
                if chunk_count % 100 == 0:  # Log every 100 chunks
                    print(f"Received {chunk_count} audio chunks for session {session_id}")
                
                # Process audio chunk in rolling window
                await streaming_service.process_audio_chunk(session_id, data)
                
            except WebSocketDisconnect:
                print(f"WebSocket disconnected for session {session_id}")
                break
            except Exception as e:
                print(f"Error processing audio chunk: {e}")
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
                except:
                    break
                
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if session_id:
            try:
                await streaming_service.end_session(session_id)
            except Exception as e:
                print(f"Error ending session: {e}")
        try:
            await websocket.close()
        except:
            pass
