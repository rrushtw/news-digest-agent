# src/processors/gemini.py
import logging
import os
import time

from google import genai
from google.genai import types


class GeminiProcessor:
    def __init__(self):
        # 讀取 API Key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # fail-fast：缺少金鑰直接拋例外，避免留下半初始化物件
            raise RuntimeError("GEMINI_API_KEY not found in .env")

        self.client = genai.Client(api_key=api_key)

        # 初始化模型
        self.model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-3.5-flash")
        logging.info(f"Selected Model: {self.model_name}")
        self.tools = [types.Tool(google_search=types.GoogleSearch())]

    def process(self, content: str, title: str, prompt_template: str) -> str:
        """
        直接把抓好的內文文字交給 Gemini 整理（不使用 grounding，配額較寬鬆）。
        這是主要路徑；失敗時由呼叫端 fallback 到 process_url。
        """
        full_prompt = f"""文章標題：{title}

文章內容：
{content}

{prompt_template}"""

        logging.info(f"Processing article content with Gemini: {title}")
        max_attempts = 2  # 原始 + 1 次重試（免費層每日額度有限，不宜多retry）
        for attempt in range(max_attempts):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                )

                if not response.text:
                    logging.warning("Gemini returned empty response.")
                    return None

                return response.text.replace("```html", "").replace("```", "").strip()

            except Exception as e:
                msg = str(e)
                code = getattr(e, "code", None)
                # 只對暫時性伺服器過載 (5xx) 退避重試；
                # 配額類 429 / RESOURCE_EXHAUSTED 重試無益又會吃掉每日額度，直接放手讓呼叫端 fallback。
                transient = code in (500, 503, 504) or (
                    code is None
                    and ("503" in msg or "UNAVAILABLE" in msg)
                    and "RESOURCE_EXHAUSTED" not in msg
                )
                if transient and attempt < max_attempts - 1:
                    wait = 5 * (attempt + 1)
                    logging.warning(
                        f"Gemini transient error, retry in {wait}s "
                        f"({attempt + 1}/{max_attempts - 1}): {msg[:80]}"
                    )
                    time.sleep(wait)
                    continue
                logging.error(f"Gemini process failed: {e}")
                return None

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
