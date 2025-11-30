import os
import torch
from TTS.api import TTS

class TTSService:
    def __init__(self, model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2", device: str = "cpu"):
        """
        Initialize the TTS service.
        
        Args:
            model_name: Name of the Coqui TTS model
            device: Device to run on (cpu, cuda)
        """
        self.device = device if torch.cuda.is_available() and device == "cuda" else "cpu"
        self.tts = TTS(model_name).to(self.device)

    def synthesize(self, text: str, output_path: str, speaker_wav: str = None, language: str = "en"):
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            speaker_wav: Path to reference audio for cloning (optional)
            language: Language code
        """
        if speaker_wav and os.path.exists(speaker_wav):
            self.tts.tts_to_file(
                text=text, 
                file_path=output_path, 
                speaker_wav=speaker_wav, 
                language=language
            )
        else:
            # Fallback or default generation if no clone source
            self.tts.tts_to_file(
                text=text, 
                file_path=output_path,
                language=language
            )
        
        return output_path

    def list_speakers(self):
        """List available speakers if model supports it."""
        if hasattr(self.tts.tts, "speaker_manager") and self.tts.tts.speaker_manager:
            return self.tts.tts.speaker_manager.speaker_names
        return []

