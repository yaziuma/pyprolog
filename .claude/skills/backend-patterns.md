---
name: backend-patterns
description: FastAPI、SQLAlchemy、Pydanticのためのバックエンドアーキテクチャパターン、API設計、データベース最適化、サーバーサイドベストプラクティス。
---

# バックエンド開発パターン

スケーラブルなPythonサーバーサイドアプリケーションのためのバックエンドアーキテクチャパターンとベストプラクティス。

## API設計パターン

### RESTful API構造

```python
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional

router = APIRouter(prefix="/api/markets", tags=["markets"])

# リソースベースのURL
@router.get("/")                    # リソース一覧
@router.get("/{id}")                # 単一リソース取得
@router.post("/")                   # リソース作成
@router.put("/{id}")                # リソース置換
@router.patch("/{id}")              # リソース更新
@router.delete("/{id}")             # リソース削除

# フィルタリング、ソート、ページネーションのクエリパラメータ
@router.get("/")
async def list_markets(
    status: Optional[str] = Query(None),
    sort: Optional[str] = Query("created_at"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> list[MarketResponse]:
    ...
```

### リポジトリパターン

```python
from abc import ABC, abstractmethod
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class MarketRepository(ABC):
    """データアクセスロジックの抽象化"""

    @abstractmethod
    async def find_all(self, filters: Optional[MarketFilters] = None) -> list[Market]:
        ...

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[Market]:
        ...

    @abstractmethod
    async def create(self, data: CreateMarketDto) -> Market:
        ...

    @abstractmethod
    async def update(self, id: str, data: UpdateMarketDto) -> Market:
        ...

    @abstractmethod
    async def delete(self, id: str) -> None:
        ...


class SQLAlchemyMarketRepository(MarketRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_all(self, filters: Optional[MarketFilters] = None) -> list[Market]:
        stmt = select(MarketModel)

        if filters:
            if filters.status:
                stmt = stmt.where(MarketModel.status == filters.status)
            if filters.limit:
                stmt = stmt.limit(filters.limit)
            if filters.offset:
                stmt = stmt.offset(filters.offset)

        result = await self.session.execute(stmt)
        return [Market.model_validate(m) for m in result.scalars().all()]

    async def find_by_id(self, id: str) -> Optional[Market]:
        stmt = select(MarketModel).where(MarketModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return Market.model_validate(model) if model else None

    # その他のメソッド...
```

### サービス層パターン

```python
from typing import Optional

class MarketService:
    """ビジネスロジックをデータアクセスから分離"""

    def __init__(self, market_repo: MarketRepository):
        self.market_repo = market_repo

    async def search_markets(self, query: str, limit: int = 10) -> list[Market]:
        # ビジネスロジック
        embedding = await generate_embedding(query)
        results = await self.vector_search(embedding, limit)

        # 完全なデータを取得
        market_ids = [r.id for r in results]
        markets = await self.market_repo.find_by_ids(market_ids)

        # 類似度でソート
        score_map = {r.id: r.score for r in results}
        return sorted(markets, key=lambda m: score_map.get(m.id, 0), reverse=True)

    async def _vector_search(self, embedding: list[float], limit: int) -> list[SearchResult]:
        # ベクトル検索の実装
        ...
```

### 依存性注入パターン

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, AsyncGenerator

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

def get_market_repository(
    session: AsyncSession = Depends(get_db)
) -> MarketRepository:
    return SQLAlchemyMarketRepository(session)

def get_market_service(
    repo: MarketRepository = Depends(get_market_repository)
) -> MarketService:
    return MarketService(repo)

# 型エイリアス
DbSession = Annotated[AsyncSession, Depends(get_db)]
MarketRepo = Annotated[MarketRepository, Depends(get_market_repository)]
MarketSvc = Annotated[MarketService, Depends(get_market_service)]

# 使用方法
@router.get("/{id}")
async def get_market(id: str, service: MarketSvc) -> MarketResponse:
    market = await service.find_by_id(id)
    if not market:
        raise HTTPException(status_code=404, detail="マーケットが見つかりません")
    return MarketResponse.model_validate(market)
```

### ミドルウェアパターン

```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time

