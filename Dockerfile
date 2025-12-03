# 1. 基礎映像檔
FROM mcr.microsoft.com/playwright/python:v1.55.0-noble

# 2. 設定在容器內的工作目錄
WORKDIR /app

# 設定時區為台北 (確保 Log 時間與問候語正確)
RUN apt-get update && apt-get install -y tzdata && \
    ln -fs /usr/share/zoneinfo/Asia/Taipei /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    rm -rf /var/lib/apt/lists/*

# 3. 複製並安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 複製所有應用程式碼 (會被 .dockerignore 過濾)
COPY . .

# 5. 預設執行命令
#    -u 參數是為了讓 print() 的日誌能即時顯示在 docker logs 中
CMD ["python", "-u", "main.py"]