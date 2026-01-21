---
name: tdd-workflow
description: 新機能の記述、バグ修正、コードリファクタリング時にこのスキルを使用。ユニット、統合、E2Eテストを含む80%以上のカバレッジでテスト駆動開発を強制。
---

# テスト駆動開発ワークフロー (Python Edition)

このスキルは、すべてのコード開発が包括的なテストカバレッジを伴うTDD原則に従うことを確保します。

## 有効化タイミング

- 新機能や機能の記述
- バグや問題の修正
- 既存コードのリファクタリング
- APIエンドポイントの追加
- 新しいコンポーネントの作成

## 基本原則

### 1. コードの前にテスト
常にテストを最初に書き、次にテストを通すためのコードを実装します。

### 2. カバレッジ要件
- 最低80%カバレッジ（ユニット + 統合 + E2E）
- すべてのエッジケースをカバー
- エラーシナリオをテスト
- 境界条件を検証

### 3. テストタイプ

#### ユニットテスト
- 個別の関数とユーティリティ
- Pydanticモデルの検証ロジック
- 純粋関数
- サービスロジック（モックを使用）

#### 統合テスト
- APIエンドポイント (FastAPI TestClient / AsyncClient)
- データベース操作 (SQLAlchemy + aiosqlite)
- サービス間相互作用
- 外部API呼び出し（VCR.pyやモックを使用）

#### E2Eテスト（Playwright Python）
- 重要なユーザーフロー
- 完全なワークフロー
- ブラウザ自動化
- UIインタラクション (htmx動作確認)

## TDDワークフローステップ

### ステップ1: ユーザージャーニーを記述
```
[役割]として、[アクション]したい、[利益]のために

例:
ユーザーとして、マーケットをセマンティックに検索したい、
正確なキーワードなしでも関連マーケットを見つけられるように。
```

### ステップ2: テストケースを生成
各ユーザージャーニーについて、包括的なテストケースを作成:

```python
import pytest
from app.services import market_service

@pytest.mark.asyncio
class TestSemanticSearch:
    async def test_returns_relevant_markets(self):
        """クエリに関連するマーケットを返す"""
        # テスト実装

    async def test_handles_empty_query(self):
        """空のクエリを適切に処理する"""
        # エッジケースをテスト

    async def test_fallback_when_redis_unavailable(self):
        """Redis利用不可時に部分文字列検索にフォールバック"""
        # フォールバック動作をテスト

    async def test_sorts_by_similarity(self):
        """類似度スコアで結果をソート"""
        # ソートロジックをテスト
```

### ステップ3: テストを実行（失敗するはず）
```bash
uv run pytest
# テストは失敗するはず - まだ実装していない
```

### ステップ4: コードを実装
テストを通すための最小限のコードを記述:

```python
# テストに導かれた実装
async def search_markets(query: str) -> list[Market]:
    # ここに実装
    pass
```

### ステップ5: テストを再実行
```bash
uv run pytest
# テストは今度は通るはず
```

### ステップ6: リファクタリング
テストを緑に保ちながらコード品質を改善:
- 重複を削除
- 命名を改善
- パフォーマンスを最適化
- 可読性を向上

### ステップ7: カバレッジを確認
```bash
uv run pytest --cov=app --cov-report=term-missing
# 80%以上のカバレッジが達成されたことを確認
```

## テストパターン

### ユニットテストパターン（pytest）
```python
import pytest
from app.utils import calculate_discount

def test_calculate_discount_valid():
    """正常な割引計算"""
    price = 100
    rate = 0.1
    assert calculate_discount(price, rate) == 90

def test_calculate_discount_invalid_rate():
    """無効な割引率でエラー"""
    with pytest.raises(ValueError):
        calculate_discount(100, 1.5)
```

### API統合テストパターン (FastAPI)
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_get_markets_success():
    """マーケットを正常に返す"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/markets")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)

@pytest.mark.asyncio
async def test_validate_query_params():
    """クエリパラメータを検証する"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/markets?limit=invalid")
    
    assert response.status_code == 422  # Validation Error

@pytest.mark.asyncio
async def test_handle_db_error(mocker):
    """データベースエラーを適切に処理する"""
    # データベース障害をモック
    mocker.patch("app.services.market_service.get_all", side_effect=Exception("DB Error"))
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/markets")
        
    assert response.status_code == 500
```

### E2Eテストパターン（Playwright Python）
```python
import pytest
from playwright.sync_api import Page, expect

