from abc import ABC, abstractmethod


class BaseScraper(ABC):
    def __init__(self, config: dict):
        self.config = config
        self.base_url = "https://www.ctee.com.tw"  # 預設，子類別可覆蓋

    @abstractmethod
    def fetch_new_articles(self, known_urls=None):
        """
        必須實作：
        傳入已知的 URL 集合 (known_urls)，回傳新文章列表
        """
        pass
