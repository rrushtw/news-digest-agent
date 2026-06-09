import logging

from bs4 import BeautifulSoup

from .base import BaseScraper


class CteeScraper(BaseScraper):
    def fetch_new_articles(self, known_urls=None):
        if known_urls is None:
            known_urls = set()

        url = self.config.get("source_url")
        selectors = self.config.get("scraper_config", {})

        # --- 抓取列表頁（樸素 requests，無需瀏覽器；原始 HTML 已含文章連結）---
        logging.info(f"Fetching list from: {url}")
        html = self._http_get(url)
        if not html:
            logging.error(f"Failed to fetch list page: {url}")
            return []

        soup = BeautifulSoup(html, "lxml")
        target_sel = selectors.get("target_selector", "h3.news-title a")
        link_tags = soup.select(target_sel)[:20]  # 只看前 20 篇

        if not link_tags:
            logging.warning(f"No article links found with selector: {target_sel}")
            return []

        results = []
        for tag in link_tags:
            article_url = tag.get("href", "")
            if not article_url:
                continue
            if not article_url.startswith("http"):
                article_url = self.base_url + article_url

            title = tag.get_text().strip()

            # 如果標題包含「戰績」，直接略過
            if "戰績" in title:
                logging.info(f"🚫 Ignoring performance report (image only): {title}")
                continue

            # 逐篇比對：略過已寄送過的文章；不假設列表為嚴格反時序排列，
            # 即使有置頂或亂序文章也不會漏抓後面的新文。
            if article_url in known_urls:
                logging.info(f"Skipping known article: {title}")
                continue

            results.append({"url": article_url, "title": title})

        return results
