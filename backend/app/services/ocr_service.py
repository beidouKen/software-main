import base64
import httpx
from app.config import settings

class OCRService:
    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.base_url = settings.DASHSCOPE_BASE_URL

    async def extract_text(self, image_file) -> str:
        if not self.api_key:
            print("Error: DASHSCOPE_API_KEY is missing.")
            return "配置错误：未设置 DASHSCOPE_API_KEY。"

        try:
            print(f"Processing image with Qwen-VL: {image_file.filename}")
            
            # Reset file cursor and read content
            image_file.file.seek(0)
            content = image_file.file.read()
            
            # Encode to base64
            # Determine mime type based on filename extension roughly, or just use image/jpeg as generic for base64 header often works, 
            # but better to be slightly specific.
            filename = image_file.filename.lower()
            mime_type = "image/jpeg"
            if filename.endswith(".png"):
                mime_type = "image/png"
            elif filename.endswith(".webp"):
                mime_type = "image/webp"
                
            base64_image = base64.b64encode(content).decode('utf-8')
            data_url = f"data:{mime_type};base64,{base64_image}"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Using qwen-vl-max for best OCR performance
            payload = {
                "model": "qwen-vl-max",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "请提取这张图片中的所有文字，不要包含任何描述性语言，只返回提取的文字内容。如果包含数学公式，请使用LaTeX格式。"},
                            {"type": "image_url", "image_url": {"url": data_url}}
                        ]
                    }
                ]
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                
                if response.status_code != 200:
                    print(f"DashScope API Error: {response.status_code} - {response.text}")
                    return f"OCR服务请求失败: {response.status_code}"
                
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    print(f"Unexpected API response: {result}")
                    return "未能识别出文字。"
                
        except Exception as e:
            print(f"OCR Service Error: {e}")
            return f"OCR处理出错: {str(e)}"

ocr_service = OCRService()
