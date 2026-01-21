---
name: clickhouse-io
description: 高性能分析ワークロードのためのClickHouseデータベースパターン、クエリ最適化、分析、データエンジニアリングベストプラクティス。
---

# ClickHouse分析パターン

高性能分析とデータエンジニアリングのためのClickHouse固有のパターン。

## 概要

ClickHouseは、オンライン分析処理（OLAP）のための列指向データベース管理システム（DBMS）です。大規模データセットでの高速分析クエリに最適化されています。

**主要機能:**
- 列指向ストレージ
- データ圧縮
- 並列クエリ実行
- 分散クエリ
- リアルタイム分析

## Pythonクライアント設定

### clickhouse-connectの使用

```python
import clickhouse_connect
from clickhouse_connect.driver import Client

def get_clickhouse_client() -> Client:
    """ClickHouseクライアントを取得"""
    return clickhouse_connect.get_client(
        host=os.environ.get("CLICKHOUSE_HOST", "localhost"),
        port=int(os.environ.get("CLICKHOUSE_PORT", 8123)),
        username=os.environ.get("CLICKHOUSE_USER", "default"),
        password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
        database=os.environ.get("CLICKHOUSE_DATABASE", "default")
    )

# 使用例
client = get_clickhouse_client()
result = client.query("SELECT * FROM markets_analytics LIMIT 10")
for row in result.result_rows:
    print(row)
```

### 非同期クライアント（aiochclient）

```python
from aiochclient import ChClient
from aiohttp import ClientSession

async def get_async_client() -> ChClient:
    """非同期ClickHouseクライアントを取得"""
    session = ClientSession()
    return ChClient(
        session,
        url=f"http://{os.environ['CLICKHOUSE_HOST']}:8123",
        user=os.environ.get("CLICKHOUSE_USER", "default"),
        password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
        database=os.environ.get("CLICKHOUSE_DATABASE", "default")
    )

# 使用例
async def fetch_markets():
    async with ClientSession() as session:
        client = ChClient(session)
        result = await client.fetch(
            "SELECT * FROM markets_analytics WHERE date >= today() - 7"
        )
        return result
```

## テーブル設計パターン

### MergeTreeエンジン（最も一般的）

```sql
CREATE TABLE markets_analytics (
    date Date,
    market_id String,
    market_name String,
    volume UInt64,
    trades UInt32,
    unique_traders UInt32,
    avg_trade_size Float64,
    created_at DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, market_id)
SETTINGS index_granularity = 8192;
```

### ReplacingMergeTree（重複排除）

```sql
-- 重複の可能性があるデータ用
CREATE TABLE user_events (
    event_id String,
    user_id String,
    event_type String,
    timestamp DateTime,
    properties String
) ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (user_id, event_id, timestamp)
PRIMARY KEY (user_id, event_id);
```

### AggregatingMergeTree（事前集計）

```sql
-- 集計メトリクスの維持用
CREATE TABLE market_stats_hourly (
    hour DateTime,
    market_id String,
    total_volume AggregateFunction(sum, UInt64),
    total_trades AggregateFunction(count, UInt32),
    unique_users AggregateFunction(uniq, String)
) ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (hour, market_id);

-- 集計データのクエリ
SELECT
    hour,
    market_id,
    sumMerge(total_volume) AS volume,
    countMerge(total_trades) AS trades,
    uniqMerge(unique_users) AS users
FROM market_stats_hourly
WHERE hour >= toStartOfHour(now() - INTERVAL 24 HOUR)
GROUP BY hour, market_id
ORDER BY hour DESC;
```

## クエリ最適化パターン

### 効率的なフィルタリング

```sql
-- 良い例: インデックス列を最初に使用
SELECT *
FROM markets_analytics
WHERE date >= '2025-01-01'
  AND market_id = 'market-123'
  AND volume > 1000
ORDER BY date DESC
LIMIT 100;

-- 悪い例: 非インデックス列を最初にフィルタ
SELECT *
FROM markets_analytics
WHERE volume > 1000
  AND market_name LIKE '%election%'
  AND date >= '2025-01-01';
```

### 集計

```sql
-- 良い例: ClickHouse固有の集計関数を使用
SELECT
    toStartOfDay(created_at) AS day,
    market_id,
    sum(volume) AS total_volume,
    count() AS total_trades,
    uniq(trader_id) AS unique_traders,
    avg(trade_size) AS avg_size
FROM trades
WHERE created_at >= today() - INTERVAL 7 DAY
GROUP BY day, market_id
ORDER BY day DESC, total_volume DESC;

-- パーセンタイルにはquantileを使用
SELECT
    quantile(0.50)(trade_size) AS median,
    quantile(0.95)(trade_size) AS p95,
    quantile(0.99)(trade_size) AS p99
FROM trades
WHERE created_at >= now() - INTERVAL 1 HOUR;
```

