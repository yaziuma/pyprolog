# プロジェクトガイドラインスキル（例）

これはプロジェクト固有のスキルの例です。独自のプロジェクト用のテンプレートとして使用してください。

---

## 使用タイミング

設計された特定のプロジェクトで作業する際にこのスキルを参照してください。プロジェクトスキルには以下が含まれます:
- アーキテクチャ概要
- ファイル構造
- コードパターン
- テスト要件
- デプロイメントワークフロー

---

## アーキテクチャ概要

**技術スタック:**
- **バックエンド**: FastAPI (Python 3.11+)、Pydanticモデル
- **データベース**: PostgreSQL + SQLAlchemy 2.0
- **テンプレート**: Jinja2
- **フロントエンド**: htmx + Alpine.js
- **AI**: Claude API（ツール呼び出しと構造化出力）
- **キャッシュ**: Redis
- **デプロイメント**: Docker + Cloud Run
- **テスト**: pytest、Playwright (E2E)

**サービス:**
```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI アプリケーション                  │
│  Python 3.11 + Pydantic + SQLAlchemy + Jinja2              │
│  デプロイ: Cloud Run / Railway                              │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │PostgreSQL│   │  Claude  │   │  Redis   │
        │ Database │   │   API    │   │  Cache   │
        └──────────┘   └──────────┘   └──────────┘
```

---

## ファイル構造

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPIアプリエントリ
│   ├── config.py            # 設定（環境変数）
│   ├── database.py          # SQLAlchemy設定
│   ├── api/                 # APIルーター
│   │   ├── __init__.py
│   │   ├── auth.py          # 認証API
│   │   ├── users.py         # ユーザーAPI
│   │   └── markets.py       # マーケットAPI
│   ├── models/              # SQLAlchemyモデル
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── market.py
│   ├── schemas/             # Pydanticスキーマ
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── market.py
│   ├── services/            # ビジネスロジック
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   └── market_service.py
│   └── utils/               # ユーティリティ
│       ├── __init__.py
│       └── helpers.py
│
├── templates/               # Jinja2テンプレート
│   ├── base.html
│   ├── pages/
│   │   ├── home.html
│   │   └── dashboard.html
│   └── partials/            # htmx部分テンプレート
│       ├── market_list.html
│       └── user_card.html
│
├── static/                  # 静的ファイル
│   ├── css/
│   └── js/
│
├── tests/                   # テスト
│   ├── conftest.py
│   ├── test_api/
│   └── e2e/
│
├── alembic/                 # マイグレーション
│   ├── versions/
│   └── env.py
│
├── deploy/                  # デプロイメント設定
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── pyproject.toml           # 依存関係
├── .env.example             # 環境変数テンプレート
└── CLAUDE.md                # Claude Code設定
```

---

## コードパターン

### APIレスポンス形式

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: T) -> "ApiResponse[T]":
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> "ApiResponse[T]":
        return cls(success=False, error=error)
```

### ルートハンドラー

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

router = APIRouter(prefix="/api/markets", tags=["markets"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("/", response_model=ApiResponse[list[MarketResponse]])
async def list_markets(db: DbSession) -> ApiResponse[list[MarketResponse]]:
    markets = await market_service.get_all(db)
    return ApiResponse.ok([MarketResponse.model_validate(m) for m in markets])

@router.post("/", response_model=ApiResponse[MarketResponse])
async def create_market(
    market: MarketCreate,
    db: DbSession,
    user: CurrentUser
) -> ApiResponse[MarketResponse]:
    new_market = await market_service.create(db, market, user.id)
    return ApiResponse.ok(MarketResponse.model_validate(new_market))
```

### Claude AI統合（構造化出力）

```python
from anthropic import Anthropic
from pydantic import BaseModel

class AnalysisResult(BaseModel):
    summary: str
    key_points: list[str]
    confidence: float

async def analyze_with_claude(content: str) -> AnalysisResult:
    client = Anthropic()

    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": content}],
        tools=[{
            "name": "provide_analysis",
            "description": "構造化された分析を提供",
            "input_schema": AnalysisResult.model_json_schema()
        }],
        tool_choice={"type": "tool", "name": "provide_analysis"}
    )

    # ツール使用結果を抽出
    tool_use = next(
        block for block in response.content
        if block.type == "tool_use"
    )

    return AnalysisResult(**tool_use.input)
```

### htmxパーシャルレスポンス

```python
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

@router.get("/search", response_class=HTMLResponse)
async def search_markets(
    request: Request,
    q: str,
    db: DbSession
) -> HTMLResponse:
    """htmx用の部分テンプレートを返す"""
    markets = await market_service.search(db, q)
    return templates.TemplateResponse(
        "partials/market_list.html",
        {"request": request, "markets": markets}
    )
```

---

## テスト要件

### バックエンド（pytest）

```bash
# すべてのテストを実行
pytest tests/

# カバレッジ付きで実行
pytest tests/ --cov=app --cov-report=html

# 特定のテストファイルを実行
pytest tests/test_api/test_markets.py -v
```

**テスト構造:**
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_list_markets(client: AsyncClient):
    response = await client.get("/api/markets")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
```

### E2E（Playwright）

```bash
# E2Eテストを実行
pytest tests/e2e/ --browser chromium
```

**テスト構造:**
```python
import pytest
from playwright.async_api import async_playwright, expect

@pytest.mark.asyncio
async def test_user_can_search_markets():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("/")

        # マーケットを検索
        await page.fill('input[name="q"]', "election")
        await page.wait_for_timeout(600)  # デバウンス

        # 結果を確認
        results = page.locator('[data-testid="market-card"]')
        await expect(results).to_have_count(5, timeout=5000)

        await browser.close()
```

---

## デプロイメントワークフロー

### デプロイ前チェックリスト

- [ ] すべてのテストがローカルで通る
- [ ] `ruff check .` が通る
- [ ] `mypy app/` が通る
- [ ] ハードコードされたシークレットがない
- [ ] 環境変数が文書化されている
- [ ] データベースマイグレーションが準備済み

### デプロイメントコマンド

```bash
# Dockerイメージをビルド
docker build -t myapp .

# Cloud Runにデプロイ
gcloud run deploy myapp \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated
```

### 環境変数

```bash
# .env.example
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=sk-ant-...
SECRET_KEY=your-secret-key
DEBUG=false
```

---

## 重要なルール

1. **絵文字禁止** - コード、コメント、ドキュメントで絵文字を使用しない
2. **不変性** - オブジェクトや配列を変更しない
3. **TDD** - 実装前にテストを書く
4. **80%カバレッジ** 最低限
5. **多くの小さなファイル** - 通常200-400行、最大800行
6. **print文禁止** プロダクションコードで
7. **適切なエラーハンドリング** try/exceptで
8. **入力検証** Pydanticで

---

## 関連スキル

- `coding-standards.md` - 一般的なコーディングベストプラクティス
- `backend-patterns.md` - FastAPIとSQLAlchemyパターン
- `frontend-patterns.md` - htmxとJinja2パターン
- `tdd-workflow/` - テスト駆動開発手法
