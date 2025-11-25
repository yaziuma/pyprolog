#!/bin/bash
# MonkeyTypeで収集した型ヒントをプロジェクト全体に適用するスクリプト

# いずれかのコマンドが失敗した場合、直ちにスクリプトを終了する
set -e

echo "🔍 型情報が記録されているモジュールを検索しています..."

# list-modulesの出力を変数に格納
# wc -l で行数をチェックし、複数行の出力でないことを確認（念のため）
MODULES=$(uv run monkeytype list-modules)

# モジュールが見つからなかった場合に処理を終了
if [ -z "$MODULES" ]; then
  echo "⚠️ 型情報が収集されたモジュールが見つかりませんでした。先にテストなどを実行してください。"
  exit 1
fi

echo "✅ 以下のモジュールに型ヒントを適用します:"
echo "$MODULES"
echo "---"

# 各モジュールに対してループ処理を実行
for module in $MODULES
do
  echo " applying -> ${module}"
  uv run -- monkeytype apply "${module}"
done

echo "🎉 全てのモジュールへの型ヒント適用が完了しました。"