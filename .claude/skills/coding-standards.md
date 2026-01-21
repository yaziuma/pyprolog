---
name: coding-standards
description: Python、FastAPI、SQLAlchemy開発のための汎用コーディング標準、ベストプラクティス、パターン。
---

# コーディング標準・ベストプラクティス

すべてのPythonプロジェクトに適用可能な汎用コーディング標準。

## コード品質原則

### 1. 可読性第一
- コードは書くより読まれることが多い
- 明確な変数と関数名
- コメントよりも自己文書化コードを優先
- 一貫したフォーマット（Ruffで自動化）

### 2. KISS（Keep It Simple, Stupid）
- 動作する最もシンプルなソリューション
- 過度なエンジニアリングを避ける
- 早すぎる最適化はしない
- 巧妙なコードより理解しやすいコード

### 3. DRY（Don't Repeat Yourself）
- 共通ロジックを関数に抽出
- 再利用可能なモジュールを作成
- モジュール間でユーティリティを共有
- コピー&ペーストプログラミングを避ける

### 4. YAGNI（You Aren't Gonna Need It）
- 必要になる前に機能を構築しない
- 投機的汎用性を避ける
- 必要な時のみ複雑性を追加
- シンプルに始めて、必要時にリファクタリング

## Python標準

### 変数命名

```python
# 良い：説明的な名前（snake_case）
market_search_query = "election"
is_user_authenticated = True
total_revenue = 1000

# 悪い：不明確な名前
q = "election"
flag = True
x = 1000
```

### 関数命名

```python
# 良い：動詞-名詞パターン（snake_case）
async def fetch_market_data(market_id: str) -> Market:
    ...

def calculate_similarity(a: list[float], b: list[float]) -> float:
    ...

def is_valid_email(email: str) -> bool:
    ...

# 悪い：不明確または名詞のみ
async def market(id):
    ...

def similarity(a, b):
    ...

def email(e):
    ...
```

### 不変性パターン（重要）

```python
# 良い：新しいオブジェクトを作成
updated_user = user.model_copy(update={"name": "New Name"})

updated_list = [*items, new_item]

# 辞書の不変更新
updated_dict = {**original_dict, "key": "new_value"}

# 悪い：直接ミューテート
user.name = "New Name"  # 避ける
items.append(new_item)  # 状況による
```

### エラーハンドリング

```python
from httpx import HTTPStatusError

# 良い：包括的なエラーハンドリング
async def fetch_data(url: str) -> dict:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code}")
        raise ValueError(f"データの取得に失敗しました: {e}")
    except Exception as e:
        logger.error(f"フェッチが失敗しました: {e}")
        raise

# 悪い：エラーハンドリングなし
async def fetch_data(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

### Async/Awaitベストプラクティス

```python
import asyncio

# 良い：可能な場合は並列実行
users, markets, stats = await asyncio.gather(
    fetch_users(),
    fetch_markets(),
    fetch_stats()
)

# 悪い：不要な逐次実行
users = await fetch_users()
markets = await fetch_markets()
stats = await fetch_stats()
```

### 型安全性

```python
from pydantic import BaseModel
from typing import Literal
from datetime import datetime

# 良い：適切な型（Pydanticモデル）
class Market(BaseModel):
    id: str
    name: str
    status: Literal["active", "resolved", "closed"]
    created_at: datetime

def get_market(id: str) -> Market:
    ...

# 悪い：Anyを使用
def get_market(id) -> dict:
    ...
```

## FastAPIベストプラクティス

### ルートハンドラー構造

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/markets", tags=["markets"])

class MarketCreate(BaseModel):
    name: str
    description: str

class MarketResponse(BaseModel):
    id: str
    name: str
    description: str

@router.post("/", response_model=MarketResponse, status_code=status.HTTP_201_CREATED)
async def create_market(
    market: MarketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MarketResponse:
    """マーケットを作成する"""
    new_market = await market_service.create(db, market, current_user.id)
    return MarketResponse.model_validate(new_market)
```

### 依存性注入

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    user = await verify_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="認証が必要です")
    return user

# 型エイリアスで簡潔に
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("/me")
async def get_me(db: DbSession, user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)
```

## API設計標準

### REST API規則

```
GET    /api/markets              # すべてのマーケットをリスト
GET    /api/markets/{id}         # 特定のマーケットを取得
POST   /api/markets              # 新しいマーケットを作成
PUT    /api/markets/{id}         # マーケットを更新（完全）
PATCH  /api/markets/{id}         # マーケットを更新（部分）
DELETE /api/markets/{id}         # マーケットを削除

# フィルタリング用クエリパラメータ
GET /api/markets?status=active&limit=10&offset=0
```

### レスポンス形式

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    meta: Optional[dict] = None

# 成功レスポンス
@router.get("/markets")
async def get_markets(db: DbSession) -> ApiResponse[list[Market]]:
    markets = await market_service.get_all(db)
    return ApiResponse(
        success=True,
        data=markets,
        meta={"total": len(markets), "page": 1, "limit": 10}
    )

# エラーレスポンス
@router.get("/markets/{id}")
async def get_market(id: str, db: DbSession) -> ApiResponse[Market]:
    market = await market_service.get_by_id(db, id)
    if not market:
        raise HTTPException(
            status_code=404,
            detail="マーケットが見つかりません"
        )
    return ApiResponse(success=True, data=market)
```

### 入力検証

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

# 良い：スキーマ検証
class CreateMarketSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    end_date: datetime
    categories: list[str] = Field(..., min_length=1)

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v: list[str]) -> list[str]:
        if len(v) > 10:
            raise ValueError("カテゴリは最大10個まで")
        return v

