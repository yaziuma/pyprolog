# ビルドと修正

mypy型エラーとRuffリントエラーを段階的に修正:

1. チェックを実行:
   ```bash
   uv run ruff check app/ --fix
   uv run mypy app/ --strict
   uv run ruff check app/
   ```

2. エラー出力を解析:
   - ファイル別にグループ化
   - 重要度でソート

3. 各エラーについて:
   - エラーコンテキストを表示（前後5行）
   - 問題を説明
   - 修正を提案
   - 修正を適用
   - チェックを再実行
   - エラーが解決されたことを確認

4. 以下の場合は停止:
   - 修正が新しいエラーを導入
   - 3回試行後も同じエラーが持続
   - ユーザーが一時停止を要求

5. 要約を表示:
   - 修正されたエラー
   - 残っているエラー
   - 導入された新しいエラー

安全のため一度に一つのエラーを修正！

## 一般的なエラータイプ

### mypy型エラー
```python
# error: Incompatible return type
def get_user(id: int) -> User:  # 修正前
    return None  # Noneを返している

def get_user(id: int) -> Optional[User]:  # 修正後
    return None

# error: Missing return type
def process(data):  # 修正前
    return data

def process(data: dict) -> dict:  # 修正後
    return data
```

### Ruffリントエラー
```python
# F401: 未使用インポート
from typing import List, Dict, Optional  # Listのみ使用
# 修正: from typing import List

# F841: 未使用変数
result = some_function()  # resultが使われていない
# 修正: _ = some_function() または削除

# E501: 行が長すぎる
# 修正: 行を分割またはruff format実行
```

## コマンド

```bash
# 自動修正可能なエラーを修正 (推奨)
uv run ruff check app/ --fix

# 型チェック
uv run mypy app/ --strict

# リントチェック
uv run ruff check app/

# フォーマット
uv run ruff format app/

# すべてを一度に実行
uv run ruff check app/ --fix && uv run mypy app/ --strict && uv run ruff format app/
```