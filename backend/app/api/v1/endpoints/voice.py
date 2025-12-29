from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.voice_service import voice_service
import shutil
import os
import tempfile
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Upload an audio file (wav/mp3/m4a) and get transcribed text.
    """
    tmp_path = None
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        
        logger.info(f"Processing voice file: {tmp_path}")
        
        # Transcribe
        text = voice_service.transcribe(tmp_path)
        
        return {"text": text}

    except Exception as e:
        logger.error(f"Error processing voice upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Cleanup
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)