## データ挿入パターン

### バルク挿入（推奨）

```python
from clickhouse_connect import get_client
from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class Trade:
    id: str
    market_id: str
    user_id: str
    amount: float
    timestamp: datetime

def bulk_insert_trades(trades: List[Trade]) -> None:
    """トレードをバルク挿入"""
    client = get_client()

    # データを行のリストに変換
    rows = [
        [t.id, t.market_id, t.user_id, t.amount, t.timestamp]
        for t in trades
    ]

    client.insert(
        "trades",
        rows,
        column_names=["id", "market_id", "user_id", "amount", "timestamp"]
    )

# 使用例
trades = [
    Trade("1", "market-1", "user-1", 100.0, datetime.now()),
    Trade("2", "market-1", "user-2", 200.0, datetime.now()),
]
bulk_insert_trades(trades)
```

### 非同期バルク挿入

```python
from aiochclient import ChClient
from aiohttp import ClientSession

async def async_bulk_insert(trades: List[Trade]) -> None:
    """非同期でトレードをバルク挿入"""
    async with ClientSession() as session:
        client = ChClient(session)

        # INSERT文を構築
        values = ", ".join([
            f"('{t.id}', '{t.market_id}', '{t.user_id}', {t.amount}, '{t.timestamp}')"
            for t in trades
        ])

        await client.execute(f"""
            INSERT INTO trades (id, market_id, user_id, amount, timestamp)
            VALUES {values}
        """)
```

### バッファリング挿入

```python
from collections import deque
import asyncio
from typing import List, Any

class ClickHouseBuffer:
    """バッファリング挿入クラス"""

    def __init__(self, table: str, batch_size: int = 1000, flush_interval: float = 5.0):
        self.table = table
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.buffer: deque = deque()
        self._flush_task: asyncio.Task = None

    async def add(self, row: List[Any]) -> None:
        """行をバッファに追加"""
        self.buffer.append(row)

        if len(self.buffer) >= self.batch_size:
            await self.flush()

    async def flush(self) -> None:
        """バッファをフラッシュ"""
        if not self.buffer:
            return

        rows = list(self.buffer)
        self.buffer.clear()

        client = get_client()
        client.insert(self.table, rows)

    async def start_periodic_flush(self) -> None:
        """定期フラッシュを開始"""
        while True:
            await asyncio.sleep(self.flush_interval)
            await self.flush()

# 使用例
buffer = ClickHouseBuffer("trades", batch_size=1000, flush_interval=5.0)
asyncio.create_task(buffer.start_periodic_flush())

# データを追加
await buffer.add(["id-1", "market-1", "user-1", 100.0, datetime.now()])
```

## マテリアライズドビュー

### リアルタイム集計

```sql
-- 時間別統計のマテリアライズドビューを作成
CREATE MATERIALIZED VIEW market_stats_hourly_mv
TO market_stats_hourly
AS SELECT
    toStartOfHour(timestamp) AS hour,
    market_id,
    sumState(amount) AS total_volume,
    countState() AS total_trades,
    uniqState(user_id) AS unique_users
FROM trades
GROUP BY hour, market_id;

-- マテリアライズドビューのクエリ
SELECT
    hour,
    market_id,
    sumMerge(total_volume) AS volume,
    countMerge(total_trades) AS trades,
    uniqMerge(unique_users) AS users
FROM market_stats_hourly
WHERE hour >= now() - INTERVAL 24 HOUR
GROUP BY hour, market_id;
```

## パフォーマンス監視

### クエリパフォーマンス

```python
def get_slow_queries(client: Client, threshold_ms: int = 1000) -> List[dict]:
    """遅いクエリを取得"""
    result = client.query(f"""
        SELECT
            query_id,
            user,
            query,
            query_duration_ms,
            read_rows,
            read_bytes,
            memory_usage
        FROM system.query_log
        WHERE type = 'QueryFinish'
          AND query_duration_ms > {threshold_ms}
          AND event_time >= now() - INTERVAL 1 HOUR
        ORDER BY query_duration_ms DESC
        LIMIT 10
    """)
    return [dict(zip(result.column_names, row)) for row in result.result_rows]
```

### テーブル統計

```python
def get_table_sizes(client: Client) -> List[dict]:
    """テーブルサイズを取得"""
    result = client.query("""
        SELECT
            database,
            table,
            formatReadableSize(sum(bytes)) AS size,
            sum(rows) AS rows,
            max(modification_time) AS latest_modification
        FROM system.parts
        WHERE active
        GROUP BY database, table
        ORDER BY sum(bytes) DESC
    """)
    return [dict(zip(result.column_names, row)) for row in result.result_rows]
```

