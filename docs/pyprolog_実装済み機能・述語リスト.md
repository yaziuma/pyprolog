# PyProlog 実装済み機能・述語リスト

## 概要

このドキュメントは、pyprolog プロジェクトの実装済み機能と述語の詳細なリストです。pyprolog は、Python で実装されたシンプルな Prolog インタープリターです。

## 目次

1. [コアコンポーネント](#コアコンポーネント)
2. [データ型](#データ型)
3. [組み込み述語](#組み込み述語)
4. [演算子](#演算子)
5. [パーサー機能](#パーサー機能)
6. [ランタイム機能](#ランタイム機能)
7. [入出力機能](#入出力機能)
8. [使用例](#使用例)

## コアコンポーネント

### 主要クラス

- **[`Runtime`](../pyprolog/runtime/interpreter.py:32)** - メインインタープリタークラス
- **[`Parser`](../pyprolog/parser/parser.py)** - Prolog コードパーサー
- **[`Scanner`](../pyprolog/parser/scanner.py)** - 字句解析器
- **[`LogicInterpreter`](../pyprolog/runtime/logic_interpreter.py)** - 論理推論エンジン
- **[`MathInterpreter`](../pyprolog/runtime/math_interpreter.py:12)** - 算術評価エンジン

### エラーハンドリング

- **[`PrologError`](../pyprolog/core/errors.py)** - 基本例外クラス
- **[`InterpreterError`](../pyprolog/core/errors.py)** - インタープリターエラー
- **[`ScannerError`](../pyprolog/core/errors.py)** - 字句解析エラー
- **[`ParserError`](../pyprolog/core/errors.py)** - 構文解析エラー
- **[`CutException`](../pyprolog/core/errors.py)** - カット例外

## データ型

### 基本データ型

| 型     | クラス                                      | 説明                                        |
| ------ | ------------------------------------------- | ------------------------------------------- | ----- |
| アトム | [`Atom`](../pyprolog/core/types.py:16)      | 文字列定数（例：`hello`, `world`）          |
| 変数   | [`Variable`](../pyprolog/core/types.py:30)  | 論理変数（例：`X`, `Y`, `_Var`）            |
| 数値   | [`Number`](../pyprolog/core/types.py:44)    | 整数・浮動小数点（例：`42`, `3.14`）        |
| 文字列 | [`String`](../pyprolog/core/types.py:58)    | 文字列リテラル（例：`'hello'`）             |
| 項     | [`Term`](../pyprolog/core/types.py:72)      | 複合項（例：`f(a, b)`, `person(john, 25)`） |
| リスト | [`ListTerm`](../pyprolog/core/types.py:102) | リスト構造（例：`[1, 2, 3]`, `[H            | T]`） |

### 論理構造

| 型       | クラス                                  | 説明                                            |
| -------- | --------------------------------------- | ----------------------------------------------- |
| ファクト | [`Fact`](../pyprolog/core/types.py:174) | 単純な事実（例：`likes(mary, wine).`）          |
| ルール   | [`Rule`](../pyprolog/core/types.py:155) | 論理ルール（例：`happy(X) :- likes(X, wine).`） |

## 組み込み述語

### 型検査述語

| 述語       | アリティ | 実装クラス                                              | 説明                         |
| ---------- | -------- | ------------------------------------------------------- | ---------------------------- |
| `var/1`    | 1        | [`VarPredicate`](../pyprolog/runtime/builtins.py:26)    | 引数が変数かどうかをテスト   |
| `atom/1`   | 1        | [`AtomPredicate`](../pyprolog/runtime/builtins.py:38)   | 引数がアトムかどうかをテスト |
| `number/1` | 1        | [`NumberPredicate`](../pyprolog/runtime/builtins.py:50) | 引数が数値かどうかをテスト   |

### 項操作述語

| 述語        | アリティ | 実装クラス                                               | 説明                                |
| ----------- | -------- | -------------------------------------------------------- | ----------------------------------- |
| `functor/3` | 3        | [`FunctorPredicate`](../pyprolog/runtime/builtins.py:62) | 項のファンクタとアリティを取得/構築 |
| `arg/3`     | 3        | [`ArgPredicate`](../pyprolog/runtime/builtins.py:146)    | 項の指定位置の引数を取得            |
| `=../2`     | 2        | [`UnivPredicate`](../pyprolog/runtime/builtins.py:179)   | 項とリストの相互変換（univ）        |

### 動的述語操作

| 述語        | アリティ | 実装クラス                                                       | 説明                       |
| ----------- | -------- | ---------------------------------------------------------------- | -------------------------- |
| `asserta/1` | 1        | [`DynamicAssertAPredicate`](../pyprolog/runtime/builtins.py:283) | 知識ベースの先頭に節を追加 |
| `assertz/1` | 1        | [`DynamicAssertZPredicate`](../pyprolog/runtime/builtins.py:373) | 知識ベースの末尾に節を追加 |
| `retract/1` | 1        | [`DynamicRetractPredicate`](../pyprolog/runtime/builtins.py:724) | 知識ベースから節を削除     |

### リスト操作述語

| 述語       | アリティ | 実装クラス                                               | 説明                         |
| ---------- | -------- | -------------------------------------------------------- | ---------------------------- |
| `member/2` | 2        | [`MemberPredicate`](../pyprolog/runtime/builtins.py:463) | リストのメンバーシップテスト |
| `append/3` | 3        | [`AppendPredicate`](../pyprolog/runtime/builtins.py:491) | リストの連結                 |

### メタ述語

| 述語        | アリティ | 実装クラス                                                | 説明                             |
| ----------- | -------- | --------------------------------------------------------- | -------------------------------- |
| `findall/3` | 3        | [`FindallPredicate`](../pyprolog/runtime/builtins.py:556) | 解の収集（bagof/setof の簡易版） |

### 入出力述語

| 述語         | アリティ | 実装クラス                                                | 説明                                    |
| ------------ | -------- | --------------------------------------------------------- | --------------------------------------- |
| `get_char/1` | 1        | [`GetCharPredicate`](../pyprolog/runtime/builtins.py:659) | 現在の入力ストリームから 1 文字読み取り |

## 演算子

### 算術演算子

| 演算子 | アリティ | 優先度 | 結合性 | 説明         |
| ------ | -------- | ------ | ------ | ------------ |
| `**`   | 2        | 200    | 右     | べき乗       |
| `-`    | 1        | 200    | なし   | 単項マイナス |
| `+`    | 1        | 200    | なし   | 単項プラス   |
| `*`    | 2        | 400    | 左     | 乗算         |
| `/`    | 2        | 400    | 左     | 除算         |
| `//`   | 2        | 400    | 左     | 整数除算     |
| `mod`  | 2        | 400    | 左     | 剰余         |
| `+`    | 2        | 500    | 左     | 加算         |
| `-`    | 2        | 500    | 左     | 減算         |

### 比較演算子

| 演算子 | アリティ | 優先度 | 説明       |
| ------ | -------- | ------ | ---------- |
| `=:=`  | 2        | 700    | 算術等価   |
| `=\\=` | 2        | 700    | 算術非等価 |
| `<`    | 2        | 700    | 未満       |
| `=<`   | 2        | 700    | 以下       |
| `>`    | 2        | 700    | 超過       |
| `>=`   | 2        | 700    | 以上       |

### 論理演算子

| 演算子 | アリティ | 優先度 | 説明             |
| ------ | -------- | ------ | ---------------- |
| `=`    | 2        | 700    | 単一化           |
| `\\=`  | 2        | 700    | 単一化失敗       |
| `==`   | 2        | 700    | 項等価           |
| `\\==` | 2        | 700    | 項非等価         |
| `is`   | 2        | 700    | 算術評価と単一化 |

### 制御演算子

| 演算子 | アリティ | 優先度 | 説明        |
| ------ | -------- | ------ | ----------- |
| `!`    | 0        | 1200   | カット      |
| `->`   | 2        | 1050   | if-then     |
| `;`    | 2        | 1100   | OR（選択）  |
| `,`    | 2        | 1000   | AND（連言） |

### 入出力演算子

| 演算子  | アリティ | 説明     |
| ------- | -------- | -------- |
| `write` | 1        | 項の出力 |
| `nl`    | 0        | 改行出力 |

## パーサー機能

### サポートする構文要素

- **アトム**: 小文字で始まる識別子、引用符で囲まれた文字列
- **変数**: 大文字または`_`で始まる識別子
- **数値**: 整数、浮動小数点数
- **複合項**: `functor(arg1, arg2, ...)`
- **リスト**: `[element1, element2, ...]`, `[Head|Tail]`
- **演算子**: 中置、前置、後置演算子
- **コメント**: `%`行コメント、`/* */`ブロックコメント

### トークン型

定義されたトークン型は[`TokenType`](../pyprolog/parser/token_type.py)に列挙されています。

## ランタイム機能

### 主要メソッド

| メソッド                                                                  | 説明                                   |
| ------------------------------------------------------------------------- | -------------------------------------- |
| [`Runtime.query(query_string)`](../pyprolog/runtime/interpreter.py:514)   | クエリ文字列を実行し、解のリストを返す |
| [`Runtime.add_rule(rule_string)`](../pyprolog/runtime/interpreter.py:610) | ルール文字列を知識ベースに追加         |
| [`Runtime.consult(filename)`](../pyprolog/runtime/interpreter.py:636)     | Prolog ファイルを読み込む              |
| [`Runtime.execute(goal, env)`](../pyprolog/runtime/interpreter.py:317)    | ゴールを環境で実行し、解を生成         |

### 単一化アルゴリズム

[`LogicInterpreter`](../pyprolog/runtime/logic_interpreter.py)クラスで実装された単一化機能：

- 変数と項の単一化
- 複合項同士の単一化
- occurs check による無限ループ防止

### バックトラッキング

- 選択点の管理
- 解の探索順序制御
- カットによる探索剪定

## 入出力機能

### IOManager

[`IOManager`](../pyprolog/runtime/io_manager.py)クラスが入出力を管理：

- 標準入力/出力
- ファイル入出力
- ストリーム管理

### サポート機能

- 文字単位入力
- 項の出力
- 改行制御

## 使用例

### 基本的な使用法

```python
from pyprolog import Runtime

# ランタイム初期化
runtime = Runtime()

# ファクト追加
runtime.add_rule("likes(mary, wine).")
runtime.add_rule("likes(john, wine).")

# ルール追加
runtime.add_rule("happy(X) :- likes(X, wine).")

# クエリ実行
results = runtime.query("happy(X)")
for result in results:
    print(f"X = {result['X']}")
```

### 算術演算例

```python
# 算術計算
results = runtime.query("X is 3 + 4 * 2")
print(f"X = {results[0]['X']}")  # X = 11

# 比較演算
results = runtime.query("5 > 3")
print(f"Success: {len(results) > 0}")  # Success: True
```

### リスト操作例

```python
# member述語
results = runtime.query("member(X, [1, 2, 3])")
for result in results:
    print(f"X = {result['X']}")  # X = 1, X = 2, X = 3

# append述語
results = runtime.query("append([1, 2], [3, 4], L)")
print(f"L = {results[0]['L']}")  # L = [1, 2, 3, 4]
```

## テスト仕様

### テストカバレッジ

pyprolog は以下のエリアで包括的なテストを提供：

- **コア機能**: [`tests/core/`](../tests/core/)
- **パーサー**: [`tests/parser/`](../tests/parser/)
- **ランタイム**: [`tests/runtime/`](../tests/runtime/)
- **統合テスト**: [`tests/integration/`](../tests/integration/)

### 主要テストケース

- 算術演算の境界値テスト
- リスト操作の総合テスト
- 動的述語操作のテスト
- 単一化アルゴリズムのテスト
- 再帰ルールのテスト
- メタ述語のテスト

## 制限事項と今後の拡張予定

### 現在の制限事項

- DCG（Definite Clause Grammar）未サポート
- モジュールシステム未実装
- 一部の標準述語未実装（`bagof/3`, `setof/3`など）
- 制約論理プログラミング（CLP）未サポート

### 将来の拡張候補

- より多くの組み込み述語
- デバッグ機能の強化
- パフォーマンス最適化
- 標準 Prolog 互換性の向上

---

**注意**: このドキュメントは実装状況に基づいて作成されています。詳細な仕様や使用方法については、対応するソースコードとテストケースを参照してください。
