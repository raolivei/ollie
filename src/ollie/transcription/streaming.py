"""
Streaming transcription service with rolling window support.
Processes audio chunks in real-time and provides incremental transcriptions.
"""
import asyncio
import io
import numpy as np
from typing import Dict, Optional
from fastapi import WebSocket
from faster_whisper import WhisperModel
import wave
from collections import deque


class StreamingTranscriptionService:
    """
    Handles real-time streaming transcription with a rolling window approach.
    
    Maintains a buffer of recent audio and continuously transcribes it,
    sending incremental updates to the client.
    """
    
    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8",
                 window_size_seconds: float = 5.0, overlap_seconds: float = 1.0, sample_rate: int = 16000):
        """
        Initialize the streaming transcription service.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large-v2)
            device: Device to run on (cpu, cuda)
            compute_type: Quantization type (int8, float16, float32)
            window_size_seconds: Size of the rolling window in seconds
            overlap_seconds: Overlap between windows to avoid cutting words
            sample_rate: Audio sample rate (Whisper expects 16kHz)
        """
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.window_size_samples = int(window_size_seconds * sample_rate)
        self.overlap_samples = int(overlap_seconds * sample_rate)
        self.sample_rate = sample_rate
        self.sessions: Dict[str, 'StreamingSession'] = {}
        
    async def start_session(self, session_id: str, websocket: WebSocket):
        """Start a new streaming transcription session."""
        if session_id in self.sessions:
            await self.end_session(session_id)
            
        self.sessions[session_id] = StreamingSession(
            session_id=session_id,
            websocket=websocket,
            window_size_samples=self.window_size_samples,
            overlap_samples=self.overlap_samples,
            sample_rate=self.sample_rate,
            model=self.model
        )
        await websocket.send_json({
            "type": "session_started",
            "session_id": session_id
        })
        
    async def process_audio_chunk(self, session_id: str, audio_data: bytes):
        """Process an audio chunk for a session."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
            
        session = self.sessions[session_id]
        await session.add_audio_chunk(audio_data)
        
    async def end_session(self, session_id: str):
        """End a streaming transcription session."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            await session.finalize()
            del self.sessions[session_id]


class StreamingSession:
    """Manages a single streaming transcription session."""
    
    def __init__(self, session_id: str, websocket: WebSocket, window_size_samples: int,
                 overlap_samples: int, sample_rate: int, model: WhisperModel):
        self.session_id = session_id
        self.websocket = websocket
        self.window_size_samples = window_size_samples
        self.overlap_samples = overlap_samples
        self.sample_rate = sample_rate
        self.model = model
        
        # Audio buffer (rolling window)
        self.audio_buffer = deque(maxlen=window_size_samples + overlap_samples)
        
        # Track last transcription to avoid duplicates
        self.last_transcription = ""
        self.last_transcription_time = 0.0
        
        # Processing lock
        self.processing = False
        self.processing_task: Optional[asyncio.Task] = None
        
    async def add_audio_chunk(self, audio_data: bytes):
        """Add an audio chunk to the buffer and trigger transcription if needed."""
        try:
            # Convert audio bytes to numpy array
            # Assume PCM 16-bit mono audio
            if len(audio_data) == 0:
                return
                
            audio_samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Add to buffer
            self.audio_buffer.extend(audio_samples)
            
            # If we have enough samples for a window, trigger transcription
            if len(self.audio_buffer) >= self.window_size_samples and not self.processing:
                self.processing = True
                if self.processing_task:
                    self.processing_task.cancel()
                self.processing_task = asyncio.create_task(self._transcribe_window())
        except Exception as e:
            print(f"Error adding audio chunk: {e}")
            import traceback
            traceback.print_exc()
            
    async def _transcribe_window(self):
        """Transcribe the current audio window."""
        try:
            # Get the current window (last window_size_samples)
            window_samples = np.array(list(self.audio_buffer)[-self.window_size_samples:])
            
            # Transcribe using Whisper
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            segments, info = await loop.run_in_executor(
                None,
                self._transcribe_sync,
                window_samples
            )
            
            # Combine segments into text
            transcript = " ".join([seg.text for seg in segments]).strip()
            
            # Only send if it's different from last transcription
            if transcript and transcript != self.last_transcription:
                # Check if WebSocket is still connected
                try:
                    # Check if it's a continuation or new text
                    if self.last_transcription and transcript.startswith(self.last_transcription):
                        # New text is continuation
                        new_text = transcript[len(self.last_transcription):].strip()
                        if new_text:
                            await self.websocket.send_json({
                                "type": "transcription_update",
                                "text": new_text,
                                "full_text": transcript,
                                "is_final": False
                            })
                    else:
                        # Completely new transcription
                        await self.websocket.send_json({
                            "type": "transcription_update",
                            "text": transcript,
                            "full_text": transcript,
                            "is_final": False
                        })
                    
                    self.last_transcription = transcript
                except Exception as e:
                    # WebSocket closed, stop processing
                    print(f"WebSocket closed during transcription: {e}")
                    self.processing = False
                    return
                
        except Exception as e:
            print(f"Transcription error: {e}")
            try:
                if self.websocket.client_state.name != "DISCONNECTED":
                    await self.websocket.send_json({
                        "type": "error",
                        "message": f"Transcription error: {str(e)}"
                    })
            except:
                pass
        finally:
            self.processing = False
            
    def _transcribe_sync(self, audio_samples: np.ndarray):
        """Synchronous transcription (runs in executor)."""
        # Convert to int16 for Whisper
        audio_int16 = (audio_samples * 32768.0).astype(np.int16)
        
        # Create a temporary WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        wav_buffer.seek(0)
        
        # Transcribe
        segments, info = self.model.transcribe(
            wav_buffer,
            beam_size=5,
            vad_filter=True,
            language=None  # Auto-detect
        )
        
        # Convert generator to list
        segments_list = list(segments)
        return segments_list, info
        
    async def finalize(self):
        """Finalize the session and send final transcription."""
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
                
        # Send final transcription if buffer has content
        if len(self.audio_buffer) > 0:
            try:
                # Check if websocket is still open
                if self.websocket.client_state.name != "DISCONNECTED":
                    window_samples = np.array(list(self.audio_buffer))
                    loop = asyncio.get_event_loop()
                    segments, info = await loop.run_in_executor(
                        None,
                        self._transcribe_sync,
                        window_samples
                    )
                    
                    final_transcript = " ".join([seg.text for seg in segments]).strip()
                    
                    if final_transcript:
                        try:
                            await self.websocket.send_json({
                                "type": "transcription_final",
                                "text": final_transcript,
                                "is_final": True
                            })
                        except Exception:
                            # WebSocket already closed, ignore
                            pass
            except Exception as e:
                try:
                    if self.websocket.client_state.name != "DISCONNECTED":
                        await self.websocket.send_json({
                            "type": "error",
                            "message": f"Final transcription error: {str(e)}"
                        })
                except Exception:
                    # WebSocket already closed, ignore
                    pass

