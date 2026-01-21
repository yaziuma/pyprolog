---
description: pytest-playwrightでエンドツーエンドテストを生成・実行。テストジャーニーを作成し、テストを実行し、スクリーンショット/動画/トレースをキャプチャ。
---

# E2Eコマンド

このコマンドは**e2e-runner**エージェントを呼び出して、pytest-playwrightを使用してエンドツーエンドテストを生成、維持、実行します。

## このコマンドが行うこと

1. **テストジャーニー生成** - ユーザーフロー用のPlaywrightテストを作成
2. **E2Eテスト実行** - ブラウザ間でテストを実行
3. **アーティファクトキャプチャ** - 失敗時のスクリーンショット、動画、トレース
4. **結果生成** - HTMLレポートとJUnit XML
5. **不安定テスト特定** - 不安定なテストを隔離

## 使用タイミング

以下の場合に`/e2e`を使用:
- 重要なユーザージャーニーのテスト（ログイン、取引、支払い）
- マルチステップフローのエンドツーエンド検証
- UIインタラクションとナビゲーションのテスト
- フロントエンドとバックエンド間の統合検証
- 本番デプロイメントの準備

## 使用例

```
ユーザー: /e2e マーケット検索と表示フローをテスト

エージェント（e2e-runner）:
# E2Eテスト生成: マーケット検索と表示フロー

## 特定されたテストシナリオ

**ユーザージャーニー:** マーケット検索 → 結果表示 → マーケットクリック → 詳細表示

## 生成されたテストコード

```python
# tests/e2e/test_market_search.py
import pytest
from playwright.sync_api import Page, expect

class TestMarketSearchFlow:
    """マーケット検索と表示フローのE2Eテスト"""

    def test_user_can_search_and_view_market(self, page: Page):
        """ユーザーはマーケットを検索して詳細を表示できる"""
        # 1. マーケットページに移動
        page.goto("/markets")

        # ページ読み込みを確認
        expect(page).to_have_title("Markets")
        expect(page.locator("h1")).to_contain_text("Markets")

        # 2. 検索を実行
        search_input = page.locator('[data-testid="search-input"]')
        search_input.fill("election")
        search_input.press("Enter")

        # APIレスポンスを待機
        page.wait_for_response(
            lambda resp: "/api/markets/search" in resp.url and resp.status == 200
        )

        # 3. 検索結果を確認
        market_cards = page.locator('[data-testid="market-card"]')
        expect(market_cards.first).to_be_visible()
        assert market_cards.count() > 0

        # スクリーンショットを撮影
        page.screenshot(path="artifacts/search-results.png")

        # 4. 最初の結果をクリック
        first_title = market_cards.first.text_content()
        market_cards.first.click()

        # 5. マーケット詳細ページの読み込みを確認
        expect(page).to_have_url(re.compile(r"/markets/[\w-]+"))

        # 詳細要素を確認
        expect(page.locator('[data-testid="market-name"]')).to_be_visible()
        expect(page.locator('[data-testid="market-description"]')).to_be_visible()

        # 6. チャートのレンダリングを確認
        expect(page.locator('[data-testid="price-chart"]')).to_be_visible()

        # マーケット詳細のスクリーンショット
        page.screenshot(path="artifacts/market-details.png")

    def test_empty_search_shows_no_results(self, page: Page):
        """結果なしの検索で空状態を表示"""
        page.goto("/markets")

        search_input = page.locator('[data-testid="search-input"]')
        search_input.fill("xyznonexistentmarket123456")
        search_input.press("Enter")

        # 空状態を確認
        no_results = page.locator('[data-testid="no-results"]')
        expect(no_results).to_be_visible()
        expect(no_results).to_contain_text("結果が見つかりません")

    def test_clear_search_shows_all_markets(self, page: Page):
        """検索をクリアして再度すべてのマーケットを表示"""
        page.goto("/markets")

        market_cards = page.locator('[data-testid="market-card"]')
        initial_count = market_cards.count()

        # 検索を実行
        search_input = page.locator('[data-testid="search-input"]')
        search_input.fill("trump")
        search_input.press("Enter")
        page.wait_for_load_state("networkidle")

        # フィルタされた結果を確認
        filtered_count = market_cards.count()
        assert filtered_count < initial_count

        # 検索をクリア
        search_input.clear()
        search_input.press("Enter")
        page.wait_for_load_state("networkidle")

        # すべてのマーケットが再度表示
        final_count = market_cards.count()
        assert final_count == initial_count