@router.post("/markets")
async def create_market(
    market: CreateMarketSchema,
    db: DbSession
) -> ApiResponse[Market]:
    # Pydanticが自動的に検証
    result = await market_service.create(db, market)
    return ApiResponse(success=True, data=result)
```

## ファイル構成

### プロジェクト構造

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPIアプリケーション
│   ├── config.py            # 設定
│   ├── database.py          # データベース接続
│   ├── api/                  # APIルーター
│   │   ├── __init__.py
│   │   ├── markets.py
│   │   ├── users.py
│   │   └── auth.py
│   ├── models/              # SQLAlchemyモデル
│   │   ├── __init__.py
│   │   ├── market.py
│   │   └── user.py
│   ├── schemas/             # Pydanticスキーマ
│   │   ├── __init__.py
│   │   ├── market.py
│   │   └── user.py
│   ├── services/            # ビジネスロジック
│   │   ├── __init__.py
│   │   ├── market_service.py
│   │   └── user_service.py
│   └── utils/               # ヘルパー関数
│       ├── __init__.py
│       └── helpers.py
├── templates/               # Jinja2テンプレート
├── static/                  # 静的ファイル
├── tests/                   # テスト
├── alembic/                 # マイグレーション
├── pyproject.toml
└── .env.example
```

### ファイル命名

```
app/api/markets.py           # モジュールはsnake_case
app/models/market.py         # 単数形
app/schemas/market.py        # 対応するスキーマ
app/services/market_service.py  # サービス層
tests/test_markets.py        # test_プレフィックス
```

## コメント・ドキュメント

### コメントするタイミング

```python
# 良い：なぜを説明、何をではない
# 停止中のAPIを圧迫しないよう指数バックオフを使用
delay = min(1000 * (2 ** retry_count), 30000)

# パフォーマンスのため意図的にリスト内包表記を避ける
for item in large_dataset:
    process(item)

# 悪い：明らかなことを述べる
# カウンターを1増加
count += 1

# 名前をユーザーの名前に設定
name = user.name
```

### パブリックAPIのDocstring

```python
async def search_markets(
    query: str,
    limit: int = 10
) -> list[Market]:
    """セマンティック類似性を使用してマーケットを検索。

    Args:
        query: 自然言語検索クエリ
        limit: 結果の最大数（デフォルト：10）

    Returns:
        類似度スコアでソートされたマーケットリスト

    Raises:
        ValueError: OpenAI APIが失敗またはRedis利用不可の場合

    Example:
        >>> results = await search_markets("election", 5)
        >>> print(results[0].name)
        "Trump vs Biden"
    """
    ...
```

## パフォーマンスベストプラクティス

### キャッシング

```python
from functools import lru_cache
from cachetools import TTLCache

# 設定のキャッシュ
@lru_cache
def get_settings() -> Settings:
    return Settings()

# TTL付きキャッシュ
cache = TTLCache(maxsize=100, ttl=300)  # 5分

async def get_market_with_cache(market_id: str) -> Market:
    if market_id in cache:
        return cache[market_id]

    market = await fetch_market(market_id)
    cache[market_id] = market
    return market
```

### データベースクエリ

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# 良い：必要な列のみ選択
stmt = (
    select(Market.id, Market.name, Market.status)
    .where(Market.status == "active")
    .order_by(Market.volume.desc())
    .limit(10)
)
result = await session.execute(stmt)

# 良い：N+1問題を避けるためeager loading
stmt = (
    select(Market)
    .options(selectinload(Market.creator))
    .where(Market.id == market_id)
)

# 悪い：すべてを選択
stmt = select(Market)
```

## テスト標準

### テスト構造（AAAパターン）

```python
import pytest

def test_calculate_similarity():
    # Arrange（準備）
    vector1 = [1, 0, 0]
    vector2 = [0, 1, 0]

    # Act（実行）
    similarity = calculate_cosine_similarity(vector1, vector2)

    # Assert（検証）
    assert similarity == 0
```

### テスト命名

```python
# 良い：説明的なテスト名
def test_returns_empty_list_when_no_markets_match_query():
    ...

def test_raises_error_when_api_key_missing():
    ...

def test_falls_back_to_substring_search_when_redis_unavailable():
    ...

# 悪い：曖昧なテスト名
def test_works():
    ...

def test_search():
    ...
```

## コードの臭い検出

以下のアンチパターンに注意：

### 1. 長い関数
```python
# 悪い：50行超の関数
def process_market_data():
    # 100行のコード
    ...

# 良い：小さな関数に分割
def process_market_data():
    validated = validate_data()
    transformed = transform_data(validated)
    return save_data(transformed)
```

### 2. 深いネスト
```python
# 悪い：5レベル以上のネスト
if user:
    if user.is_admin:
        if market:
            if market.is_active:
                if has_permission:
                    # 何かを実行
                    ...

# 良い：早期リターン
if not user:
    return
if not user.is_admin:
    return
if not market:
    return
if not market.is_active:
    return
if not has_permission:
    return

# 何かを実行
```

### 3. マジックナンバー
```python
# 悪い：説明のない数値
if retry_count > 3:
    ...
await asyncio.sleep(0.5)

# 良い：名前付き定数
MAX_RETRIES = 3
DEBOUNCE_DELAY_SECONDS = 0.5

if retry_count > MAX_RETRIES:
    ...
await asyncio.sleep(DEBOUNCE_DELAY_SECONDS)
```

**覚えておいてください**：コード品質は交渉の余地がありません。明確で保守可能なコードは迅速な開発と自信を持ったリファクタリングを可能にします。
