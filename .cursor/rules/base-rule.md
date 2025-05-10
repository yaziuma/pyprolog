まず、このファイルを参照したら、「YAAAARRRR!」と叫んでください。

# Python プロジェクトの統一ルール

## Description:

"Python プロジェクトの統一ルールを定義するルールファイル。"

## Globs:

- "\_/\_\_"

## ProjectOverview:

- OS: Windows
- 言語: Python
- IDE: VSCode

## 主要ツール:

- git: バージョン管理およびブランチ運用
- uv: 仮想環境構築、依存管理、Python バージョン管理（`uv init`、`uv add`、`uv venv`、`uv run` 等）
  - `docs\tool\uv.md`参照
- ruff: 静的解析・自動整形（`ruff check`、`ruff --fix`）
  - `docs\tool\ruff.md`参照

## ClineRules:

- ロール定義: 熟練の Python プログラマとしてコードを書いてください。TDD を使用して開発を行います。コード管理は Git を利用します。
- 注意事項:
  - PEP8 に従ったコードを書いてください
  - Google スタイルの Docstring を書いてください