## 一般的な分析クエリ

### 時系列分析

```python
async def get_daily_active_users(client: Client, days: int = 30) -> List[dict]:
    """日次アクティブユーザーを取得"""
    result = client.query(f"""
        SELECT
            toDate(timestamp) AS date,
            uniq(user_id) AS daily_active_users
        FROM events
        WHERE timestamp >= today() - {days}
        GROUP BY date
        ORDER BY date
    """)
    return [dict(zip(result.column_names, row)) for row in result.result_rows]
```

### リテンション分析

```sql
SELECT
    signup_date,
    countIf(days_since_signup = 0) AS day_0,
    countIf(days_since_signup = 1) AS day_1,
    countIf(days_since_signup = 7) AS day_7,
    countIf(days_since_signup = 30) AS day_30
FROM (
    SELECT
        user_id,
        min(toDate(timestamp)) AS signup_date,
        toDate(timestamp) AS activity_date,
        dateDiff('day', signup_date, activity_date) AS days_since_signup
    FROM events
    GROUP BY user_id, activity_date
)
GROUP BY signup_date
ORDER BY signup_date DESC;
```

### ファネル分析

```sql
SELECT
    countIf(step = 'viewed_market') AS viewed,
    countIf(step = 'clicked_trade') AS clicked,
    countIf(step = 'completed_trade') AS completed,
    round(clicked / viewed * 100, 2) AS view_to_click_rate,
    round(completed / clicked * 100, 2) AS click_to_completion_rate
FROM (
    SELECT
        user_id,
        session_id,
        event_type AS step
    FROM events
    WHERE event_date = today()
)
GROUP BY session_id;
```

## データパイプラインパターン

### ETLパターン

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import pandas as pd

async def etl_pipeline():
    """Extract, Transform, Load パイプライン"""
    # 1. PostgreSQLから抽出
    pg_engine = create_engine(os.environ["DATABASE_URL"])
    with Session(pg_engine) as session:
        raw_data = pd.read_sql(
            "SELECT * FROM trades WHERE created_at >= NOW() - INTERVAL '1 hour'",
            session.connection()
        )

    # 2. 変換
    transformed = raw_data.assign(
        date=pd.to_datetime(raw_data["created_at"]).dt.date,
        hour=pd.to_datetime(raw_data["created_at"]).dt.floor("H")
    )

    # 3. ClickHouseにロード
    ch_client = get_client()
    ch_client.insert_df("trades_analytics", transformed)


# 定期実行（Celeryタスク等）
@celery_app.task
def run_etl():
    asyncio.run(etl_pipeline())
```

## FastAPIとの統合

```python
from fastapi import APIRouter, Depends
from clickhouse_connect.driver import Client

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

def get_ch_client() -> Client:
    """ClickHouseクライアント依存性"""
    return get_clickhouse_client()

@router.get("/daily-stats")
async def get_daily_stats(
    days: int = 7,
    client: Client = Depends(get_ch_client)
):
    """日次統計を取得"""
    result = client.query(f"""
        SELECT
            date,
            sum(volume) AS total_volume,
            count() AS total_trades,
            uniq(trader_id) AS unique_traders
        FROM markets_analytics
        WHERE date >= today() - {days}
        GROUP BY date
        ORDER BY date DESC
    """)

    return [
        dict(zip(result.column_names, row))
        for row in result.result_rows
    ]
```

## ベストプラクティス

### 1. パーティション戦略
- 時間でパーティション（通常は月または日）
- パーティションが多すぎないように（パフォーマンスに影響）
- パーティションキーにはDATE型を使用

### 2. 順序キー
- 最も頻繁にフィルタされる列を最初に配置
- カーディナリティを考慮（高カーディナリティを最初に）
- 順序は圧縮に影響

### 3. データ型
- 適切な最小型を使用（UInt32 vs UInt64）
- 繰り返し文字列にはLowCardinalityを使用
- カテゴリデータにはEnumを使用

### 4. 避けるべきこと
- SELECT *（列を指定する）
- FINAL（代わりにクエリ前にデータをマージ）
- 多すぎるJOIN（分析用に非正規化）
- 小さな頻繁な挿入（代わりにバッチ）

### 5. 監視
- クエリパフォーマンスを追跡
- ディスク使用量を監視
- マージ操作をチェック
- 遅いクエリログをレビュー

**覚えておくこと**: ClickHouseは分析ワークロードに優れています。クエリパターンに合わせてテーブルを設計し、挿入をバッチ化し、リアルタイム集計にはマテリアライズドビューを活用してください。
