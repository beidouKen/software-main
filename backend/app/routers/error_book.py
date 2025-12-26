from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from pydantic import BaseModel
from app.services.ocr_service import ocr_service
from app.services.llm_service import llm_service

router = APIRouter()

class AnalyzeRequest(BaseModel):
    text: str

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
