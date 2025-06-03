# PyProlog実装機能概要

## プロジェクト全体構成

### アーキテクチャ
PyPrologは以下の主要モジュールで構成されています：

```
prolog/
├── cli/           # コマンドライン・REPL機能
├── core/          # コア機能（型、演算子、バインディング等）
├── parser/        # パーサー・字句解析
├── runtime/       # ランタイム・インタープリター
└── util/          # ユーティリティ
```

## コア機能 (prolog/core)

### 型システム (types.py)
実装されているProlog型：

- **[`Atom`](prolog/core/types.py:16)**: 原子（例: `hello`, `world`）
- **[`Variable`](prolog/core/types.py:30)**: 変数（例: `X`, `Y`）
- **[`Number`](prolog/core/types.py:44)**: 数値（整数・浮動小数点）
- **[`String`](prolog/core/types.py:58)**: 文字列
- **[`Term`](prolog/core/types.py:72)**: 複合項（述語呼び出し）
- **[`ListTerm`](prolog/core/types.py:102)**: リスト構造
- **[`Rule`](prolog/core/types.py:155)**: ルール（ヘッド :- ボディ）
- **[`Fact`](prolog/core/types.py:174)**: ファクト

### バインディング環境 (binding_environment.py)
- **[`BindingEnvironment`](prolog/core/binding_environment.py:10)**: 変数束縛の管理
  - [`bind(var_name, value)`](prolog/core/binding_environment.py:15): 変数束縛
  - [`get_value(var_name)`](prolog/core/binding_environment.py:28): 値取得
  - [`unify(term1, term2)`](prolog/core/binding_environment.py:62): 単一化
  - [`merge_with(other)`](prolog/core/binding_environment.py:101): 環境マージ

### 演算子システム (operators.py)
#### 演算子分類
- **[`OperatorType`](prolog/core/operators.py:10)**: 演算子種別
  - `ARITHMETIC`: 算術演算子
  - `COMPARISON`: 比較演算子
  - `LOGICAL`: 論理演算子
  - `CONTROL`: 制御構造
  - `IO`: 入出力操作

#### 実装済み演算子

**算術演算子**：
- `**` (べき乗, 優先度200)
- `+`, `-` (単項, 優先度200)
- `*`, `/`, `//`, `mod` (優先度400)
- `+`, `-` (二項, 優先度500)

**比較演算子**：
- `=:=` (算術等価)
- `=\=` (算術非等価)
- `<`, `=<`, `>`, `>=` (大小比較)

**論理演算子**：
- `=` (単一化)
- `\=` (非単一化)
- `==`, `\==` (同一性)

### エラーハンドリング (errors.py)
- **PrologError**: 基底例外クラス
- **InterpreterError**: インタープリターエラー
- **ScannerError**: 字句解析エラー
- **ParserError**: 構文解析エラー
- **CutException**: カット処理用例外

## パーサー (prolog/parser)

### 字句解析 (scanner.py)
- **[`Scanner`](prolog/parser/scanner.py:14)**: トークン化処理
  - 演算子統合設計対応
  - [`scan_tokens()`](prolog/parser/scanner.py:64): トークン列生成

### 構文解析 (parser.py)
- **[`Parser`](prolog/parser/parser.py:16)**: 構文解析処理
  - 演算子優先度対応
  - [`parse()`](prolog/parser/parser.py:29): ルール・ファクト解析
  - [`_parse_expression_with_precedence()`](prolog/parser/parser.py:118): 式解析

### トークン管理
- **[`Token`](prolog/parser/token.py:1)**: トークン表現
- **[`TokenType`](prolog/parser/token_type.py:9)**: トークン種別
- **[`TokenTypeManager`](prolog/parser/token_type.py:43)**: 動的トークン管理

## ランタイム (prolog/runtime)

### インタープリター (interpreter.py)
- **[`Runtime`](prolog/runtime/interpreter.py:24)**: メインランタイム
  - **統合評価システム**: [`_build_unified_evaluator_system()`](prolog/runtime/interpreter.py:35)
  - **クエリ実行**: [`query(query_string)`](prolog/runtime/interpreter.py:321)
  - **ゴール実行**: [`execute(goal, env)`](prolog/runtime/interpreter.py:206)

### 組み込み述語 (builtins.py)
実装済み組み込み述語：

#### 型チェック述語
- **[`VarPredicate`](prolog/runtime/builtins.py:18)**: `var/1` - 変数判定
- **[`AtomPredicate`](prolog/runtime/builtins.py:27)**: `atom/1` - 原子判定
- **[`NumberPredicate`](prolog/runtime/builtins.py:36)**: `number/1` - 数値判定

