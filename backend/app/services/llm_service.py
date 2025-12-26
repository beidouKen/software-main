import json
import httpx
from app.config import settings

class LLMService:
    def __init__(self):
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.api_key = settings.DEEPSEEK_API_KEY

    async def _call_deepseek(self, messages: list, response_format: str = "text") -> dict:
        if not self.api_key:
            raise ValueError("DeepSeek API Key is missing. Please set DEEPSEEK_API_KEY in .env")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "stream": False
        }
        
        if response_format == "json_object":
             payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    async def summarize_notes(self, text: str) -> dict:
        prompt = f"""
        请总结以下课堂内容。
        返回一个纯 JSON 对象，不要包含 Markdown 格式。
        JSON 必须包含以下字段:
        - "title": 笔记标题
        - "key_points": 关键点列表 (字符串数组)
        - "examples": 提到的例子列表 (字符串数组)
        
        内容: {text}
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的AI助教。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response_data = await self._call_deepseek(messages, response_format="json_object")
            content = response_data["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as e:
            print(f"Error calling DeepSeek: {e}")
            # Fallback or re-raise
            return {
                "title": "Error Generating Notes",
                "key_points": ["Error: " + str(e)],
                "examples": []
            }

    async def analyze_question(self, question_text: str) -> dict:
        prompt = f"""
        分析以下题目。
        注意：题目文本是通过OCR（光学字符识别）从图片中提取的，可能存在识别错误或格式丢失。
        如果题目中似乎包含图表、几何图形或函数图像的描述但缺失了具体数据，请在"explanation"中指出这一点，并尝试根据现有文本进行最合理的推断或给出解题思路。
        
        返回 JSON 对象，包含字段: topic, difficulty, explanation, similar_question。
        题目: {question_text}
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的数学老师。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response_data = await self._call_deepseek(messages, response_format="json_object")
            content = response_data["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as e:
             print(f"Error calling DeepSeek: {e}")
             return {
                "topic": "Error",
                "difficulty": "Unknown",
                "explanation": str(e),
                "similar_question": ""
            }

    async def generate_parent_report(self, student_data: dict) -> str:
        prompt = f"""
        根据以下学生数据生成一份给家长的简明学习报告：
        {json.dumps(student_data, ensure_ascii=False)}
        """
        
        messages = [
            {"role": "system", "content": "你是一个贴心的班主任。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response_data = await self._call_deepseek(messages)
            return response_data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error generating report: {e}"

llm_service = LLMService()
