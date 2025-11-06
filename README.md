# ようせいさんDiscord Bot


# 📁 ディレクトリ・ファイル構成

このプロジェクトの基本的な構成と，各ディレクトリの役割を示します。
```
.
├── Dockerfile     # コンテナ構成定義
├── .dockerignore  # docker imageに含まないファイルを定義
├── .gitignore  # gitで管理しないファイルを定義
├── .env  # 環境変数
├── README.md      # このファイル
├── cogs           # Discord Botの機能をモジュールごとにまとめたフォルダ
│   ├── admin.py      # 管理者向けコマンド（Bot管理・サーバー管理関連）
│   ├── birthday.py   # 誕生日通知・登録機能
│   ├── event.py      # on_messageみたいなの書いてるけど無くす予定
│   ├── general.py    # 汎用コマンド（ヘルプや挨拶など基本機能）
│   ├── level.py      # 経験値・レベルシステム関連機能
│   ├── tts.py        # テキスト読み上げ機能（Text-to-Speech）
│   └── twitch.py     # Twitch配信通知機能
├── key.json       # google cloud ttsのapi key
├── main.py        # エントリーポイント。Botの起動・初期化処理を行う
├── requirements.txt   # Python依存パッケージ一覧（インストール用）
└── run.sh         # Botの実行スクリプト（実行コマンドを自動化）
```

# 🌿 Git ブランチ運用ルール

## 📌 概要

このプロジェクトでは，開発を効率的に進めるために，以下のブランチ運用ルールを採用します。

---

## 🌱 ブランチ構成

| ブランチ名 | 用途 | 説明 |
|-------------|------|------|
| `main` | 本番用 | 常にリリース可能な状態を保つ。本番反映専用。直接コミットは禁止。 |
| `develop` | 開発用 | 開発のメインブランチ。ここに各機能ブランチをマージする。 |
| `feature/*` | 機能開発用 | 新機能や修正ごとに作成する一時ブランチ。完了後に `develop` へマージする。 |
| `hotfix/*` | 緊急修正用 | 本番環境で発生したバグを即時修正するブランチ。修正後は `main` と `develop` の両方へマージする。 |

---

## 🔁 開発フロー

1. **開発ブランチ作成**
   ```bash
   # develop ブランチを最新にする
   git checkout develop
   git pull origin develop

   # 新しい機能ブランチを作成する（例: feature/login）
   git checkout -b feature/login
   ```

2. **実装・コミット**

   - 実装を行い，わかりやすく小さなコミットに分ける。
   - コミットメッセージは「[コミットメッセージルール](#コミットメッセージルール)」に従う。

3. **プルリクエスト作成**

   - 作業完了後，GitHub上で `feature/xxx → develop` の Pull Request（PR）を作成する。  
   - 他メンバーによるレビューを経てマージする。

4. **リリース**

   ```bash
   # main ブランチへ切り替え，develop の内容をマージする
   git checkout main
   git pull origin main
   git merge --no-ff develop

   # リリースタグを作成する（例: v1.0.0）
   git tag -a v1.0.0 -m "初回リリース"

   # main とタグをリモートへプッシュする
   git push origin main --tags
   ```

## ✏️ コミットメッセージルール

- 推奨: Conventional Commits 形式を採用（例）
  - feat(scope): 簡潔な説明
  - fix(scope): バグ修正
  - docs: ドキュメント変更
  - chore: ビルド・補助ツール等の変更
- 例: `feat(tts): サーバーごとに読み上げ音声を変更できるように変更`

## 🗂️ ブランチ命名規則

| 種類 | 命名例 | 説明 |
|------|--------|------|
| 機能追加 | `feature/login` | ログイン機能の追加 |
| バグ修正 | `fix/typo-login` | ログイン画面のtypo修正 |
| 緊急修正 | `hotfix/500error` | 本番での500エラー修正 |
| 改善 | `improve/ui-color` | UI配色の改善 |

> **命名ルール**
> - 英語の単語を使用し，簡潔にまとめる  
> - `/` で分類する（例：`feature/`, `fix/`, `hotfix/`）  
> - ハイフン（`-`）で単語を区切る（例：`feature/add-login-api`）

---

## 👥 チームルール

- `main` への直接 push は禁止（保護ブランチ設定を行う）  
- コミットやPRは小さく，1つの機能・修正単位でまとめる  
- コンフリクトは作業者自身で解消してからレビュー依頼を行う  
- Issue番号をPRやコミットメッセージに紐付ける（例：`feat: ログイン画面追加 (#12)`）  
- 不要になったブランチはマージ後に削除する


---
---

## 🔃 プルリクエスト（Pull Request）の流れ


### 1. 作業ブランチを作成する
作業を始める前に，最新の `develop` ブランチから新しいブランチを作成します。

```bash
git checkout develop
git pull origin develop
git checkout -b feature/〇〇
```
---

### 2. 自分の作業ブランチに戻る
途中で別ブランチに移動していた場合は，自分のブランチに戻ります。

```bash
git checkout feature/〇〇
```

### 3. 最新の `develop` を取り込む（他メンバーの変更を反映）
他のメンバーが `develop` に新しい変更をマージしている場合，自分の作業ブランチにも取り込みます。

```bash
git checkout develop
git pull origin develop
git checkout feature/〇〇
git merge develop
```

### 4. 変更をコミット・プッシュする
作業内容をコミットし，リモートの自分のブランチへプッシュします。

```bash
git add .
git commit -m "〇〇機能を追加"
git push origin feature/〇〇
```

### 5. プルリクエストを作成する
GitHub上で「`feature/〇〇` → `develop`」に対してプルリクエスト（Pull Request）を作成します。

> **ポイント**
> - PRタイトルは簡潔に（例：「ユーザー登録APIを実装」）  
> - PR本文には概要，変更点，確認してほしいポイントを記載  

### 6. レビュー・修正
レビュアーがコメントを残した場合は，修正コミットを行い再プッシュします。

```bash
git add .
git commit -m "レビュー修正：〇〇を修正"
git push origin feature/〇〇
```

### 7. マージ
レビューが通ったら，`develop` ブランチにマージします。

### 8. 作業ブランチの削除
マージ後は不要になったブランチを削除します。

```bash
git branch -d feature/〇〇        # ローカル削除
git push origin --delete feature/〇〇  # リモート削除
```