#### 項操作述語
- **[`FunctorPredicate`](prolog/runtime/builtins.py:46)**: `functor/3` - 述語名・アリティ取得
- **[`ArgPredicate`](prolog/runtime/builtins.py:105)**: `arg/3` - 引数取得
- **[`UnivPredicate`](prolog/runtime/builtins.py:125)**: `=../2` - 項とリスト変換

#### 動的述語管理
- **[`DynamicAssertAPredicate`](prolog/runtime/builtins.py:195)**: `asserta/1` - ルール追加（先頭）
- **[`DynamicAssertZPredicate`](prolog/runtime/builtins.py:221)**: `assertz/1` - ルール追加（末尾）

#### リスト処理
- **[`MemberPredicate`](prolog/runtime/builtins.py:244)**: `member/2` - メンバー判定
- **[`AppendPredicate`](prolog/runtime/builtins.py:266)**: `append/3` - リスト結合

#### メタ述語
- **[`FindallPredicate`](prolog/runtime/builtins.py:325)**: `findall/3` - 解収集

#### 入出力
- **[`GetCharPredicate`](prolog/runtime/builtins.py:410)**: `get_char/1` - 文字入力

### 論理インタープリター (logic_interpreter.py)
- **[`LogicInterpreter`](prolog/runtime/logic_interpreter.py:22)**: 論理推論エンジン
  - **単一化**: [`unify(term1, term2, env)`](prolog/runtime/logic_interpreter.py:75)
  - **ゴール解決**: [`solve_goal(goal, env)`](prolog/runtime/logic_interpreter.py:192)
  - **変数リネーム**: [`_rename_variables()`](prolog/runtime/logic_interpreter.py:28)
  - **参照解決**: [`dereference(term, env)`](prolog/runtime/logic_interpreter.py:156)

### 数学インタープリター (math_interpreter.py)
- **[`MathInterpreter`](prolog/runtime/math_interpreter.py:12)**: 数学的評価エンジン
  - **式評価**: [`evaluate(expr, env)`](prolog/runtime/math_interpreter.py:18)
  - **二項演算**: [`evaluate_binary_op()`](prolog/runtime/math_interpreter.py:66)
  - **単項演算**: [`evaluate_unary_op()`](prolog/runtime/math_interpreter.py:112)
  - **比較演算**: [`evaluate_comparison_op()`](prolog/runtime/math_interpreter.py:131)

### I/O管理 (io_manager.py, io_streams.py)
- **[`IOManager`](prolog/runtime/io_manager.py:4)**: 入出力ストリーム管理
- **[`IOStream`](prolog/runtime/io_streams.py:11)**: 抽象ストリームインターフェース
- **[`ConsoleStream`](prolog/runtime/io_streams.py:51)**: コンソール入出力
- **[`StringStream`](prolog/runtime/io_streams.py:78)**: 文字列ベース入出力

## CLI (prolog/cli)

### REPL (repl.py)
- **[`run_repl(runtime)`](prolog/cli/repl.py:86)**: 対話式実行環境
- **[`display_variables()`](prolog/cli/repl.py:54)**: 結果表示

### プログラム実行 (prolog.py)
- **[`start(input_path)`](prolog/cli/prolog.py:11)**: ファイル実行
- **[`main()`](prolog/cli/prolog.py:33)**: エントリーポイント

## 特徴的機能

### 1. 統合演算子システム
演算子を型別に統一管理し、優先度・結合性を考慮した解析を実現。

### 2. モジュラー設計
各機能を独立したモジュールに分離し、拡張性を確保。

### 3. エラーハンドリング
階層化されたエラー型による詳細なエラー情報提供。

### 4. テスト充実
包括的なテストスイートによる品質保証。

### 5. I/Oストリーム抽象化
柔軟な入出力処理のためのストリーム抽象化。

## 現在の制限事項

1. **DCG (Definite Clause Grammar)**: 未実装
2. **モジュールシステム**: 未実装
3. **制約処理**: 未実装
4. **テーブル化・メモ化**: 未実装
5. **一部組み込み述語**: 部分実装

## 拡張性

本実装は以下の観点で拡張可能な設計：
- 新演算子の動的追加
- 組み込み述語の追加
- カスタムI/Oストリーム
- 新たなエラー型の追加

---

*このドキュメントは実装コードの調査に基づいて作成されています。詳細な API 仕様については各モジュールのソースコードを参照してください。*