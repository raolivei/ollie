import os
from typing import BinaryIO, Union
from faster_whisper import WhisperModel

class WhisperService:
    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8"):
        """
        Initialize the Whisper service.
        
        Args:
            model_size: Size of the model (tiny, base, small, medium, large-v2)
            device: Device to run on (cpu, cuda)
            compute_type: Quantization type (int8, float16, float32)
        """
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_source: Union[str, BinaryIO], language: str = None):
        """
        Transcribe audio from a file path or file-like object.
        
        Args:
            audio_source: Path to audio file or file-like object
            language: Language code (e.g., "en", "pt") or None for auto-detect
            
        Returns:
            Generator yielding segments
        """
        segments, info = self.model.transcribe(
            audio_source, 
            beam_size=5, 
            language=language,
            vad_filter=True
        )
        
        return segments, info

if __name__ == "__main__":
    # Simple test
    service = WhisperService()
    print("Whisper service initialized.")

