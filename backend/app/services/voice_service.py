import whisper
import os
import sys
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class VoiceService:
    _model = None

    @staticmethod
    def _get_bundle_path():
        """Get the absolute path to the resource, works for dev and for PyInstaller OneDir."""
        if getattr(sys, 'frozen', False):
            # In OneDir mode, resources are usually next to the executable
            return os.path.dirname(sys.executable)
        # Running in a normal Python environment
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    @classmethod
    def get_model(cls):
        if cls._model is None:
            logger.info("Loading Whisper model 'tiny'...")
            try:
                # 1. Handle Model Path
                bundle_path = cls._get_bundle_path()
                
                # In dev: let it download to default cache or customized path
                # In prod: look in bundled temporary directory
                download_root = None
                if getattr(sys, 'frozen', False):
                    download_root = os.path.join(bundle_path, 'whisper_models')
                    logger.info(f"Frozen mode detected. Loading model from {download_root}")
                
                # 2. Handle FFmpeg Path
                # If frozen, add the app's bin directory to PATH so subprocess can find ffmpeg
                if getattr(sys, 'frozen', False):
                    os.environ["PATH"] += os.pathsep + bundle_path
                    logger.info(f"Added {bundle_path} to PATH for FFmpeg")

                # Load model
                cls._model = whisper.load_model("tiny", download_root=download_root)
                logger.info("Whisper model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise e
        return cls._model

    @classmethod
    def transcribe(cls, audio_path: str) -> str:
        """
        Transcribe audio file to text using local Whisper model.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            model = cls.get_model()
            # Initial prompt can help with context or language detection
            # 强制指定中文 'zh'
            result = model.transcribe(audio_path, fp16=False, language='zh') # fp16=False for wider compatibility
            text = result.get("text", "").strip()
            logger.info(f"Transcription result: {text}")
            return text
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise e

voice_service = VoiceService()