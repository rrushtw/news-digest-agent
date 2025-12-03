from abc import ABC, abstractmethod


class BaseScraper(ABC):
    def __init__(self, config: dict):
        self.config = config
        self.base_url = "https://www.ctee.com.tw"  # 預設，子類別可覆蓋

    @abstractmethod
    def fetch_latest(self):
        """
        必須實作：回傳 (title, content, url)
        如果失敗回傳 None
        """
        pass
