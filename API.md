## Youseisan API

このドキュメントは Django 製バックエンド (`/account`, `/guilds`, `/twitch`, `/birthday`, `/stripe`) のフロントエンド実装向け API 仕様です。レスポンスはすべて JSON、日時は `Asia/Tokyo` タイムゾーンで保存されています。

### Base URL

- ローカル: `https://api.youseisan.local`
- 本番: `https://api.youseisan.jp`
- `Content-Type: application/json` を送信してください。

### 認証と CORS

| 区分 | 方法 | 備考 |
| --- | --- | --- |
| ユーザー | Discord OAuth → JWT | `POST /account/auth/discord/` で `code` を渡すと `access_token`(30分) / `refresh_token`(30日) が **HttpOnly Cookie** に保存されます。フロント（Next.js）はサーバーサイド(Route Handler 等)で Cookie を読み取り、バックエンドへ fetch するときに `Authorization: Bearer <access_token>` ヘッダーを付与してください。ブラウザ JS からトークンを読む必要はありません。 |
| Bot | API キー | `Authorization: Bot <BOT_API_KEY>` のみ。Bot がアクセス可能なエンドポイントには `IsBotAuthorized` が付いています。 |

- JWT は `core.authentication.BotOrUserAuthentication` で検証され、`Bot` 認証が優先されます。
- CORS で `http://localhost`, `https://youseisan.jp`, `https://youseisan.local` が許可され、`withCredentials` が必要です。

### 共通レスポンス / エラー

- 成功は基本的に 200/201/204。バリデーションエラーは 400、権限エラーは 403、存在しない場合は 404。
- Stripe などの外部連携で障害が起こった場合は 502 を返します。
- すべてのエンドポイントで CSRF 対策済み (JWT+Cookie 運用)。

---

## 認証 API (`/account/auth/*`)

### `POST /account/auth/discord/`
- 説明: Discord OAuth コードをサーバーに渡し、ユーザー作成とギルド同期、JWT Cookie 付与を行います。
- リクエスト例:
```json
{ "code": "<Discord authorization code>" }
```
- レスポンス: `{"user": DiscordUser}`（ユーザー情報のみ）。JWT は Cookie に格納されるため、ボディには含まれません。
- エラー: `400 code missing`, `502 Discord API failure`

### `POST /account/auth/token/refresh/`
- 説明: Cookie（または Body）の `refresh_token` を検証し、新しい `access_token` / `refresh_token` を **再び HttpOnly Cookie としてセット** します。レスポンスボディは空なので、Next.js などのサーバー側コードは Cookie を再取得して以降の fetch に利用してください。
- リクエスト: 基本的に空ボディで `withCredentials` を付けて呼べば OK。必要なら `{"refresh_token": "<token>"}` を明示的に渡せます。
- レスポンス: 200 / エラーは 400（refresh token 不正）。Cookie のみ更新されます。

### `POST /account/auth/token/validate/`
- 説明: アクセストークンの有効性を確認します。
- リクエスト:
```json
{ "access_token": "<token>" }
```
- レスポンス例: `{"valid": true}` / `{"valid": false, "error": "<reason>"}`。

---

## ユーザー API (`/account/users/*`)

| メソッド/パス | 要求権限 | 説明 |
| --- | --- | --- |
| `GET /account/users/` | Bot | 全 Discord ユーザー一覧 |
| `POST /account/users/` | Bot | ユーザーを手動作成（通常は OAuth で作成） |
| `GET /account/users/{discord_id}/` | 自分 or Bot | 自分自身 or Bot がユーザー詳細取得 |
| `PATCH /account/users/{discord_id}/` | 自分 or Bot | 自分自身 or Bot が部分更新 |
| `DELETE /account/users/{discord_id}/` | Bot | ユーザー削除 |
| `GET /account/users/{discord_id}/own_guilds/` | 自分 or Bot | ユーザーがオーナーのギルド一覧 |
| `GET /account/users/{discord_id}/guilds/` | 自分 or Bot | ユーザーが所属するギルド（`UserGuilds`） |

