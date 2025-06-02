# テスト品質指標と継続的テスト

## 6. テスト品質指標

### 6.1 カバレッジ目標

- **行カバレッジ**: 90%以上
- **分岐カバレッジ**: 85%以上
- **関数カバレッジ**: 95%以上

### 6.2 実行時間目標

- 単体テスト: 各テストクラス < 1 秒
- 統合テスト: 各テストクラス < 5 秒
- システムテスト: 全体 < 30 秒

## 7. 継続的テスト

### 7.1 自動化

- GitHub Actions での自動テスト実行
- プルリクエスト時の必須テスト
- 毎日のパフォーマンステスト

### 7.2 レポーティング

- カバレッジレポート
- パフォーマンストレンド
- 失敗テストの詳細ログ

### 7.3 テスト実行のベストプラクティス

#### 継続的インテグレーション設定

```yaml
# GitHub Actions の例
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      - name: Run tests with coverage
        run: |
          pytest --cov=prolog tests/
      - name: Upload coverage reports
        uses: codecov/codecov-action@v1
```

#### カバレッジ設定例

```ini
# .coveragerc
[run]
source = prolog
omit =
    */tests/*
    */venv/*
    setup.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

## 関連文書

- [システム概要とテスト戦略](./01_system_overview_and_strategy.md) - 全体戦略
- [テストデータとテスト実行環境](./03_test_data_and_environment.md) - 環境設定
- [テスト実装の優先順位](./05_implementation_priority.md) - 実装計画