def test_user_can_search_markets(page: Page):
    # マーケットページに移動
    page.goto("http://localhost:8000/")
    page.click('a[href="/markets"]')

    # ページが読み込まれたことを確認
    expect(page.locator('h1')).to_contain_text('マーケット')

    # マーケットを検索
    page.fill('input[placeholder="マーケットを検索"]', 'election')

    # デバウンスと結果を待機
    page.wait_for_timeout(600)

    # 検索結果が表示されることを確認
    results = page.locator('[data-testid="market-card"]')
    expect(results).to_have_count(5)

    # 結果に検索語が含まれることを確認
    first_result = results.first
    expect(first_result).to_contain_text('election', ignore_case=True)

    # ステータスでフィルタ
    page.click('button:has-text("アクティブ")')

    # フィルタされた結果を確認
    expect(results).to_have_count(3)
```

## テストファイル構成

```
app/
├── services/
│   ├── market_service.py
│   └── tests/
│       └── test_market_service.py   # ユニットテスト
├── routers/
│   ├── market_router.py
│   └── tests/
│       └── test_market_router.py    # 統合テスト
tests/
├── conftest.py                      # 共通フィクスチャ
└── e2e/
    ├── test_markets_e2e.py          # E2Eテスト
    └── test_auth_e2e.py
```

## 外部サービスのモック

### サービスモック (pytest-mock)
```python
def test_create_user(mocker):
    # Supabase呼び出しをモック
    mock_supabase = mocker.patch("app.services.auth.supabase_client")
    mock_supabase.table.return_value.insert.return_value.execute.return_value = {
        "data": [{"id": 1, "email": "test@example.com"}],
        "error": None
    }
    
    # テスト実行...
```

### Redisモック
```python
@pytest.fixture
def mock_redis(mocker):
    mock = mocker.patch("app.core.cache.redis_client")
    mock.get.return_value = None
    mock.set.return_value = True
    return mock
```

## テストカバレッジ検証

### カバレッジレポートを実行
```bash
uv run pytest --cov=app --cov-report=html
```

### 設定 (`pyproject.toml`)
```toml
[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q"
testpaths = ["tests"]

[tool.coverage.run]
source = ["app"]
branch = true

[tool.coverage.report]
fail_under = 80
show_missing = true
```

## 避けるべき一般的なテストミス

### ❌ 間違い: 実装詳細をテスト
```python
# 内部状態をテストしない
assert service._internal_cache["key"] == "value"
```

### ✅ 正しい: パブリックな振る舞いをテスト
```python
# 戻り値をテスト
assert service.get_value("key") == "value"
```

### ❌ 間違い: 脆弱なセレクタ (E2E)
```python
# 簡単に壊れる
page.click('.css-class-xyz')
```

### ✅ 正しい: セマンティックセレクタ (E2E)
```python
# 変更に強い
page.click('button:has-text("送信")')
page.click('[data-testid="submit-button"]')
```

### ❌ 間違い: テスト分離なし
```python
# テストが相互依存
global_id = None
def test_create():
    global global_id
    global_id = create()

def test_update():
    update(global_id) # 前のテストに依存
```

### ✅ 正しい: 独立したテスト
```python
# 各テストが独自のデータを設定
def test_create():
    # ...

def test_update():
    id = create_for_test() # 専用データを作成
    update(id)
```

## 継続的テスト

### 開発中のウォッチモード
```bash
uv run pytest -f  # pytest-watch プラグインなど
```

### プリコミットフック
```bash
# 各コミット前に実行
uv run pytest && uv run ruff check .
```

### CI/CD統合
```yaml
# GitHub Actions
- name: テストを実行
  run: uv run pytest --cov=app --cov-report=xml
- name: カバレッジをアップロード
  uses: codecov/codecov-action@v3
```

## ベストプラクティス

1. **テストを最初に書く** - 常にTDD
2. **テストごとに一つのアサート** - 単一の動作に焦点
3. **説明的なテスト名** - `test_should_return_error_when_invalid`
4. **Arrange-Act-Assert** - 明確なテスト構造
5. **外部依存関係をモック** - ユニットテストを分離
6. **エッジケースをテスト** - None, 空文字列, 境界値
7. **エラーパスをテスト** - 例外発生を確認
8. **テストを高速に保つ** - 非同期テストを活用
9. **テスト後のクリーンアップ** - フィクスチャのteardown活用
10. **カバレッジレポートをレビュー** - ギャップを特定

## 成功指標

- 80%以上のコードカバレッジを達成
- すべてのテストが通過（緑）
- スキップまたは無効化されたテストなし
- 高速なテスト実行
- E2Eテストが重要なユーザーフローをカバー
- テストが本番前にバグをキャッチ

---

**覚えておくこと**: テストはオプションではありません。自信を持ったリファクタリング、迅速な開発、本番の信頼性を可能にするセーフティネットです。
