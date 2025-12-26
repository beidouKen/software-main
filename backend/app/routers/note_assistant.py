from fastapi import APIRouter, UploadFile, File
from app.services.audio_service import audio_service
from app.services.llm_service import llm_service

router = APIRouter()

@router.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    # 1. Transcribe
    transcript = audio_service.transcribe(file)
    
    # 2. Summarize
    notes = await llm_service.summarize_notes(transcript)
    
    return {"transcript": transcript, "structured_notes": notes}
