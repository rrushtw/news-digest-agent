# 📰 News Digest Agent

> **An AI-powered, elder-friendly news aggregator designed to declutter the noise.**
>
> 一個基於 AI 的自動化新聞摘要代理人，專為長輩設計的無廣告、大字體、重點式閱讀體驗。

## 📖 專案緣起 (Motivation)

這個專案的靈感來自於家中的長輩。他們喜歡閱讀財經新聞（如工商時報台股逐洞賽），但往往面臨以下痛點：
1.  **廣告遮蔽**：網頁充滿蓋版廣告與彈跳視窗，閱讀體驗極差。
2.  **字體過小**：手機版面擁擠，對老花眼不友善。
3.  **資訊過載**：專有名詞堆砌，缺乏白話文重點整理。

**News Digest Agent** 的目標很簡單：**「去蕪存菁，傳遞溫暖」**。透過自動化爬蟲與 Google Gemini AI，將每日新聞轉換為一封排版精美、語氣溫暖、字體清晰的 Email，讓長輩能輕鬆掌握市場脈動。

## ✨ 核心功能 (Features)

* **🛡️ 自動去廣告 (Clean Read)**：透過 Python 爬蟲精準提取內文與圖表，移除所有廣告與干擾元素。
* **🤖 AI 智慧摘要 (AI Powered)**：串接 **Google Gemini 3.5 Flash**，將艱澀的財經新聞改寫為長輩易讀的白話文，並自動抓取重點個股。
* **📧 批次通知 (Batch Notification)**：自動彙整多篇新文章為一封 Email，避免長輩信箱被大量信件轟炸。
* **🔄 智慧防重 (Deduplication)**：內建歷史紀錄機制 (`history.txt`)，確保不會重複寄送相同的文章。
* **📊 圖文並茂**：保留原文關鍵的 K 線圖與表格，並針對手機閱讀進行 RWD 優化。
* **🐳 Docker Ready**：基於 Playwright 映像檔構建，部署容易，保留未來擴充動態爬蟲的彈性。

## 🛠️ 技術堆疊 (Tech Stack)

* **Language**: Python 3.12+
* **AI Model**: Google Gemini (Default: `gemini-3.5-flash`)
* **Scraping**: `Requests` + `BeautifulSoup4` (Base on `mcr.microsoft.com/playwright` image)
* **Notification**: SMTP (Gmail)
* **Deployment**: Docker & Docker Compose

## 🚀 快速開始 (Quick Start)

### 1. 前置準備
請確保您擁有以下金鑰：
* **Google AI Studio API Key**: [取得連結](https://aistudio.google.com/app/apikey)
* **Gmail App Password**: [取得連結](https://myaccount.google.com/apppasswords) (需開啟兩步驟驗證)

### 2. 下載專案
```bash
git clone https://github.com/rrushtw/news-digest-agent.git
cd news-digest-agent
```

### 3. 設定環境變數
請複製範本 `.env.example` 為 `.env`，並填入您的資訊：

```bash
cp .env.example .env
```

```env
# Google Gemini API Key
GEMINI_API_KEY=AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxx

# (可選) 指定 Gemini 模型，省略時預設 gemini-3.5-flash
GEMINI_MODEL_NAME=gemini-3.5-flash

# Gmail 設定 (寄件者)
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# 收件者清單 (逗號分隔)
TARGET_EMAIL=grandpa@example.com, grandma@example.com, me@example.com
```

### 4. 使用 Docker 啟動 (推薦)
這是最簡單的運行方式，環境已完全隔離。

```bash
# 建置並啟動
docker compose up --build
```

若要在背景執行並設定為排程任務（例如配合 Linux Crontab），可以設定 crontab 每天執行一次：
```bash
# 範例：每天早上 8:00 執行
0 8 * * * cd /path/to/news-digest-agent && /usr/bin/docker compose up >> cron.log 2>&1
```

### 5. 本地開發 (Local Development)
若您使用 VS Code，建議直接使用 **Dev Container** 開啟專案，環境會自動設定完成。
或者手動安裝：
```bash
pip install -r requirements.txt
python main.py
```

## 📂 專案結構 (Project Structure)

本專案採用模組化設計 (Strategy Pattern)，方便未來擴充其他新聞來源。

```text
news-digest-agent/
├── configs/                 # 設定檔 (定義來源與 AI Prompt)
│   └── finance.yaml         # 範例：工商時報設定
├── src/
│   ├── scrapers/            # 爬蟲邏輯 (可擴充)
│   │   ├── base.py          # 基礎類別
│   │   └── ctee.py          # 工商時報實作
│   ├── processors/          # AI 處理邏輯
│   │   └── gemini.py
│   └── notifiers/           # 通知發送邏輯
│       └── email_sender.py
├── Dockerfile               # 建置檔
├── docker-compose.yml       # 部署檔
├── history.txt              # (自動生成) 已發送文章紀錄
├── main.py                  # 程式入口
└── requirements.txt
```

## ⚙️ 客製化 (Configuration)

若要新增或修改新聞來源，請編輯 `configs/` 資料夾下的 YAML 檔案。
例如 `configs/finance.yaml`：

```yaml
name: "工商時報-台股逐洞賽"
source_url: "https://www.ctee.com.tw/stock/matchplay"
type: "finance"

# 定義爬蟲選擇器 (CSS Selectors)
scraper_config:
  target_selector: "h3.news-title a"
  content_selector: "article"
  # ...

# 定義 AI 的角色與指令 (Prompt)
ai_prompt: |
  你是一位貼心的晚輩，請幫我將這篇財經文章整理成給長輩看的 Email...
  (此處可自訂語氣與摘要重點)
```

## 🤝 貢獻 (Contributing)

歡迎提交 Pull Request！如果您有更好的 Prompt 建議，或是實作了新的新聞來源 Scraper（例如鉅亨網、經濟日報），請不吝分享。

## 📄 License

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.