# ドキュメント更新

信頼できる情報源からドキュメントを同期:

1. pyproject.tomlのscriptsセクションを読み取り
   - スクリプト参照テーブルを生成
   - コメントからの説明を含める

2. .env.exampleを読み取り
   - すべての環境変数を抽出
   - 目的と形式を文書化

3. 以下を含むdocs/CONTRIB.mdを生成:
   - 開発ワークフロー
   - 利用可能なスクリプト
   - 環境セットアップ
   - テスト手順

4. 以下を含むdocs/RUNBOOK.mdを生成:
   - デプロイメント手順
   - 監視とアラート
   - 一般的な問題と修正
   - ロールバック手順

5. 古いドキュメントを特定:
   - 90日以上変更されていないドキュメントを発見
   - 手動レビュー用にリスト化

6. 差分要約を表示

信頼できる情報源: pyproject.tomlと.env.example

## pyproject.toml構造例

```toml
[project]
name = "myapp"
version = "0.1.0"
description = "FastAPI application"

[project.scripts]
dev = "uvicorn app.main:app --reload"
test = "pytest"
lint = "ruff check app/"
format = "ruff format app/"
typecheck = "mypy app/"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=app"

[tool.ruff]
line-length = 88
select = ["E", "F", "I"]

[tool.mypy]
strict = true
```

## 生成されるドキュメント

### docs/CONTRIB.md

```markdown
# 開発者ガイド

## セットアップ

\`\`\`bash
# 仮想環境作成
python -m venv .venv
source .venv/bin/activate

# 依存関係インストール
pip install -e ".[dev]"

# 環境変数設定
cp .env.example .env
\`\`\`

## 利用可能なコマンド

| コマンド | 説明 |
|---------|------|
| `uvicorn app.main:app --reload` | 開発サーバー起動 |
| `pytest` | テスト実行 |
| `ruff check app/` | リントチェック |
| `mypy app/` | 型チェック |
```

### docs/RUNBOOK.md

```markdown
# 運用手順書

## デプロイメント

1. テスト実行: `pytest`
2. 型チェック: `mypy app/`
3. ビルド: `docker build -t myapp .`
4. デプロイ: `docker push myapp`

## ロールバック

\`\`\`bash
# 前のバージョンに戻す
docker pull myapp:previous
docker tag myapp:previous myapp:latest
\`\`\`
```
