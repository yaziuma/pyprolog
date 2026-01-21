# コードマップ更新

コードベース構造を分析し、アーキテクチャドキュメントを更新:

1. すべてのソースファイルをスキャンしてインポート、エクスポート、依存関係を確認
2. 以下の形式でトークンリーンなコードマップを生成:
   - docs/CODEMAPS/INDEX.md - 全体アーキテクチャ
   - docs/CODEMAPS/api.md - APIエンドポイント構造
   - docs/CODEMAPS/models.md - データベースモデル
   - docs/CODEMAPS/services.md - サービス層構造

3. 前バージョンからの差分パーセンテージを計算
4. 変更が30%を超える場合、更新前にユーザー承認を要求
5. 各コードマップに新鮮度タイムスタンプを追加
6. レポートを.reports/codemap-diff.txtに保存

分析にはPythonのastモジュールを使用。実装詳細ではなく高レベル構造に焦点を当てる。

## 分析スクリプト例

```python
import ast
from pathlib import Path

def analyze_module(filepath: Path) -> dict:
    """モジュールを解析してエクスポート・インポートを抽出"""
    with open(filepath) as f:
        tree = ast.parse(f.read())

    imports = []
    exports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
        elif isinstance(node, ast.FunctionDef):
            if not node.name.startswith('_'):
                exports.append(node.name)
        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith('_'):
                exports.append(node.name)

    return {"imports": imports, "exports": exports}
```

## コードマップ形式

```markdown
# [エリア] コードマップ

**最終更新：** YYYY-MM-DD
**エントリーポイント：** app/main.py

## アーキテクチャ

[コンポーネント関係のASCII図]

## 主要モジュール

| モジュール | 目的 | エクスポート | 依存関係 |
|--------|---------|---------|--------------|
| app/api/users.py | ユーザーAPI | router | services |
| app/services/user.py | ユーザーロジック | UserService | repositories |
```
