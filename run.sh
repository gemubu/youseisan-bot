#!/bin/bash

# コンテナ名を定義
CONTAINER_NAME=discordbot

# 既存のコンテナを停止・削除
docker stop $CONTAINER_NAME >/dev/null 2>&1
docker rm $CONTAINER_NAME >/dev/null 2>&1

# イメージを再ビルド
docker build -t discordbot .

# 新しいコンテナを起動
docker run \
  --env-file .env \
  -v $(pwd)/key.json:/app/key.json \
  --name $CONTAINER_NAME \
  discordbot