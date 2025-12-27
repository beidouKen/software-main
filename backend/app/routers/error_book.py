from fastapi import APIRouter, UploadFile, File, HTTPException, Body, Depends, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import json
import shutil
from datetime import datetime
from app.services.ocr_service import ocr_service
from app.services.llm_service import llm_service
from app import models, schemas
from app.dependencies import get_db, get_current_user

router = APIRouter()

class AnalyzeRequest(BaseModel):
    text: str

@router.get("/knowledge-tags")
def get_knowledge_tags():
    """Get knowledge tags from cache"""
    cache_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data_cache", "knowledge_tags.json")
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@router.post("/mistakes")
async def create_mistake(
    subject: str = Form(...),
    chapter: str = Form(...),
    knowledge_point: str = Form(...), # Expecting JSON string of list or comma separated
    content: str = Form(...),
    note: str = Form(...),
    date: str = Form(...),
    graph_1: UploadFile = File(...),
    graph_2: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user_data: dict = Depends(get_current_user)
):
    user = current_user_data["user"]
    if current_user_data["user_type"] != "student":
        raise HTTPException(status_code=403, detail="Only students can create mistakes")

    # Save images
    upload_dir = "uploads/mistakes"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filenames
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    graph_1_path = f"{upload_dir}/{user.student_id}_{timestamp}_1_{graph_1.filename}"
    with open(graph_1_path, "wb") as buffer:
        shutil.copyfileobj(graph_1.file, buffer)
        
    graph_2_path = None
    if graph_2:
        graph_2_path = f"{upload_dir}/{user.student_id}_{timestamp}_2_{graph_2.filename}"
        with open(graph_2_path, "wb") as buffer:
            shutil.copyfileobj(graph_2.file, buffer)

    # Parse date
    try:
        mistake_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
    except ValueError:
        mistake_date = datetime.now()

    # Create DB entry
    # Note: ID is auto-incremented by database
    mistake = models.LearningMistake(
        student_id=user.student_id,
        date=mistake_date,
        subject=subject,
        chapter=chapter,
        knowledge_point=knowledge_point,
        content=content,
        note=note,
        graph_1=graph_1_path,
        graph_2=graph_2_path
    )
    
    db.add(mistake)
    db.commit()
    db.refresh(mistake)
    
    return {"message": "Mistake created successfully", "id": mistake.id}

@router.post("/ocr")
async def ocr_problem(file: UploadFile = File(...)):
    print(f"Received OCR request: {file.filename}")
    try:
        # 1. OCR
        problem_text = await ocr_service.extract_text(file)
        print(f"OCR Result: {problem_text[:50]}...")
        return {"text": problem_text}
    except Exception as e:
        print(f"Error in ocr_problem: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_problem(request: AnalyzeRequest):
    print(f"Received analysis request")
    try:
        # 2. Analyze
        analysis = await llm_service.analyze_question(request.text)
        return {"analysis": analysis}
    except Exception as e:
        print(f"Error in analyze_problem: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Deprecated: Kept for reference or legacy support if needed, but new flow uses /ocr and /analyze
# @router.post("/upload-problem")
# async def upload_problem(file: UploadFile = File(...)):
#     ...
