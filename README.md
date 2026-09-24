# 42 Evaluation Explorer

42 APIを使い、Project進捗とEvaluation関連データを調査・集約するFastAPIアプリです。

## 現在の到達点

実機Capability Probeで、通常のApplication tokenから以下のコメント経路を取得できることを確認しました。

- `scale_team.comment`
- `feedback.comment`

一方、Project Scale定義の取得は現在のApplication tokenでは403となることを確認しています。

v0.2.0では、特定ユーザーとProjectを指定し、Scale TeamコメントとFeedbackコメントを1つのレビュー一覧へ統合します。

## 技術構成

- Python
- FastAPI
- httpx
- Jinja2
- Vanilla JavaScript

MVPではDBを使用しません。

## セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

`.env` に42 API Applicationの資格情報を設定します。

```env
FT_CLIENT_ID=your_application_uid
FT_CLIENT_SECRET=your_application_secret
```

> `FT_CLIENT_SECRET` をGitへコミットしないでください。

起動：

```bash
uvicorn app.main:app --reload
```

ブラウザ：

```text
http://127.0.0.1:8000
```

OpenAPI：

```text
http://127.0.0.1:8000/docs
```

## Project Review Aggregation

Project slugまたはIDを指定できます。

```text
GET /api/reviews/{login}?project=libft
```

レスポンスでは各Evaluationについて以下をまとめます。

- Scale Team ID
- Team ID
- Project ID
- final_mark
- corrector
- begin_at / filled_at
- `scale_team.comment`
- Feedback一覧
- `feedback.comment`
- comment source

同じコメント本文がScale TeamとFeedbackの両方に現れる場合は、統合コメント一覧では重複を除外します。

Feedback取得だけが失敗した場合はEvaluation全体を失敗させず、該当レコードの `feedback_error` に状態を残します。

APIリクエスト数を抑えるため、1回の検索でFeedbackを補完するEvaluationはデフォルト50件、最大100件です。

## Capability Report

秘密情報やレビュー本文を含めない診断レポートを生成できます。

```bash
python -m scripts.probe_report \
  --login YOUR_42_LOGIN \
  --project libft
```

出力：

```text
reports/capability-report.json
```

`reports/` はGit管理対象外です。

現在確認済みの結果：

```json
{
  "accessible_comment_paths": [
    "scale_team.comment",
    "feedback.comment"
  ],
  "project_scales_access": "forbidden"
}
```

## Capability Probe API

主な検証用エンドポイント：

```text
GET /api/test/token
GET /api/test/report/{login}?project=libft
GET /api/test/users/{login}
GET /api/test/users/{login}/projects
GET /api/test/users/{login}/teams
GET /api/test/users/{login}/scale-teams/as-corrected
GET /api/test/users/{login}/scale-teams/as-corrector
GET /api/test/projects/{project_id_or_slug}
GET /api/test/projects/{project_id_or_slug}/scales
GET /api/test/scale-teams/{scale_team_id}
GET /api/test/scale-teams/{scale_team_id}/feedbacks
GET /api/test/teams/{team_id}/uploads
```

## Project進捗

```text
GET /api/users/{login}/project-progress?project=libft&status=finished
```

## セキュリティ

- `.env` は `.gitignore` 済み
- Access Tokenはブラウザへ返しません
- 任意URLを代理取得するAPIは提供しません
- Raw probeも許可済みリソースのホワイトリストのみです
- 42 OAuthユーザーログイン実装前はlocalhostで使用してください

## 次の開発項目

- Projectを突破した複数Userの検索
- 複数Userを横断したEvaluation集約
- Level / Cursus / Project進捗による絞り込み
- キャッシュとRate Limit最適化
- 42 OAuthログイン
- 公開時のデータ露出ルール

---

# English

A FastAPI application for probing and aggregating evaluation-related data exposed by the 42 API.

The current v0.2.0 implementation has verified access to `scale_team.comment` and `feedback.comment` for the tested application token and can aggregate both sources for a selected user and project.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Configure `FT_CLIENT_ID` and `FT_CLIENT_SECRET` in `.env`. Never commit the secret.

## Review API

```text
GET /api/reviews/{login}?project=libft
```

## License

MIT

## Deployment warning

v0.2.0 still has no end-user OAuth gate. Do **not** expose it publicly with real 42 credentials yet. Keep it on localhost until 42 OAuth authentication and data-exposure rules are implemented.
