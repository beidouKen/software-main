import asyncio
import os
import sys
from fastapi import UploadFile

# Add current directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ocr_service import ocr_service

# Mock UploadFile for testing
class MockUploadFile:
    def __init__(self, filename, file_path):
        self.filename = filename
        self.file = open(file_path, 'rb')

async def test_ocr():
    image_path = "test_image.png"
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found.")
        print("Please ensure 'test_image.png' exists in the backend directory.")
        return

    print(f"Testing OCR with {image_path}...")
    print(f"Using API Key: {ocr_service.api_key[:5]}... (masked)" if ocr_service.api_key else "No API Key found!")
    print(f"Using Base URL: {ocr_service.base_url}")
    
    mock_file = MockUploadFile("test_image.png", image_path)
    
    try:
        result = await ocr_service.extract_text(mock_file)
        print("\n--- OCR Result ---")
        print(result)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        mock_file.file.close()

if __name__ == "__main__":
    asyncio.run(test_ocr())
