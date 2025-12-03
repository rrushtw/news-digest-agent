import logging

import requests
import urllib3  # 用來處理 SSL 警告
from bs4 import BeautifulSoup

from .base import BaseScraper

# 關閉 "InsecureRequestWarning" 警告，避免 Log 被洗版
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CteeScraper(BaseScraper):
    def fetch_new_articles(self, known_urls=None):
        """
        抓取所有不在 known_urls 中的新文章
        """
        if known_urls is None:
            known_urls = set()

        url = self.config.get("source_url")
        selectors = self.config.get("scraper_config", {})

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            # 1. 抓取列表頁
            logging.info(f"Fetching list from: {url}")

            # 加入 verify=False 解決公司網路 SSL 攔截問題
            resp = requests.get(url, headers=headers, verify=False)

            if resp.status_code != 200:
                logging.error(f"Failed to fetch list. Status: {resp.status_code}")
                return []

            soup = BeautifulSoup(resp.text, "lxml")
            target_sel = selectors.get("target_selector", "h3.news-title a")

            # [關鍵修改] 改用 select 抓取多個連結 (預設抓前 10 篇來檢查)
            link_tags = soup.select(target_sel)[:10]

            if not link_tags:
                logging.warning(f"No article links found with selector: {target_sel}")
                return []

            new_articles_queue = []

            # [策略] 抓取所有「沒看過」的文章。
            for tag in link_tags:
                article_url = tag["href"]
                if not article_url.startswith("http"):
                    article_url = "https://www.ctee.com.tw" + article_url

                title = tag.get_text().strip()

                # 如果這篇文章已經在歷史紀錄中，代表後面的都是舊聞了，直接停止掃描
                if article_url in known_urls:
                    logging.info(f"Found known article, stopping scan: {title}")
                    break

                # 加入待抓取清單
                new_articles_queue.append({"url": article_url, "title": title})

            # 如果沒有新文章
            if not new_articles_queue:
                logging.info("No new articles found.")
                return []

            logging.info(
                f"Found {len(new_articles_queue)} new articles. Fetching content..."
            )

            # 2. 批次抓取內文
            results = []
            # 注意：列表通常是 新->舊，為了閱讀順序，我們可以反轉 (舊->新) 或是保持原樣
            # 這裡保持 新->舊 的順序處理，讓長輩先看到最新的
            for item in new_articles_queue:
                article_data = self._fetch_single_article(
                    item["url"], item["title"], headers, selectors
                )
                if article_data:
                    results.append(article_data)

            return results

        except Exception as e:
            logging.error(f"Error in CteeScraper: {e}")
            return []

    def _fetch_single_article(self, url, title, headers, selectors):
        """
        [輔助函式] 抓取單篇文章內容
        """
        try:
            logging.info(f"Fetching content: {title}")
            resp = requests.get(url, headers=headers, verify=False)
            soup = BeautifulSoup(resp.text, "lxml")

            content_sel = selectors.get("content_selector", "article")

            # 優先找 article，找不到則找 content__body
            content_div = soup.select_one(content_sel)
            if not content_div:
                content_div = soup.select_one(".content__body")

            if not content_div:
                logging.warning(f"Skipping {title}: No content found.")
                return None

            # --- 3. 圖片處理 (在 content__body 範圍內搜尋) ---
            images = []

            # 擴大搜尋範圍：圖片可能在 article 外但在 body 內
            body_scope = soup.select_one(".content__body") or content_div
            img_sel = selectors.get("image_selector", "figure.picture--article")

            for fig in body_scope.select(img_sel):
                a_tag = fig.select_one("a")
                img_tag = fig.select_one("img")
                caption_tag = fig.select_one("figcaption")

                img_url = ""
                # 優先抓取超連結 (通常是 Lightbox 大圖)
                if a_tag and "href" in a_tag.attrs:
                    img_url = a_tag["href"]
                elif img_tag and "src" in img_tag.attrs:
                    img_url = img_tag["src"]

                caption = caption_tag.get_text().strip() if caption_tag else ""

                if img_url and not img_url.endswith(".svg"):
                    images.append({"url": img_url, "caption": caption})

            # 清理雜訊
            ignore_list = selectors.get("ignore_selectors", [])
            for ignore in ignore_list:
                for tag in content_div.select(ignore):
                    tag.decompose()

            text_content = content_div.get_text(separator="\n")

            return {
                "title": title,
                "content": text_content,
                "url": url,
                "images": images,
            }

        except Exception as e:
            logging.error(f"Failed to fetch article {title}: {e}")
            return None
