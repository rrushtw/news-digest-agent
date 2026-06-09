# main.py
import logging
import os
import time
from typing import Set

import yaml
from dotenv import load_dotenv

from src.notifiers.email_sender import EmailNotifier
from src.processors.gemini import GeminiProcessor
from src.scrapers.ctee import CteeScraper

# 設定 Log 格式
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# 載入 .env 環境變數
load_dotenv()

# 歷史紀錄檔案的路徑
HISTORY_FILE = "history.txt"


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_scraper(config):
    if "ctee.com.tw" in config.get("source_url", ""):
        return CteeScraper(config)
    return None


def load_history() -> Set[str]:
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def append_history(urls: list[str] | str):
    """
    - 儲存已寄送的紀錄
    - 只保留最近 100 筆，避免檔案無限膨脹
    """
    if not urls:
        return

    sent_urls = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            sent_urls = f.read().splitlines()

    # 加入新 URL
    if isinstance(urls, list):
        sent_urls.extend(urls)
    else:
        sent_urls.append(urls)

    # 寫回檔案 (只留最後 100 筆)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sent_urls[-100:]))


def process_single_config(filename, config_dir, processor, notifier):
    """
    處理單一設定檔的完整流程
    """
    if not (filename.endswith(".yaml") or filename.endswith(".yml")):
        return

    logging.info(f"Processing config: {filename}")
    config_path = os.path.join(config_dir, filename)
    config = load_config(config_path)

    # 1. Scrape
    scraper = get_scraper(config)
    if not scraper:
        logging.warning(f"No scraper found for {config.get('name')}")
        return

    history_set = load_history()

    # 抓取多篇新文章
    new_articles = scraper.fetch_new_articles(known_urls=history_set)

    if not new_articles:
        logging.info(f"[{config.get('name')}] No new articles found.")
        return

    logging.info(
        f"[{config.get('name')}] Found {len(new_articles)} new articles. Processing..."
    )

    # 用來收集所有文章的 HTML 片段
    email_body_parts = []
    success_urls = []

    for i, article in enumerate(new_articles):
        # 除了第一篇，之後的每一篇都要先休息一下，避免觸發 API Rate Limit (429)
        if i > 0:
            logging.info(
                "⏳ Sleeping for 15 seconds to respect Gemini API rate limits..."
            )
            time.sleep(15)

        logging.info(f"Processing Article with AI: {article['title']}")

        prompt = config.get("ai_prompt")
        # friendly_html = processor.process(article["content"], prompt)
        friendly_html = processor.process_url(article["url"], article["title"], prompt)

        if not friendly_html:
            logging.warning(f"Skipping {article['title']} due to AI error.")
            continue

        # 為每一篇文章加上標題區塊，方便區隔
        article_block = f"""
        <div style="border: 1px solid #ccc; padding: 20px; margin-bottom: 30px; border-radius: 10px; background-color: #fff;">
            <h2 style="color: #d32f2f; border-bottom: 2px solid #d32f2f; padding-bottom: 10px;">📰 {article["title"]}</h2>
            {friendly_html}
            <p style="text-align: right;"><a href="{article["url"]}" style="color: #007bff;">閱讀原文</a></p>
        </div>
        """
        email_body_parts.append(article_block)
        success_urls.append(article["url"])

    # 整合寄送邏輯
    if len(email_body_parts) == 0:
        logging.warning("No valid content generated after processing.")
        return

    # 組合所有文章內容
    combined_html = "".join(email_body_parts)

    # 加上 Email 整體外框 (例如加上日期標題)
    full_email_content = f"""
    <html>
    <body style="font-family: sans-serif; background-color: #f4f4f4; padding: 20px;">
        <h1 style="text-align: center; color: #333;">【{config["name"]}】最新快訊彙整</h1>
        <p style="text-align: center; color: #666;">共整理了 {len(email_body_parts)} 篇新文章</p>
        {combined_html}
        <div style="text-align: center; margin-top: 40px; color: #888; font-size: 12px;">
            <p>本郵件由 AI 自動整理發送，僅供參考。</p>
            <p>祝您 操作順利 身體健康</p>
        </div>
    </body>
    </html>
    """

    subject = f"【{config['name']}】今日重點快訊 ({len(email_body_parts)} 篇)"

    # 只有「真正寄送成功」才寫入歷史紀錄；任何失敗都不寫，讓下次執行能重試，
    # 避免寄信失敗卻把文章標記為已寄送、導致新聞永久遺失。
    if notifier.send(subject, full_email_content):
        append_history(success_urls)
        logging.info(
            f"✅ Batch email sent successfully with {len(success_urls)} articles."
        )
    else:
        logging.error(
            f"❌ Email 寄送失敗，{len(success_urls)} 篇文章未寫入 history，下次將重試。"
        )


def main():
    config_dir = "configs"

    # 初始化共用元件
    processor = GeminiProcessor()
    notifier = EmailNotifier()

    # 檢查目錄是否存在
    if not os.path.exists(config_dir):
        logging.error(f"Config directory '{config_dir}' not found.")
        return

    # 掃描並執行
    for filename in os.listdir(config_dir):
        process_single_config(filename, config_dir, processor, notifier)


if __name__ == "__main__":
    main()