- `discord_id` は整数型 (Snowflake)。
- JWT ユーザーは自分以外の ID にアクセスすると 403。
- Serializer: `DiscordUserSerializer` は `password`/`last_login` を除外。

---

## Guild API (`/guilds/*`)

### 一覧・作成
- `GET /guilds/` (Bot 専用): 全 Guild を返却。
- `POST /guilds/` (Bot 専用): `GuildSerializer` 全フィールドで作成。

### 個別操作
| メソッド/パス | 権限 | 備考 |
| --- | --- | --- |
| `GET /guilds/{discord_id}/` | owner or Bot | 単一 Guild の詳細 |
| `PATCH /guilds/{discord_id}/` | owner or Bot | ユーザーは `stripe_customer_id`, `stripe_subscription_id`, `status`, `current_period_end`, `owner`, `plan` を送ると 403。Bot だけが `GuildAdminSerializer` で全フィールド更新可能。 |
| `DELETE /guilds/{discord_id}/` | Bot | 完全削除 |

### 関連データ
| エンドポイント | 権限 | 返却 |
| --- | --- | --- |
| `GET /guilds/{discord_id}/users/` | owner or Bot | メンバー (`DiscordUserSerializer`) |
| `GET /guilds/{discord_id}/birthdays/` | owner or Bot | ギルド配下の Birthday |
| `GET /guilds/{discord_id}/twitch/` | owner or Bot | Twitch 通知設定 |
| `GET /guilds/{discord_id}/tts/` | owner or Bot | `TtsSetting`（存在しない場合は 500/404 になるので、事前にレコードを準備） |

### レベル API
- `GET /guilds/levels/?user={discord_id}&guild={guild_id}`
  - 説明: 特定ユーザーのレベル (`UserGuilds`) を取得。
  - 権限: Bot は制限なし。JWT ユーザーは「自分が所属するギルド」のデータのみ取得可。
  - レスポンス: `UserGuildsSerializer` (`user`, `guild`, `level`, `xp`, `last_message`)。
- `POST /guilds/levels/?user={discord_id}&guild={guild_id}`
  - 説明: Bot 専用でレベル情報を作成/更新。Body に更新したいフィールドだけ入れる。
  - レスポンス: 作成時 201、更新時 200。
- `POST /guilds/levels/bulk_update/`
  - 説明: Bot 専用の一括更新。リクエストボディは `{"levels": [...]}` もしくは直接配列でも可。各要素に以下を指定:
    - `user`(必須) / `guild`(必須): Discord ID (int)
    - `level`(必須): 整数
    - `xp`(任意): 整数。新規作成時を除き、省略すると既存値を保持
    - `last_message`(任意): ISO8601 文字列。省略すると既存値を保持。未指定/空文字は `null` 扱い
  - 重複キー `(user, guild)` は最後の要素が優先されます。レスポンスは `{"updated": <更新件数>, "created": <作成件数>}`。
  - エラー: 存在しないユーザー/ギルドID は 404、不正フォーマットは 400。

> 注: Level 系エンドポイントは `/guilds/levels/` 配下に集約されており、`?user=...&guild=...` クエリが必須です。

---

## Birthday API (`/birthday/*`)

| メソッド/パス | 権限 | 概要 |
| --- | --- | --- |
| `GET /birthday/?channel=&user=` | Bot: 全件 / ユーザー: 自分の Guild or 自分の Birthday | クエリで `channel_id` や `discord_id` を絞り込み可能 |
| `POST /birthday/` | Bot, Guild owner, 本人 | Body 例: `{"user": <discord_id>, "birthday": "YYYY-MM-DD", "channel_id": 123, "guild": <guild_id>}` |
| `GET /birthday/{id}` | Bot / owner / 本人 | 単一 Birthday 取得 |
| `PUT /birthday/{id}` | Bot / owner / 本人 | 部分更新 (`partial=True`) |
| `DELETE /birthday/{id}` | Bot / owner / 本人 | 削除 |

- `Birthday` は `(user, channel_id)` で一意。重複登録時は 400。

---

## Twitch API (`/twitch/*`)

