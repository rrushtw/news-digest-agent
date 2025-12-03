import logging
import random
import time

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from .base import BaseScraper


class CteeScraper(BaseScraper):
    def fetch_new_articles(self, known_urls=None):
        if known_urls is None:
            known_urls = set()

        url = self.config.get("source_url")
        selectors = self.config.get("scraper_config", {})

        # 使用 Playwright 啟動瀏覽器
        with sync_playwright() as p:
            # 啟動 Chromium (headless=True 代表不顯示視窗，適合在 Docker/Server 跑)
            # browser = p.chromium.launch(headless=True)
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",  # 關鍵：隱藏自動化標記
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            )

            # 設定 Context (偽裝成一般瀏覽器)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                ignore_https_errors=True,
            )

            # 注入 JavaScript，徹底移除 webdriver 屬性
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            page = context.new_page()

            try:
                # --- 1. 抓取列表頁 ---
                logging.info(f"Fetching list from: {url} (using Playwright)")

                # 前往頁面，等待網路閒置 (確保載入完成)
                response = page.goto(url, wait_until="domcontentloaded", timeout=15000)

                if response.status != 200:
                    logging.error(f"Failed to fetch list. Status: {response.status}")
                    return []

                # 隨機延遲一下，模擬真人
                time.sleep(random.uniform(1, 3))

                # 取得渲染後的 HTML 給 BeautifulSoup 解析
                html = page.content()
                soup = BeautifulSoup(html, "lxml")

                target_sel = selectors.get("target_selector", "h3.news-title a")
                link_tags = soup.select(target_sel)[:20]  # 只看前 20 篇

                if not link_tags:
                    logging.warning(
                        f"No article links found with selector: {target_sel}"
                    )
                    # 截圖除錯 (若失敗，這張圖會幫助很大)
                    # page.screenshot(path="debug_list_failed.png")
                    return []

                results = []

                for tag in link_tags:
                    article_url = tag["href"]
                    if not article_url.startswith("http"):
                        article_url = "https://www.ctee.com.tw" + article_url

                    title = tag.get_text().strip()

                    # 如果標題包含「戰績」，直接略過
                    if "戰績" in title:
                        logging.info(
                            f"🚫 Ignoring performance report (image only): {title}"
                        )
                        continue

                    if article_url in known_urls:
                        logging.info(f"Found known article, stopping scan: {title}")
                        break

                    results.append({"url": article_url, "title": title})

                return results

            except Exception as e:
                logging.error(f"Error in CteeScraper (Playwright): {e}")
                return []
            finally:
                browser.close()