class TimingMiddleware(BaseHTTPMiddleware):
    """リクエスト処理時間を計測"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response


class AuthMiddleware(BaseHTTPMiddleware):
    """認証ミドルウェア"""

    async def dispatch(self, request: Request, call_next):
        # 公開エンドポイントをスキップ
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "認証が必要です"}
            )

        try:
            user = await verify_token(token)
            request.state.user = user
        except Exception:
            return JSONResponse(
                status_code=401,
                content={"detail": "無効なトークンです"}
            )

        return await call_next(request)

# アプリケーションに追加
app.add_middleware(TimingMiddleware)
app.add_middleware(AuthMiddleware)
```

## データベースパターン

### SQLAlchemyモデル定義

```python
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from uuid import uuid4

class Base(DeclarativeBase):
    pass

class MarketModel(Base):
    __tablename__ = "markets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    creator_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=func.now())

    # リレーション
    creator: Mapped["UserModel"] = relationship(back_populates="markets")
    trades: Mapped[list["TradeModel"]] = relationship(back_populates="market")
```

### クエリ最適化

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

# 良い例: 必要な列のみ選択
stmt = (
    select(MarketModel.id, MarketModel.name, MarketModel.status)
    .where(MarketModel.status == "active")
    .order_by(MarketModel.volume.desc())
    .limit(10)
)
result = await session.execute(stmt)
markets = result.all()

# 悪い例: すべてを選択
stmt = select(MarketModel)
```

### N+1クエリ問題の防止

```python
# 悪い例: N+1クエリ問題
markets = await session.execute(select(MarketModel))
for market in markets.scalars():
    # 各マーケットで追加クエリが発生
    creator = await session.execute(
        select(UserModel).where(UserModel.id == market.creator_id)
    )

# 良い例: Eager Loading（selectinload）
stmt = (
    select(MarketModel)
    .options(selectinload(MarketModel.creator))
    .where(MarketModel.status == "active")
)
result = await session.execute(stmt)
markets = result.scalars().all()
# market.creator は追加クエリなしでアクセス可能

# 良い例: Eager Loading（joinedload）- 1対1関係向け
stmt = (
    select(MarketModel)
    .options(joinedload(MarketModel.creator))
    .where(MarketModel.id == market_id)
)
```

### トランザクションパターン

```python
from sqlalchemy.ext.asyncio import AsyncSession

async def create_market_with_position(
    session: AsyncSession,
    market_data: CreateMarketDto,
    position_data: CreatePositionDto
) -> Market:
    """トランザクション内で複数操作を実行"""
    try:
        # マーケット作成
        market = MarketModel(**market_data.model_dump())
        session.add(market)
        await session.flush()  # IDを取得

        # ポジション作成
        position = PositionModel(
            market_id=market.id,
            **position_data.model_dump()
        )
        session.add(position)

        await session.commit()
        await session.refresh(market)
        return Market.model_validate(market)

    except Exception:
        await session.rollback()
        raise


# コンテキストマネージャーを使用
async def transfer_funds(from_user_id: str, to_user_id: str, amount: float):
    async with async_session_factory() as session:
        async with session.begin():  # 自動コミット/ロールバック
            from_user = await session.get(UserModel, from_user_id)
            to_user = await session.get(UserModel, to_user_id)

            if from_user.balance < amount:
                raise ValueError("残高不足")

            from_user.balance -= amount
            to_user.balance += amount
```

## キャッシュ戦略

### Redisキャッシュ層

```python
import redis.asyncio as redis
import json
from typing import Optional, TypeVar, Callable
from functools import wraps

T = TypeVar("T")

class CacheService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def get(self, key: str) -> Optional[dict]:
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value: dict, ttl: int = 300) -> None:
        await self.redis.setex(key, ttl, json.dumps(value))

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)


class CachedMarketRepository(MarketRepository):
    def __init__(self, base_repo: MarketRepository, cache: CacheService):
        self.base_repo = base_repo
        self.cache = cache

    async def find_by_id(self, id: str) -> Optional[Market]:
        cache_key = f"market:{id}"

        # キャッシュをチェック
        cached = await self.cache.get(cache_key)
        if cached:
            return Market.model_validate(cached)

        # キャッシュミス - データベースから取得
        market = await self.base_repo.find_by_id(id)

        if market:
            await self.cache.set(cache_key, market.model_dump(), ttl=300)

        return market

    async def invalidate(self, id: str) -> None:
        await self.cache.delete(f"market:{id}")
```

### デコレーターベースのキャッシュ

```python
from functools import wraps
from typing import Callable, Any

def cached(ttl: int = 300, key_prefix: str = ""):
    """キャッシュデコレーター"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # キャッシュキーを生成
            cache_key = f"{key_prefix}:{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"

            # キャッシュをチェック
            cached_value = await cache_service.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 関数を実行
            result = await func(*args, **kwargs)

            # 結果をキャッシュ
            await cache_service.set(cache_key, result, ttl=ttl)

            return result
        return wrapper
    return decorator


# 使用例
@cached(ttl=600, key_prefix="markets")
async def get_popular_markets(limit: int = 10) -> list[Market]:
    ...
```

## エラーハンドリングパターン

### 集中エラーハンドラー

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)

class ApiError(Exception):
    """カスタムAPIエラー"""
    def __init__(self, status_code: int, message: str, details: dict = None):
        self.status_code = status_code
        self.message = message
        self.details = details or {}


app = FastAPI()

@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": "検証エラー",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("予期しないエラー")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "内部サーバーエラー"
        }
    )
```

### 指数バックオフでのリトライ

```python
import asyncio
from typing import TypeVar, Callable, Awaitable

T = TypeVar("T")

async def retry_with_backoff(
    func: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0
) -> T:
    """指数バックオフでリトライ"""
    last_error: Exception = None

    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            last_error = e

            if attempt < max_retries - 1:
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning(f"リトライ {attempt + 1}/{max_retries}、{delay}秒後...")
                await asyncio.sleep(delay)

    raise last_error


# 使用例
data = await retry_with_backoff(
    lambda: fetch_from_external_api(),
    max_retries=3
)
```

