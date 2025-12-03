# src/processors/gemini.py
import logging
import os

import google.generativeai as genai  # [修改] 換成這個套件


class GeminiProcessor:
    def __init__(self):
        # 讀取 API Key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logging.error("GEMINI_API_KEY not found in .env")
            return

        # 設定 API Key
        genai.configure(api_key=api_key)

        # 初始化模型
        self.model_name = os.getenv("GEMINI_MODEL_NAME")
        logging.info(f"Selected Model: {self.model_name}")
        self.model = genai.GenerativeModel(self.model_name)

    def process(self, content: str, prompt_template: str) -> str:
        """
        將文章內容丟給 Gemini 進行摘要與改寫
        """
        if not content:
            return None

        # 組合 Prompt
        full_prompt = f"{prompt_template}\n\n【原始文章內容】：\n{content[:15000]}"  # 截斷以防超長

        try:
            logging.info(f"Sending request to Google AI Studio ({self.model_name})...")
            response = self.model.generate_content(full_prompt)

            if not response.parts:
                logging.warning(
                    f"Gemini returned empty response. Finish Reason: {response.prompt_feedback}"
                )
                return "（AI 無法生成摘要，可能因內容觸發安全過濾機制）"

            clean_html = response.text.replace("```html", "").replace("```", "").strip()
            return clean_html

        except Exception as e:
            logging.error(f"Gemini API processing failed: {e}")
            return None
