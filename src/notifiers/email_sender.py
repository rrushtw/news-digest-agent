# src/notifiers/email_sender.py
import logging
import os
import smtplib
from email.header import Header
from email.mime.text import MIMEText


class EmailNotifier:
    def __init__(self):
        self.gmail_user = os.getenv("GMAIL_USER")
        self.gmail_password = os.getenv("GMAIL_APP_PASSWORD")

        # 讀取環境變數
        raw_targets = os.getenv("TARGET_EMAIL", "")

        # 1. 使用 Set Comprehension 自動去重 (Deduplication)
        #    如果 .env 裡寫了 "a@test.com, a@test.com"，這裡只會保留一個
        self.target_emails = {e.strip() for e in raw_targets.split(",") if e.strip()}

    def send(self, subject: str, html_content: str):
        if not html_content:
            logging.warning("No content to send.")
            return

        if not self.target_emails:
            logging.error("No target emails configured. Please check .env")
            return

        msg = MIMEText(html_content, "html", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = self.gmail_user

        # BCC 模式：Header 中的收件人寫自己，隱藏真實名單
        msg["To"] = self.gmail_user

        try:
            # 2. 要發送時，將 set 轉回 list (Array)
            recipient_list = list(self.target_emails)

            logging.info(f"Sending email (BCC) to {len(recipient_list)} recipients...")

            # 使用 Gmail SSL Port 465
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
            server.set_debuglevel(1)  # [新增] 這會印出連線過程，讓你知道卡在哪
            server.login(self.gmail_user, self.gmail_password)

            # 3. to_addrs 接受 list 參數
            server.send_message(msg, to_addrs=recipient_list)

            server.quit()
            logging.info("Email sent successfully!")

        except Exception as e:
            logging.error(f"Failed to send email: {e}")
