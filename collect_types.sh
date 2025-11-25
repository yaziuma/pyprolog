#!/bin/bash
# MonkeyTypeで型情報を収集するスクリプト (pytestを実行)

# いずれかのコマンドが失敗した場合、直ちにスクリプトを終了する
set -e

DB_FILE="monkeytype.sqlite3"

# 既存のデータベースファイルがあれば削除し、常に新しい情報から始める
if [ -f "$DB_FILE" ]; then
  echo "🗑️ 古いデータベースファイル ($DB_FILE) を削除しています..."
  rm "$DB_FILE"
fi

echo "🧪 pytestを実行して型情報の収集を開始します..."

# MonkeyTypeを使ってテストを実行し、型情報を収集
uv run monkeytype run -m pytest tests

echo "✅ 型情報の収集が完了しました。$DB_FILE が作成/更新されました。"