| メソッド/パス | 権限 | 説明 |
| --- | --- | --- |
| `GET /twitch/?channel=&username=` | Bot: 全件 / ユーザー: 自分の Guild | クエリで `notice_channel_id` と `twitch_username` を絞り込み |
| `POST /twitch/` | Bot or Guild owner | Body 例: `{"twitch_username": "name", "notice_channel_id": 1234567890, "guild": <guild_id>}` |
| `GET /twitch/{id}` | Bot or owner | 単体取得 |
| `PUT /twitch/{id}` | Bot or owner | 部分更新 (`partial=True`) |
| `DELETE /twitch/{id}` | Bot or owner | 削除 |

- `(twitch_username, notice_channel_id)` でユニーク制約。

---

## Stripe / Billing API (`/stripe/*`)

### `POST /stripe/webhook/`
- Stripe からのイベントを受け付けるエンドポイント（署名必須）。`ProcessedStripeEvent` に `event_id` を保存して重複処理を避け、Celery タスク `handle_stripe_event_async` に委譲します。
- 対応イベント（payments/tasks.py 参照）:
  - `customer.subscription.created/updated/deleted`
  - `checkout.session.completed`
  - `invoice.payment_succeeded/failed`
- すべて 200 を即返却し、Stripe の再送を防ぎます。

### `POST /stripe/guilds/{discord_id}/checkout/`
- 権限: Guild owner（JWT 必須）。
- Body: `{"plan": "light" | "standard" | "premium"}`
- 処理:
  1. ギルドに `stripe_customer_id` が無ければ Stripe Customer を作成し、`guild.stripe_customer_id` に保存。
  2. Stripe Checkout Session を作成し、URL と Session ID を返却。
- レスポンス例:
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay_...",
  "session_id": "cs_test_..."
}
```

### `POST /stripe/guilds/{discord_id}/billing-portal/`
- 権限: Guild owner（JWT）。
- 前提: `stripe_customer_id` が存在すること。無い場合は 400。
- 処理: Stripe Billing Portal Session を生成し、`{"url": "<portal url>"}` を返します。

---

## モデル/シリアライザー概要

| モデル | 主なフィールド |
| --- | --- |
| `account.DiscordUser` | `discord_id`(PK), `username`, `global_name`, `avatar` |
| `account.UserGuilds` | `user`, `guild`, `level`, `xp`, `last_message` |
| `guild.Guild` | `discord_id`, `name`, `icon`, `is_level_on`, `level_notice_channel_id`, `stripe_customer_id`, `stripe_subscription_id`, `status`, `current_period_end`, `plan`, `owner` |
| `guild.TtsSetting` | `guild`(OneToOne), `language`, `voice`, `num_char` |
| `birthday.Birthday` | `user`, `birthday`, `channel_id`, `guild` |
| `twitch.Twitch` | `twitch_username`, `notice_channel_id`, `guild` |
| `payments.ProcessedStripeEvent` | `event_id`, `payload`, `received_at` |

シリアライザーはいずれも `ModelSerializer` で全フィールドを返します（`DiscordUserSerializer` のみ `password`/`last_login` を除外）。Plan / Stripe 関連の更新は Bot か Stripe Webhook のみが行います。

---

## 実装時の注意

1. **トークンの扱い**: Next.js の Route Handler / サーバーアクションで HttpOnly Cookie から `access_token` を取り出し、バックエンドへの fetch に `Authorization: Bearer ...` を付けてください。401 になったら同じサーバー側コンテキストで `POST /account/auth/token/refresh/`（withCredentials）を呼び、Cookie を更新して再実行します。
2. **権限 UI**: フロント側でも「自分が owner のギルドのみ編集できる」等のガードを設け、403 を避けるようにしてください。
3. **Stripe 状態同期**: Guild 詳細レスポンスに `plan`, `status`, `current_period_end`, `stripe_customer_id`, `stripe_subscription_id` が含まれるため、課金画面ではこれらを利用してフロー分岐してください。
4. **レベル一括更新**: `POST /guilds/levels/bulk_update/` は Bot 専用です。クライアント側でも API キーを持つバックエンド経由で呼び出し、`last_message` などの日時は ISO8601 (例: `2024-01-01T09:00:00+09:00`) に揃えてください。
