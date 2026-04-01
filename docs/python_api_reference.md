# PyProlog Python API リファレンス

## 概要
このドキュメントは、PyProlog を Python ライブラリとして使用するための詳細な API リファレンスです。
Prolog 言語としての機能や述語については、[実装済み機能・述語リスト](pyprolog_実装済み機能・述語リスト.md)を参照してください。

## コアコンポーネント

### 主要クラス

* **[`Runtime`](../pyprolog/runtime/interpreter.py)** - メインインタープリタークラス
* **[`Parser`](../pyprolog/parser/parser.py)** - Prolog コードパーサー
* **[`Scanner`](../pyprolog/parser/scanner.py)** - 字句解析器
* **[`LogicInterpreter`](../pyprolog/runtime/logic_interpreter.py)** - 論理推論エンジン
* **[`MathInterpreter`](../pyprolog/runtime/math_interpreter.py)** - 算術評価エンジン

### エラーハンドリング

* **[`PrologError`](../pyprolog/core/errors.py)** - 基本例外クラス
* **[`InterpreterError`](../pyprolog/core/errors.py)** - インタープリターエラー
* **[`ScannerError`](../pyprolog/core/errors.py)** - 字句解析エラー
* **[`ParserError`](../pyprolog/core/errors.py)** - 構文解析エラー
* **[`CutException`](../pyprolog/core/errors.py)** - カット例外
* **[`UnsafeModeError`](../pyprolog/core/errors.py)** - unsafe モード未有効で外部実行機能を使用した場合の例外
* **[`ScriptRegistrationError`](../pyprolog/core/errors.py)** - スクリプト登録時の検証エラー
* **[`InvalidCliArgsError`](../pyprolog/core/errors.py)** - `py_call/5` の引数列が不正な場合の例外
* **[`ScriptNotRegisteredError`](../pyprolog/core/errors.py)** - 未登録スクリプト参照時の例外
* **[`ExternalExecutionError`](../pyprolog/core/errors.py)** - 外部Python実行時の環境エラー

## データ型 (Python クラス)

PyProlog の内部データ構造を表すクラス群です。AST 操作や結果の解析に使用します。

| 型 | クラス | 説明 |
| --- | --- | --- |
| アトム | [`Atom`](../pyprolog/core/types.py) | 文字列定数（例：`hello`, `world`） |
| 変数 | [`Variable`](../pyprolog/core/types.py) | 論理変数（例：`X`, `Y`, `_Var`） |
| 数値 | [`Number`](../pyprolog/core/types.py) | 整数・浮動小数点（例：`42`, `3.14`） |
| 文字列 | [`String`](../pyprolog/core/types.py) | 文字列リテラル（例：`'hello'`） |
| 項 | [`Term`](../pyprolog/core/types.py) | 複合項（例：`f(a, b)`, `person(john, 25)`） |
| リスト | [`ListTerm`](../pyprolog/core/types.py) | リスト構造（例：`[1, 2, 3]`, `[H|T]`） |
| ファクト | [`Fact`](../pyprolog/core/types.py) | 単純な事実（例：`likes(mary, wine).`） |
| ルール | [`Rule`](../pyprolog/core/types.py) | 論理ルール（例：`happy(X) :- likes(X, wine).`） |

## ランタイム機能

### 主要メソッド

| メソッド | 説明 |
| --- | --- |
| [`Runtime.query(query_string)`](../pyprolog/runtime/interpreter.py) | クエリ文字列を実行し、解のリストを返す |
| [`Runtime.add_rule(rule_string)`](../pyprolog/runtime/interpreter.py) | ルール文字列を知識ベースに追加 |
| [`Runtime.consult(filename)`](../pyprolog/runtime/interpreter.py) | Prolog ファイルを読み込む |
| [`Runtime.execute(goal, env)`](../pyprolog/runtime/interpreter.py) | ゴールを環境で実行し、解を生成 |

### Runtime 初期化オプション

```python
from pyprolog import Runtime

runtime = Runtime(
    unsafe_mode=True,
)
```

現在の主要オプション:

| 引数 | 説明 |
| --- | --- |
| `rules` | 初期ルールのリスト |
| `variable_mapper` | 日本語変数名マッパー |
| `functor_mapper` | 非ASCIIファンクタ名マッパー |
| `occurs_check_enabled` | occurs check の有効/無効 |
| `unsafe_mode` | unsafe 外部Python実行機能を有効化 |

`unsafe_mode=True` のときのみ、`py_register/2`, `py_unregister/1`, `py_registered/2`, `py_call/5` が利用できます。

### 単一化アルゴリズム

[`LogicInterpreter`](../pyprolog/runtime/logic_interpreter.py)クラスで実装された単一化機能：
* 変数と項の単一化
* 複合項同士の単一化
* occurs check による無限ループ防止

### 入出力管理 (IOManager)

[`IOManager`](../pyprolog/runtime/io_manager.py)クラスが入出力を管理します。
* 標準入力/出力
* ファイル入出力
* ストリーム管理

### unsafe 外部Python実行

unsafe モードでは、Prolog から登録済み Python スクリプトを同期実行できます。

対象述語:

* `py_register/2`
* `py_unregister/1`
* `py_registered/2`
* `py_call/5`

制約:

* 登録パスは絶対パスのみ
* 対象は `.py` ファイルのみ
* `Args` は atom / string / number の proper list のみ
* 実行は `shell=False`、stdin 無効、同期実行

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
    print(result)
```

### unsafe モードで外部Pythonスクリプトを実行

```python
from pyprolog import Runtime

runtime = Runtime(unsafe_mode=True)

runtime.query('py_register(run_task, "/absolute/path/to/run_task.py").')
results = runtime.query(
    'py_call(run_task, ["--task-id", "task-001"], Exit, Out, Err).'
)

for result in results:
    print(result)
```

`consult()` で読み込む Prolog ファイル内でも directive として登録できます。

```python
from pyprolog import Runtime

runtime = Runtime(unsafe_mode=True)
runtime.consult("workflow.pl")
results = runtime.query("run(Exit, Out, Err).")
```

```prolog
:- py_register(run_task, "/absolute/path/to/run_task.py").

run(Exit, Out, Err) :-
    py_call(run_task, ["--mode", "fast"], Exit, Out, Err).
```

### 入出力操作とストリーム

```python
# get_char述語（文字単位入力）
from pyprolog.runtime.io_streams import StringStream
runtime.io_manager.set_input_stream(StringStream("hello"))
results = runtime.query("get_char(X)")
print(f"X = {results[0]['X']}")  # X = h

# read_line述語（行単位入力）
runtime.io_manager.set_input_stream(StringStream("Hello World\n"))
results = runtime.query("read_line(Line)")
print(f"Line = {results[0]['Line']}")  # Line = Hello World
```

### 知識ベースのエクスポート (export_facts)

```python
import tempfile
import os

# ファクト追加
runtime.add_rule("person(alice, 28, engineer).")

# CSV形式でエクスポート
temp_dir = tempfile.mkdtemp()
output_file = os.path.join(temp_dir, "persons.csv")

results = runtime.query(f"export_facts(person/3, '{output_file}').")

# JSON形式でエクスポート
json_file = os.path.join(temp_dir, "persons.json")
results = runtime.query(f"export_facts(person/3, json('{json_file}')).")
```
