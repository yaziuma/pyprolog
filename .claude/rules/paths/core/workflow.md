# Workflow

## コミット
- 形式: `<type>: <description>`
- type: feat/fix/refactor/docs/test/chore/perf/ci

## PR
- 変更内容 / 理由 / テスト方法を明記。
- `git diff [base]...HEAD` で全体確認。

# 省力化
- 広範囲のテスト実行(1ファイルを超えるもの)、grepによる機械的な調査、一括置換、といったデータ量に比較して思考が必要ない作業は、"必ず"Haikuモデルのサブエージェントを作成して作業を移譲、結果をまとめて報告させること。