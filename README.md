# 42 Evaluation Explorer

42 APIを使い、Project進捗とEvaluation関連データの取得可否を調査するFastAPI MVPです。

## 目的

最初のマイルストーンは、一般的な42 API Application資格情報で、以下のどこまで取得できるかを確認することです。

- User
- Projects / projects_users
- Teams
- Scale Teams（被評価者 / 評価者側）
- Scale Team comment / final_mark
- Feedbacks
- Team uploads
- Project scales（権限制約確認用）

42 APIではエンドポイントごとに権限差があります。このアプリは403を単なる失敗ではなく、Capability Probeの結果として画面に表示します。

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
pip install -r requirements.txt
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

## Capability Probe

主な検証用エンドポイント：

```text
GET /api/test/token
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

レスポンス例：

```json
{
  "ok": false,
  "status_code": 403,
  "message": "42 API denied access to this resource. The endpoint may require extra roles or scopes.",
  "detail": {}
}
```

## MVP API

UserのProject進捗：

```text
GET /api/users/{login}/project-progress?project=a-maze-ing&status=finished
```

APIから見える被評価履歴：

```text
GET /api/reviews/{login}
GET /api/reviews/{login}?project_id=1234
```

## 最初に確認する手順

1. `/api/test/token` が成功することを確認
2. 自分のloginで `/api/test/users/{login}` を確認
3. `/api/test/users/{login}/projects` を確認
4. `/api/test/users/{login}/scale-teams/as-corrected` を確認
5. 返却されたScale Team IDで詳細・Feedbackを確認
6. Team IDが得られた場合はTeam uploadsも確認
7. `/projects/{id}/scales` の403有無を確認

ここで得られたJSONを基に、通常のIntraに表示されるレビューコメントと、API上の `comment` / `feedback` / `teams_uploads.comment` のどれが一致するかを判定します。

## セキュリティ

- `.env` は `.gitignore` 済み
- Access Tokenはブラウザへ返しません
- 任意URLを代理取得するAPIは提供しません
- Raw probeも許可済みリソースのホワイトリストのみです

## 現時点の制約

- 42 OAuthユーザーログインはまだ未実装です（Phase 2）
- DB / キャッシュは未実装です
- 複数ユーザー横断検索はAPI Capability確認後に追加します
- ProjectのScale定義取得は42 API側で追加権限が必要な可能性があります

---

# English

A FastAPI MVP for exploring project progress and determining which evaluation-related data is actually exposed by the 42 API to a normal application token.

## Goal

Before building a large UI or database, this project probes access to users, projects, teams, scale teams, feedbacks, team uploads, and project scales. Permission errors such as HTTP 403 are treated as useful capability results.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Configure `FT_CLIENT_ID` and `FT_CLIENT_SECRET` in `.env`. Never commit the secret.

Open `http://127.0.0.1:8000` or `http://127.0.0.1:8000/docs`.

## License

MIT

## Deployment warning

The current `0.1.0` MVP intentionally has no end-user OAuth gate. Do **not** expose it publicly with real 42 credentials yet. Keep it on localhost while verifying which evaluation data your application token can access. Public deployment belongs to Phase 2 after 42 OAuth authentication and data-exposure rules are implemented.
