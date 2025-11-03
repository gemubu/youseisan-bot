# 1. Pythonベースイメージ
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    && rm -rf /var/lib/apt/lists/*

# 2. 作業ディレクトリを作成
WORKDIR /app

# 3. 依存パッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. ソースコードをコピー
COPY . .

ENV GOOGLE_APPLICATION_CREDENTIALS="/app/key.json"

# 5. コンテナ起動時に Bot を実行
CMD ["python", "main.py"]