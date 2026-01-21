# テストカバレッジ

テストカバレッジを分析し、不足しているテストを生成:

1. カバレッジ付きでテストを実行:
   ```bash
   pytest --cov=app --cov-report=html --cov-report=json
   ```

2. カバレッジレポートを分析（htmlcov/index.html、coverage.json）

3. 80%カバレッジ閾値を下回るファイルを特定

4. カバレッジ不足の各ファイルについて:
   - テストされていないコードパスを分析
   - 関数用のユニットテストを生成
   - API用の統合テストを生成
   - 重要フロー用のE2Eテストを生成

5. 新しいテストが通ることを確認

6. 前後のカバレッジメトリクスを表示

7. プロジェクトが80%以上の全体カバレッジに到達することを確保

焦点:
- ハッピーパスシナリオ
- エラーハンドリング
- エッジケース（None、空リスト、空文字列）
- 境界条件

## コマンド

```bash
# 基本的なカバレッジ
pytest --cov=app

# HTMLレポート生成
pytest --cov=app --cov-report=html
# htmlcov/index.html をブラウザで開く

# 特定ファイルのカバレッジ
pytest --cov=app/services/user_service.py tests/test_user_service.py

# 最小カバレッジを強制
pytest --cov=app --cov-fail-under=80

# 未カバー行を表示
pytest --cov=app --cov-report=term-missing

# XMLレポート（CI用）
pytest --cov=app --cov-report=xml
```

## カバレッジ設定（pyproject.toml）

```toml
[tool.coverage.run]
source = ["app"]
omit = ["*/tests/*", "*/__pycache__/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
fail_under = 80
```

## カバレッジ優先度

**100%必須:**
- 財務計算
- 認証ロジック
- セキュリティ重要コード
- コアビジネスロジック

**80%以上:**
- サービス層
- APIエンドポイント
- ユーティリティ関数

**除外可能:**
- マイグレーションファイル
- 設定ファイル
- 型定義のみのファイル
