from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.voice_service import voice_service
import shutil
import os
import uuid

router = APIRouter()


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    # 保存临时文件 (.webm 或 .wav)
    temp_filename = f"temp_{uuid.uuid4()}.webm"
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 调用识别
        text = voice_service.transcribe(temp_filename)
        return {"text": text}

    except Exception as e:
        print(f"识别失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 清理临时文件
        if os.path.exists(temp_filename):
            os.remove(temp_filename)