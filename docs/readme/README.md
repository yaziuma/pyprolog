# PyProlog ドキュメント

PyProlog は純粋 Python で実装された Prolog インタープリターです。このドキュメント集は、実装されている機能の詳細と使用方法を説明しています。

## ドキュメント構成

### 📋 [実装機能概要](prolog_implementation_overview.md)

PyProlog の全体アーキテクチャと実装されている機能の概要を説明しています。

**内容:**

- プロジェクト全体構成
- コア機能（型システム、バインディング環境、演算子システム）
- パーサー（字句解析、構文解析）
- ランタイム（インタープリター、組み込み述語）
- CLI 機能
- 特徴的機能と設計思想

### 📖 [組み込み述語リファレンス](prolog_predicates_reference.md)

実装されている全ての組み込み述語の詳細リファレンスです。

**内容:**

- 型チェック述語（`var/1`, `atom/1`, `number/1`）
- 項操作述語（`functor/3`, `arg/3`, `=../2`）
- 動的述語管理（`asserta/1`, `assertz/1`）
- リスト処理（`member/2`, `append/3`）
- メタ述語（`findall/3`）
- 入出力（`get_char/1`）
- 算術・比較演算子
- 単一化・等価演算子
- 論理演算子と制御構造

### 🔧 [API 利用ガイド](prolog_api_guide.md)

Python から PyProlog を使用するための API ガイドです。

**内容:**

- 基本的な使用方法
- ランタイムの初期化とクエリ実行
- パーサーの直接使用
- Prolog 型の構築
- バインディング環境の操作
- エラーハンドリング
- I/O 管理
- 高度な使用例
- パフォーマンス考慮事項
- デバッグ手法

### ⚠️ [制限事項とエラーハンドリング](prolog_limitations_and_errors.md)

現在の制限事項、エラー種別、デバッグ手法について説明しています。

**内容:**

- 未実装機能（DCG、モジュールシステム、制約処理等）
- 部分実装機能
- エラー種別と対処法
- デバッグ手法
- パフォーマンスの制限
- 既知の問題と回避策

## クイックスタート

### 基本的な使用例

```python
from prolog import Runtime

# ランタイムを初期化
runtime = Runtime()

# ファクトとルールを追加
runtime.add_rule("likes(mary, food).")
runtime.add_rule("likes(mary, wine).")
runtime.add_rule("likes(john, wine).")
runtime.add_rule("likes(john, mary).")
runtime.add_rule("happy(X) :- likes(X, wine).")

# クエリを実行
results = runtime.query("likes(mary, X)")
for result in results:
    print(f"Mary likes {result['X']}")

# 複雑なクエリ
results = runtime.query("happy(X)")
for result in results:
    print(f"{result['X']} is happy")
```

### ファイルからの読み込み

```python
# Prologファイルを読み込み
runtime.consult("example.pl")

# REPLを起動
from prolog.cli.repl import run_repl
run_repl(runtime)
```

## アーキテクチャ概要

```
PyProlog
├── prolog/
│   ├── cli/           # CLI・REPL
│   ├── core/          # 型システム・演算子・バインディング
│   ├── parser/        # パーサー・スキャナー
│   ├── runtime/       # インタープリター・組み込み述語
│   └── util/          # ユーティリティ
├── tests/             # テストスイート
└── docs/              # ドキュメント
```

## 主要な特徴

### ✨ 統合演算子システム

演算子を型別に統一管理し、優先度・結合性を考慮した解析を実現。

### 🔄 モジュラー設計

各機能を独立したモジュールに分離し、拡張性を確保。

### 📊 包括的テスト

充実したテストスイートによる品質保証。

### 🔧 柔軟な I/O

抽象化された I/O ストリームによる柔軟な入出力処理。

### 🐍 Pure Python

外部依存なしの純粋 Python 実装。

## 実装済み機能一覧

### コア機能

- ✅ 基本的な Prolog 型（Atom、Variable、Number、Term、List）
- ✅ 単一化アルゴリズム
- ✅ バックトラック機能
- ✅ 変数束縛管理
- ✅ 演算子優先度処理

### 組み込み述語

- ✅ 型チェック（`var/1`, `atom/1`, `number/1`）
- ✅ 項操作（`functor/3`, `arg/3`, `=../2`）
- ✅ リスト処理（`member/2`, `append/3`）
- ✅ 動的述語（`asserta/1`, `assertz/1`）
- ✅ メタ述語（`findall/3`）
- ✅ 算術演算（`is/2`, `+`, `-`, `*`, `/`, `**`, `mod`）
- ✅ 比較演算（`=:=`, `=\=`, `<`, `=<`, `>`, `>=`）
- ✅ 論理演算（`=`, `\=`, `==`, `\==`）
- ✅ 制御構造（`,`, `;`, `\+`, `->`, `!`）

### パーサー

- ✅ 字句解析（トークン化）
- ✅ 構文解析（演算子優先度対応）
- ✅ エラーレポート

### CLI

- ✅ REPL（対話式実行環境）
- ✅ ファイル実行
- ✅ 結果表示

## 制限事項

### 未実装機能

- ❌ DCG（Definite Clause Grammar）
- ❌ モジュールシステム
- ❌ 制約処理（CLP）
- ❌ テーブル化・メモ化
- ❌ 例外処理（`catch/3`, `throw/1`）

### 部分実装

- ⚠️ 一部の組み込み述語（`bagof/3`, `setof/3`, `call/N`）
- ⚠️ ファイル I/O（基本機能のみ）
- ⚠️ 数学関数（三角関数、対数等）

## 開発とテスト

### テスト実行

```bash
# 全テスト実行
python -m pytest tests/

# 特定のテスト実行
python -m pytest tests/runtime/test_interpreter.py

# カバレッジ付きテスト
python -m pytest tests/ --cov=prolog
```

### 開発環境

```bash
# 依存関係インストール
pip install -r requirements-dev.txt

# リンター実行
ruff check prolog/
ruff format prolog/
```

## コントリビューション

PyProlog の改善に貢献する場合は、以下のガイドラインに従ってください：

1. イシューを作成して機能要求やバグ報告を行う
2. フォークしてブランチを作成
3. テストを追加・実行して品質を確保
4. プルリクエストを送信

## ライセンス

このプロジェクトは[LICENSE](../LICENSE)ファイルに記載されたライセンスの下で配布されています。

---

_より詳細な情報については、各ドキュメントを参照してください。質問や問題がある場合は、GitHub のイシューを作成してください。_
