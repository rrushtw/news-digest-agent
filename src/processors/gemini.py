# src/processors/gemini.py
import logging
import os

from google import genai
from google.genai import types


class GeminiProcessor:
    def __init__(self):
        # 讀取 API Key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logging.error("GEMINI_API_KEY not found in .env")
            return

        self.client = genai.Client(api_key=api_key)

        # 初始化模型
        self.model_name = os.getenv("GEMINI_MODEL_NAME")
        logging.info(f"Selected Model: {self.model_name}")
        self.tools = [types.Tool(google_search=types.GoogleSearch())]

    def process_url(self, url: str, title: str, prompt_template: str) -> str:
        """
        直接給 URL 讓 Gemini 去讀
        """
        # 組合 Prompt：明確告訴它去讀這個網址
        full_prompt = f"""
        請利用 Google Search Grounding 功能，閱讀這篇網頁內容：{url}
        
        文章標題：{title}
        
        {prompt_template}
        """

        try:
            logging.info(f"Asking Gemini to read URL: {url}")

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(tools=self.tools),
            )

            # 檢查回應
            if not response.text:
                logging.warning("Gemini returned empty response.")
                return None

            # 清理 Markdown
            clean_html = response.text.replace("```html", "").replace("```", "").strip()
            return clean_html

        except Exception as e:
            logging.error(f"Gemini Grounding failed: {e}")
            return None
