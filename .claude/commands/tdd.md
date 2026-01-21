---
description: テスト駆動開発ワークフローを強制。インターフェースを足場化し、最初にテストを生成し、次に通すための最小限のコードを実装。80%以上のカバレッジを確保。
---

# TDDコマンド

このコマンドは**tdd-guide**エージェントを呼び出して、テスト駆動開発方法論を強制します。

## このコマンドが行うこと

1. **インターフェースの足場化** - 最初に型/Pydanticモデルを定義
2. **最初にテストを生成** - 失敗するテストを書く（RED）
3. **最小限のコードを実装** - 通すのに十分なだけ書く（GREEN）
4. **リファクタリング** - テストを緑に保ちながらコードを改善（REFACTOR）
5. **カバレッジを確認** - 80%以上のテストカバレッジを確保

## 使用タイミング

以下の場合に`/tdd`を使用：
- 新機能の実装
- 新しい関数/サービスの追加
- バグの修正（最初にバグを再現するテストを書く）
- 既存コードのリファクタリング
- 重要なビジネスロジックの構築

## 動作方法

tdd-guideエージェントは以下を行います：

1. **インターフェースを定義**入力/出力用（Pydanticモデル）
2. **失敗するテストを書く**（コードがまだ存在しないため）
3. **テストを実行**し、正しい理由で失敗することを確認
4. **最小限の実装を書く**テストを通すため
5. **テストを実行**し、通ることを確認
6. **コードをリファクタリング**テストを緑に保ちながら
7. **カバレッジをチェック**し、80%未満の場合はテストを追加

## TDDサイクル

```
RED → GREEN → REFACTOR → 繰り返し

RED:      失敗するテストを書く
GREEN:    通すための最小限のコードを書く
REFACTOR: テストを通したままコードを改善
繰り返し:   次の機能/シナリオ
```

## 使用例

```
ユーザー：/tdd マーケット流動性スコアを計算する関数が必要

エージェント（tdd-guide）：
# TDDセッション：マーケット流動性スコア計算機

## ステップ1：インターフェースを定義（足場化）

```python
# app/schemas/market.py
from pydantic import BaseModel
from datetime import datetime

class MarketData(BaseModel):
    total_volume: float
    bid_ask_spread: float
    active_traders: int
    last_trade_time: datetime

# app/services/liquidity.py
def calculate_liquidity_score(market: MarketData) -> float:
    """マーケットの流動性スコアを計算（0-100）"""
    raise NotImplementedError()
```

## ステップ2：失敗するテストを書く（RED）

```python
# tests/test_liquidity.py
import pytest
from datetime import datetime, timedelta
from app.schemas.market import MarketData
from app.services.liquidity import calculate_liquidity_score

class TestCalculateLiquidityScore:
    """流動性スコア計算のテスト"""

    def test_high_liquidity_market_returns_high_score(self):
        """流動性の高いマーケットに高いスコアを返すべき"""
        market = MarketData(
            total_volume=100000,
            bid_ask_spread=0.01,
            active_traders=500,
            last_trade_time=datetime.now()
        )

        score = calculate_liquidity_score(market)

        assert score > 80
        assert score <= 100

    def test_low_liquidity_market_returns_low_score(self):
        """流動性の低いマーケットに低いスコアを返すべき"""
        market = MarketData(
            total_volume=100,
            bid_ask_spread=0.5,
            active_traders=2,
            last_trade_time=datetime.now() - timedelta(days=1)
        )

        score = calculate_liquidity_score(market)

        assert score < 30
        assert score >= 0

    def test_handles_edge_case_zero_volume(self):
        """エッジケース：ゼロボリューム"""
        market = MarketData(
            total_volume=0,
            bid_ask_spread=0,
            active_traders=0,
            last_trade_time=datetime.now()
        )

        score = calculate_liquidity_score(market)

        assert score == 0
```

## ステップ3：テストを実行 - 失敗を確認

```bash
pytest tests/test_liquidity.py -v

FAILED tests/test_liquidity.py::TestCalculateLiquidityScore::test_high_liquidity_market_returns_high_score
    NotImplementedError

1 failed, 0 passed
```

✅ テストが期待通りに失敗。実装準備完了。

## ステップ4：最小限のコードを実装（GREEN）

```python
# app/services/liquidity.py
from datetime import datetime
from app.schemas.market import MarketData

def calculate_liquidity_score(market: MarketData) -> float:
    """マーケットの流動性スコアを計算（0-100）"""
    # ゼロボリュームのエッジケースを処理
    if market.total_volume == 0:
        return 0.0

    # コンポーネントスコアを計算（0-100スケール）
    volume_score = min(market.total_volume / 1000, 100)
    spread_score = max(100 - (market.bid_ask_spread * 1000), 0)
    trader_score = min(market.active_traders / 10, 100)

    # 最近のアクティビティボーナス
    hours_since_last_trade = (
        datetime.now() - market.last_trade_time
    ).total_seconds() / 3600
    recency_score = max(100 - (hours_since_last_trade * 10), 0)

    # 加重平均
    score = (
        volume_score * 0.4 +
        spread_score * 0.3 +
        trader_score * 0.2 +
        recency_score * 0.1
    )

    return min(max(score, 0), 100)  # 0-100にクランプ