```

## テスト実行

```bash
# 生成されたテストを実行
pytest tests/e2e/test_market_search.py -v

tests/e2e/test_market_search.py::TestMarketSearchFlow::test_user_can_search_and_view_market PASSED
tests/e2e/test_market_search.py::TestMarketSearchFlow::test_empty_search_shows_no_results PASSED
tests/e2e/test_market_search.py::TestMarketSearchFlow::test_clear_search_shows_all_markets PASSED

3 passed in 9.1s

生成されたアーティファクト:
- artifacts/search-results.png
- artifacts/market-details.png
```

✅ E2EテストスイートがCI/CD統合準備完了！
```

## Page Object Model

```python
# tests/e2e/pages/markets_page.py
from playwright.sync_api import Page, Locator

class MarketsPage:
    """マーケットページのPage Object"""

    def __init__(self, page: Page):
        self.page = page
        self.search_input = page.locator('[data-testid="search-input"]')
        self.market_cards = page.locator('[data-testid="market-card"]')
        self.no_results = page.locator('[data-testid="no-results"]')

    def goto(self):
        """マーケットページに移動"""
        self.page.goto("/markets")

    def search(self, query: str):
        """マーケットを検索"""
        self.search_input.fill(query)
        self.search_input.press("Enter")
        self.page.wait_for_load_state("networkidle")

    def get_market_count(self) -> int:
        """表示されているマーケット数を取得"""
        return self.market_cards.count()

    def click_first_market(self):
        """最初のマーケットをクリック"""
        self.market_cards.first.click()
```

## conftest.py設定

```python
# tests/e2e/conftest.py
import pytest
from playwright.sync_api import Page

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """ブラウザコンテキスト設定"""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "record_video_dir": "artifacts/videos",
    }

@pytest.fixture
def page(page: Page):
    """ページフィクスチャ（ベースURL設定）"""
    page.goto("http://localhost:8000")
    yield page
```

## クイックコマンド

```bash
# すべてのE2Eテストを実行
pytest tests/e2e/ -v

# ヘッドモードで実行（ブラウザを表示）
pytest tests/e2e/ --headed

# 特定のブラウザで実行
pytest tests/e2e/ --browser chromium
pytest tests/e2e/ --browser firefox
pytest tests/e2e/ --browser webkit

# テストをデバッグ
PWDEBUG=1 pytest tests/e2e/test_login.py -v

# トレースを有効化
pytest tests/e2e/ --tracing on

# スクリーンショットを撮影（失敗時のみ）
pytest tests/e2e/ --screenshot only-on-failure

# HTMLレポート生成
pytest tests/e2e/ --html=report.html

# 並列実行
pytest tests/e2e/ -n auto
```

## pytest.ini設定

```ini
[pytest]
addopts = -v --tb=short
testpaths = tests/e2e
markers =
    slow: marks tests as slow
    critical: marks tests as critical (must pass)
```

## ベストプラクティス

**すべきこと:**
- ✅ 保守性のためPage Object Modelを使用
- ✅ セレクタにdata-testid属性を使用
- ✅ 任意のタイムアウトではなくAPIレスポンスを待機
- ✅ 重要なユーザージャーニーをエンドツーエンドでテスト
- ✅ mainにマージ前にテストを実行
- ✅ テスト失敗時にアーティファクトをレビュー

**してはいけないこと:**
- ❌ 脆弱なセレクタを使用（CSSクラスは変更される可能性）
- ❌ 実装詳細をテスト
- ❌ 本番環境でテストを実行
- ❌ 不安定テストを無視
- ❌ すべてのエッジケースをE2Eでテスト（ユニットテストを使用）

## 関連エージェント

このコマンドは以下にある`e2e-runner`エージェントを呼び出します:
`~/.claude/agents/e2e-runner.md`