## 認証・認可

### JWT認証

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import datetime, timedelta

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

class TokenPayload(BaseModel):
    sub: str  # user_id
    exp: datetime
    role: str

def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=24)
    payload = TokenPayload(sub=user_id, exp=expire, role=role)
    return jwt.encode(payload.model_dump(), SECRET_KEY, algorithm="HS256")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: DbSession = Depends()
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        token_data = TokenPayload.model_validate(payload)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なトークンです"
        )

    user = await db.get(UserModel, token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザーが見つかりません"
        )

    return User.model_validate(user)
```

### ロールベースアクセス制御

```python
from enum import Enum
from typing import Callable
from functools import wraps

class Role(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"

ROLE_PERMISSIONS = {
    Role.ADMIN: {"read", "write", "delete", "admin"},
    Role.MODERATOR: {"read", "write", "delete"},
    Role.USER: {"read", "write"}
}

def require_permission(permission: str):
    """権限チェックデコレーター"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            user_permissions = ROLE_PERMISSIONS.get(current_user.role, set())

            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="権限がありません"
                )

            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


# 使用例
@router.delete("/{id}")
@require_permission("delete")
async def delete_market(
    id: str,
    current_user: User = Depends(get_current_user),
    service: MarketSvc = Depends()
):
    await service.delete(id)
    return {"success": True}
```

## レート制限

### スライディングウィンドウレート制限

```python
import redis.asyncio as redis
from fastapi import Request, HTTPException
import time

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """スライディングウィンドウでレート制限をチェック"""
        now = time.time()
        key = f"rate_limit:{identifier}"

        async with self.redis.pipeline() as pipe:
            # 古いエントリを削除
            pipe.zremrangebyscore(key, 0, now - window_seconds)
            # 現在のカウントを取得
            pipe.zcard(key)
            # 新しいリクエストを追加
            pipe.zadd(key, {str(now): now})
            # TTLを設定
            pipe.expire(key, window_seconds)

            results = await pipe.execute()

        current_count = results[1]
        return current_count < max_requests


# FastAPI依存性として使用
async def rate_limit_dependency(
    request: Request,
    limiter: RateLimiter = Depends(get_rate_limiter)
):
    client_ip = request.client.host
    allowed = await limiter.check_limit(client_ip, max_requests=100, window_seconds=60)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="リクエストが多すぎます。しばらくお待ちください。"
        )


# ルートに適用
@router.get("/", dependencies=[Depends(rate_limit_dependency)])
async def list_markets():
    ...
```

## バックグラウンドタスク

### FastAPIバックグラウンドタスク

```python
from fastapi import BackgroundTasks

async def send_notification(user_id: str, message: str):
    """非同期で通知を送信"""
    # 通知ロジック
    ...

@router.post("/markets")
async def create_market(
    market: CreateMarketSchema,
    background_tasks: BackgroundTasks,
    service: MarketSvc
) -> MarketResponse:
    new_market = await service.create(market)

    # バックグラウンドで通知
    background_tasks.add_task(
        send_notification,
        user_id=new_market.creator_id,
        message=f"マーケット「{new_market.name}」が作成されました"
    )

    return MarketResponse.model_validate(new_market)
```

### Celeryタスクキュー

```python
from celery import Celery

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)

@celery_app.task
def process_market_data(market_id: str):
    """重い処理をバックグラウンドで実行"""
    # 処理ロジック
    ...

@celery_app.task
def generate_report(user_id: str, report_type: str):
    """レポート生成"""
    ...


# FastAPIから呼び出し
@router.post("/markets/{id}/process")
async def trigger_processing(id: str):
    task = process_market_data.delay(id)
    return {"task_id": task.id, "status": "processing"}


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }
```

## ログ・監視

### 構造化ログ

```python
import logging
import json
from datetime import datetime
from typing import Any

class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # 追加コンテキストを含める
        if hasattr(record, "context"):
            log_entry["context"] = record.context

        return json.dumps(log_entry)


# ロガー設定
def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())

    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# 使用例
logger = logging.getLogger(__name__)

async def process_request(request_id: str):
    logger.info(
        "リクエストを処理中",
        extra={"context": {"request_id": request_id, "user_id": "123"}}
    )
```

### リクエストログミドルウェア

```python
import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()

        logger.info(
            "リクエスト開始",
            extra={
                "context": {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": request.client.host
                }
            }
        )

        response = await call_next(request)

        process_time = time.perf_counter() - start_time

        logger.info(
            "リクエスト完了",
            extra={
                "context": {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time_ms": round(process_time * 1000, 2)
                }
            }
        )

        response.headers["X-Request-ID"] = request_id
        return response
```

**覚えておくこと**: バックエンドパターンはスケーラブルで保守可能なサーバーサイドアプリケーションを可能にします。複雑さのレベルに適したパターンを選択してください。