```

## ステップ5：テストを実行 - 通過を確認

```bash
pytest tests/test_liquidity.py -v

PASSED tests/test_liquidity.py::TestCalculateLiquidityScore::test_high_liquidity_market_returns_high_score
PASSED tests/test_liquidity.py::TestCalculateLiquidityScore::test_low_liquidity_market_returns_low_score
PASSED tests/test_liquidity.py::TestCalculateLiquidityScore::test_handles_edge_case_zero_volume

3 passed
```

✅ すべてのテストが通過！

## ステップ6：リファクタリング（改善）

```python
# app/services/liquidity.py - 定数とより良い可読性でリファクタリング
from datetime import datetime
from app.schemas.market import MarketData

WEIGHTS = {
    "VOLUME": 0.4,
    "SPREAD": 0.3,
    "TRADERS": 0.2,
    "RECENCY": 0.1,
}

SCALE_FACTORS = {
    "VOLUME": 1000,
    "SPREAD": 1000,
    "TRADERS": 10,
    "RECENCY_PENALTY": 10,
}

def _clamp(value: float, min_val: float, max_val: float) -> float:
    """値を範囲内にクランプ"""
    return min(max(value, min_val), max_val)

def calculate_liquidity_score(market: MarketData) -> float:
    """マーケットの流動性スコアを計算（0-100）"""
    if market.total_volume == 0:
        return 0.0

    volume_score = min(market.total_volume / SCALE_FACTORS["VOLUME"], 100)
    spread_score = _clamp(100 - (market.bid_ask_spread * SCALE_FACTORS["SPREAD"]), 0, 100)
    trader_score = min(market.active_traders / SCALE_FACTORS["TRADERS"], 100)

    hours_since_last_trade = (
        datetime.now() - market.last_trade_time
    ).total_seconds() / 3600
    recency_score = _clamp(100 - (hours_since_last_trade * SCALE_FACTORS["RECENCY_PENALTY"]), 0, 100)

    weighted_score = (
        volume_score * WEIGHTS["VOLUME"] +
        spread_score * WEIGHTS["SPREAD"] +
        trader_score * WEIGHTS["TRADERS"] +
        recency_score * WEIGHTS["RECENCY"]
    )

    return _clamp(weighted_score, 0, 100)
```

## ステップ7：テストがまだ通ることを確認

```bash
pytest tests/test_liquidity.py -v

3 passed
```

✅ リファクタリング完了、テストはまだ通過！

## ステップ8：カバレッジをチェック

```bash
pytest --cov=app/services/liquidity tests/test_liquidity.py

Name                          Stmts   Miss  Cover
-------------------------------------------------
app/services/liquidity.py        20      0   100%

カバレッジ：100% ✅（目標：80%）
```

✅ TDDセッション完了！
```

## TDDベストプラクティス

**すべきこと：**
- ✅ 実装前に最初にテストを書く
- ✅ テストを実行し、実装前に失敗することを確認
- ✅ テストを通すための最小限のコードを書く
- ✅ テストが緑になった後のみリファクタリング
- ✅ エッジケースとエラーシナリオを追加
- ✅ 80%以上のカバレッジを目指す（重要なコードは100%）

**すべきでないこと：**
- ❌ テスト前に実装を書く
- ❌ 各変更後のテスト実行をスキップ
- ❌ 一度に多すぎるコードを書く
- ❌ 失敗するテストを無視
- ❌ 実装詳細をテスト（動作をテスト）
- ❌ すべてをモック（統合テストを優先）

## 含めるべきテストタイプ

**単体テスト**（関数レベル）：
- ハッピーパスシナリオ
- エッジケース（None、空リスト、最大値）
- エラー条件
- 境界値

**統合テスト**（コンポーネントレベル）：
- APIエンドポイント（TestClient使用）
- データベース操作（テストDB使用）
- 外部サービス呼び出し

**E2Eテスト**（`/e2e`コマンドを使用）：
- 重要なユーザーフロー
- 複数ステップのプロセス
- フルスタック統合

## カバレッジ要件

- **80%最小**すべてのコード用
- **100%必須**以下用：
  - 財務計算
  - 認証ロジック
  - セキュリティ重要コード
  - コアビジネスロジック

## 重要な注意事項

**必須**：テストは実装前に書かれなければなりません。TDDサイクルは：

1. **RED** - 失敗するテストを書く
2. **GREEN** - 通すために実装
3. **REFACTOR** - コードを改善

REDフェーズをスキップしてはいけません。テスト前にコードを書いてはいけません。

## 他のコマンドとの統合

- 最初に`/plan`を使用して何を構築するかを理解
- `/tdd`を使用してテスト付きで実装
- ビルドエラーが発生した場合は`/build-fix`を使用
- 実装をレビューするために`/code-review`を使用
- カバレッジを確認するために`/test-coverage`を使用

## 関連エージェント

このコマンドは以下にあるtdd-guideエージェントを呼び出します：
`~/.claude/agents/tdd-guide.md`

また、以下のtdd-workflowスキルを参照できます：
`~/.claude/skills/tdd-workflow/`
