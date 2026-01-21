# コードレビュー

コミットされていない変更の包括的なセキュリティと品質レビュー:

1. 変更されたファイルを取得: git diff --name-only HEAD

2. 変更された各ファイルについて以下をチェック:

**セキュリティ問題（CRITICAL）:**
- ハードコードされた認証情報、APIキー、トークン
- SQLインジェクション脆弱性（文字列連結クエリ）
- XSS脆弱性（Jinja2でのsafeフィルター使用）
- 入力検証の欠如（Pydantic未使用）
- 安全でない依存関係（pip-audit警告）
- パストラバーサルリスク
- 安全でないデシリアライゼーション（pickle）

**コード品質（HIGH）:**
- 50行を超える関数
- 800行を超えるファイル
- 4レベルを超えるネスト深度
- エラーハンドリングの欠如（try/except）
- print文（本番コードに残っている）
- TODO/FIXMEコメント（チケットなし）
- パブリックAPIのdocstring欠如
- 型注釈の欠如

**ベストプラクティス（MEDIUM）:**
- ミューテーションパターン（代わりにイミュータブルを使用）
- コード/コメントでの絵文字使用
- 新しいコードのテスト欠如
- PEP 8違反（Ruffで検出）

3. 以下を含むレポートを生成:
   - 重要度: CRITICAL、HIGH、MEDIUM、LOW
   - ファイル場所と行番号
   - 問題の説明
   - 修正提案

4. CRITICALまたはHIGH問題が見つかった場合はコミットをブロック

セキュリティ脆弱性のあるコードを承認しない！

## Python固有チェック

### セキュリティ
```python
# ❌ SQLインジェクション
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✓ SQLAlchemy ORM
user = session.query(User).filter(User.id == user_id).first()
```

### 型注釈
```python
# ❌ 型注釈なし
def process(data):
    return data.items()

# ✓ 型注釈あり
def process(data: dict[str, Any]) -> list[tuple[str, Any]]:
    return list(data.items())
```

### エラーハンドリング
```python
# ❌ 広すぎるexcept
try:
    result = do_something()
except:
    pass

# ✓ 具体的なexcept
try:
    result = do_something()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

## ツール

```bash
# セキュリティチェック
bandit -r app/
pip-audit

# 型チェック
mypy app/ --strict

# リント
ruff check app/

# すべて実行
bandit -r app/ && mypy app/ && ruff check app/
```
