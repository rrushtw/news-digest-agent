import logging
import random
import time
from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup


class BaseScraper(ABC):
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-TW,zh;q=0.9",
    }

    def __init__(self, config: dict):
        self.config = config
        self.base_url = "https://www.ctee.com.tw"  # 預設，子類別可覆蓋

    def _http_get(self, url: str, retries: int = 2) -> str | None:
        """以 requests 抓取 HTML（含 UA、timeout 與小重試）；失敗回 None。"""
        for attempt in range(retries + 1):
            try:
                resp = requests.get(url, headers=self.DEFAULT_HEADERS, timeout=15)
                if resp.status_code == 200:
                    return resp.text
                logging.warning(f"GET {url} -> HTTP {resp.status_code}")
            except Exception as e:
                logging.warning(f"GET {url} failed (attempt {attempt + 1}): {e}")
            time.sleep(random.uniform(1, 2))
        return None

    def fetch_article_content(self, url: str) -> str | None:
        """
        通用內文擷取：抓內頁 → 以 content_selector 取正文 → 移除 ignore_selectors
        的廣告/推薦等雜訊 → 回傳純文字。抓不到正文則回 None（讓呼叫端 fallback）。
        """
        selectors = self.config.get("scraper_config", {})
        html = self._http_get(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "lxml")
        node = soup.select_one(selectors.get("content_selector", "article"))
        if not node:
            logging.warning(f"No content node found for: {url}")
            return None

        # 資料清洗：移除 script/style/廣告/推薦/相關新聞等雜訊
        for ignore_sel in selectors.get("ignore_selectors", []):
            for el in node.select(ignore_sel):
                el.decompose()

        text = node.get_text("\n", strip=True)
        # 收斂多餘空行
        text = "\n".join(ln.strip() for ln in text.splitlines() if ln.strip())
        return text or None

    @abstractmethod
    def fetch_new_articles(self, known_urls=None):
        """
        必須實作：
        傳入已知的 URL 集合 (known_urls)，回傳新文章列表
        """
        pass
