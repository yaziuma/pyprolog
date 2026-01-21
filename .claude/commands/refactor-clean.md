# リファクタリングクリーン

テスト検証付きでデッドコードを安全に特定・削除:

1. デッドコード分析ツールを実行:
   - vulture: 未使用コード、関数、変数を発見
   - ruff: 未使用インポート、変数を発見（F401, F841）
   - pip-audit: 未使用/脆弱な依存関係を発見

2. .reports/dead-code-analysis.mdに包括的レポートを生成

3. 発見事項を重要度で分類:
   - SAFE: 未使用インポート、未使用ローカル変数
   - CAUTION: 動的インポートで使用される可能性
   - DANGER: 設定ファイル、メインエントリポイント、APIルート

4. 安全な削除のみを提案

5. 各削除前に:
   - 完全なテストスイートを実行（pytest）
   - テストが通ることを確認
   - 変更を適用
   - テストを再実行
   - テストが失敗した場合はロールバック

6. クリーンアップされた項目の要約を表示

まずテストを実行せずにコードを削除しない！

## コマンド

```bash
# 未使用コードを検出
vulture app/

# 最小信頼度を指定
vulture app/ --min-confidence 80

# 未使用インポートをチェック
ruff check app/ --select F401

# 未使用変数をチェック
ruff check app/ --select F841

# インポートを整理
isort app/

# 自動修正
ruff check app/ --fix

# テストを実行
pytest

# カバレッジレポート
pytest --cov=app --cov-report=html
```

## vultureホワイトリスト

誤検知を防ぐために`vulture_whitelist.py`を作成:

```python
# vulture_whitelist.py
# これらは使用されているが、vultureが検出できない

# FastAPIエンドポイント（デコレータ経由で使用）
from app.api import router  # noqa

# Pydanticモデル（バリデーションで使用）
from app.schemas import UserCreate  # noqa

# Alembicマイグレーション
from app.models import Base  # noqa

# pytest フィクスチャ
from tests.conftest import client  # noqa
```

使用方法:
```bash
vulture app/ vulture_whitelist.py
```
