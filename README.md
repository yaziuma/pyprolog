# Simple Prolog Interpreter in Python (uv 版)

[](https://www.google.com/search?q=LICENSE)

このプロジェクトは、Python で実装されたシンプルな Prolog インタープリタです。
ここでは、高速な Python パッケージインストーラーおよびリゾルバーである `uv` を使用した開発手順を説明します。

## ⚠️ 演算子システム更新について

**2025年6月21日 - 重要な演算子システム修正を実施中**

バックスラッシュ演算子（`\==`, `\=`, `=\=`）のパース処理に問題があるため、以下の代替演算子を導入しました：

### 新しい演算子体系
- **等価性**: `=`（単一化）, `==`（同一性）, `=:=`（算術等価）
- **非等価性**: `<>`（統一記法）, `!=`（代替記法）
- **比較**: `<`, `>`, `=<`, `>=`（従来通り）

### 変更の利点
- パーサーの安定性向上
- 他言語経験者にとって直感的
- 保守性とテスト性の向上

### 使用例
```prolog
% 新しい演算子の使用例（推奨）
different(X, Y) :- X <> Y.
not_same(A, B) :- A != B.

% ❌ 禁止: バックスラッシュ演算子は使用不可
% old_way(X, Y) :- X \= Y.  % 使用禁止！
```

詳細は `docs/20250621/operator_alternatives.md` および `docs/pyprolog_実装済み機能・述語リスト.md` を参照してください。

## 0\. `uv` のインストール

まだ `uv` をインストールしていない場合は、以下のコマンドでインストールしてください。

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

詳細なインストール方法は [uv 公式ドキュメント](https://astral.sh/uv) を参照してください。

## 1\. プロジェクトのセットアップ

### 1.1. プロジェクトの初期化 (オプション)

新しいプロジェクトとして始める場合、または既存のプロジェクトに `pyproject.toml` を導入する場合は、以下のコマンドを実行します。

```bash
uv init
```

これにより、対話的に `pyproject.toml` ファイルが生成されます。

### 1.2. Python バージョンの管理

プロジェクトで使用する Python のバージョンを指定・管理できます。

```bash
# 利用可能なPythonバージョンを検索 (例: 3.10)
uv python find 3.10

# 特定のPythonバージョンをインストール (もし未インストールの場合)
uv python install 3.10

# プロジェクトで使用するPythonバージョンを固定
# これにより .python-version ファイルが作成または更新されます
uv python pin 3.10
```

### 1.3. 仮想環境の作成と有効化

プロジェクト専用の仮想環境を作成し、有効化します。

```bash
# 仮想環境の作成 (デフォルトでは .venv という名前で作成されます)
uv venv
# 特定のPythonバージョンを指定して仮想環境を作成する場合
# uv venv --python 3.10

# 仮想環境の有効化
# macOS / Linux
source .venv/bin/activate
# Windows
.\.venv\Scripts\activate
```

## 2\. 依存関係の管理

プロジェクトの依存関係は `pyproject.toml` ファイルで管理し、`uv` を使ってインストール・同期します。

### 2.1. 依存関係のインストール

`requirements.txt` ファイルがある場合:

```bash
# requirements.txt から依存関係をインストール
uv add -r requirements.txt
```

`pyproject.toml` を使用する場合 (推奨):

```bash
# プロジェクトの依存関係を pyproject.toml (または uv.lock) に基づいて同期
uv sync

# 個別のパッケージを依存関係として追加
uv add <パッケージ名>
# 例: uv add requests

# 開発用の依存関係 (テストツール、リンターなど) を追加
uv add --dev <パッケージ名>
# 例: uv add --dev pytest ruff
```

### 2.2. 依存関係のロック

依存関係のバージョンを固定するためにロックファイルを作成・更新します。
`pyproject.toml` がある場合は、`uv.lock` が生成されます。

```bash
uv lock
```

## 3\. REPL の実行

Prolog インタープリタの REPL (Read-Eval-Print Loop) を実行します。

```bash
# uv を使ってプロジェクト環境内でスクリプトを実行
uvx python -m pyprolog.cli.prolog [options] path
```

例えば:

```bash
uvx python -m pyprolog.cli.prolog tests/data/puzzle1.prolog
```

`pyproject.toml` の `[tool.uv.scripts]` セクションにスクリプトを定義することもできます。
例 (`pyproject.toml`):

```toml
[tool.uv.scripts]
prolog-repl = "python -m pyprolog.cli.prolog"
```

その場合、以下のように実行できます:

```bash
uvx prolog-repl -- tests/data/puzzle1.prolog
# (注意: スクリプト定義後の引数は -- の後に記述します)
```

サンプル REPL セッション出力:

```bash
python -m pyprolog.cli.prolog tests/data/myadven.prolog

Welcome to Simple Prolog
ctrl-c to quit
> location(desk, office).
yes
> location(X, Y).
X = desk Y = office
... (以下略) ...
```

Simple Prolog は、`write`, `tab`, `nl`, `fail` といった組み込み述語をサポートしています。
算術演算やリスト操作も可能です。

**重要な変更**: 2025年6月21日のアップデートで、新しい非等価演算子 `<>` と `!=` が追加されました。
これらは従来のバックスラッシュ演算子 `\=` の代替として、より安定したパース処理と直感的な記法を提供します。

**⚠️ 注意**: バックスラッシュ演算子（`\=`, `\==`, `=\=`）の使用は禁止されました。必ず新しい演算子を使用してください。

詳細な機能リストと使用例については `docs/pyprolog_実装済み機能・述語リスト.md` を参照してください。

## 4\. テストとリンティング

### 4.1. 開発用依存関係のインストール (まだの場合)

```bash
uv add --dev ruff pytest pytest-cov
# requirements-dev.txt などがある場合は:
# uv pip install -r requirements-dev.txt
```

### 4.2. リンターの実行

```bash
uvx ruff check .
# または、整形も同時に行う場合
# uvx ruff format .
# uvx ruff check . --fix # 自動修正可能な問題を修正
```

### 4.3. テストの実行

```bash
uvx pytest --cov=pyprolog tests
```

## 5\. PyProlog をライブラリとして使用する

PyProlog を自身の Python プロジェクトでライブラリとして使用する方法です。

### 5.1. PyProlog のインストール

ご自身のプロジェクトに `pieprolog` (注意: パッケージ名は `pieprolog` です) を追加します。

```bash
# uv を使用してプロジェクトに依存関係として追加 (推奨)
uv add pieprolog

# もしくは、現在の仮想環境に直接インストールする場合
# uv pip install pieprolog
```

### 5.2. ライブラリ使用例

```python
from pyprolog import Scanner, Parser, Runtime

def main():
    source = '''
    location(computer, office).
    location(knife, kitchen).
    location(chair, office).
    location(shoe, hall).

    isoffice(X) :- location(computer, X), location(chair, X).
    
    % 新しい演算子の使用例（推奨）
    different_locations(X, Y) :- location(_, X), location(_, Y), X <> Y.
    
    % ❌ 禁止例: バックスラッシュ演算子
    % old_different(X, Y) :- X \= Y.  % 使用禁止！
    '''

    tokens = Scanner(source).tokenize()
    rules = Parser(tokens).parse_rules()

    runtime = Runtime(rules)

    # 基本的なクエリ例
    goal_text = 'location(X, office).'
    goal = Parser(Scanner(goal_text).tokenize()).parse_terms()

    # 新しい非等価演算子の使用例
    different_query = 'different_locations(office, kitchen).'
    different_goal = Parser(Scanner(different_query).tokenize()).parse_terms()

    x = goal.args[0] # 元のREADMEの記述に合わせる

    has_solution = False
    for index, item in enumerate(runtime.execute(goal)):
        has_solution = True
        print(f"Solution {index + 1}: {item}")
        # goal.match(item) が辞書を返し、そのキーが変数オブジェクトであると仮定
        solution_mapping = goal.match(item)
        if x in solution_mapping:
            print(f"X = {solution_mapping[x]}")
        else:
            # goal.args[0] が直接解決された値を持つ場合など、
            # Prolog実装によってここの処理は変わります。
            # print(f"X = {item.args[0]}") # item の構造に依存
            pass

    # 新しい演算子のテスト
    print("\n新しい演算子のテスト:")
    different_solutions = list(runtime.execute(different_goal))
    print(f"different_locations クエリ: {len(different_solutions)} 個の解")

    if has_solution:
        print('Query has solution(s)')
    else:
        print('Query has no solution')

if __name__ == "__main__":
    main()
```

## 5.3. 非ブロッキング入力機能（新機能）

PyProlog 0.2.2 から、`peek_char/1` および `at_end_of_stream/0` 述語が追加されました。これにより、入力待ちでアプリケーションが停止することなく、条件付きの入力処理が可能になります。

### 基本的な使用例

```python
from pyprolog.runtime.interpreter import Runtime
from pyprolog.runtime.io_streams import StringStream
from pyprolog.core.types import Variable

# ランタイムの初期化
runtime = Runtime()

# テスト用の文字列ストリームを設定
runtime.io_manager.set_input_stream(StringStream("hello"))

# peek_char/1: 次の文字を非破壊的に先読み
peek_result = runtime.query("peek_char(X)")
print(f"Next character: {peek_result[0][Variable('X')]}")  # 'h'

# 同じ文字がもう一度取得される（ストリーム位置は変更されない）
peek_again = runtime.query("peek_char(Y)")  
print(f"Same character: {peek_again[0][Variable('Y')]}")  # 'h'

# 実際に文字を消費
consume_result = runtime.query("get_char(Z)")
print(f"Consumed: {consume_result[0][Variable('Z')]}")  # 'h'

# at_end_of_stream/0: EOF状態の確認
eof_result = runtime.query("at_end_of_stream")
print(f"At EOF: {len(eof_result) > 0}")  # False（まだデータあり）
```

### 条件付き読み取りパターン

```python
# 数字判定ルールの追加
runtime.add_rule("""
read_if_digit(Char) :-
    peek_char(Next),
    Next >= '0',
    Next =< '9',
    get_char(Char).
""")

# テストケース1: 数字がある場合
runtime.io_manager.set_input_stream(StringStream("5abc"))
digit_result = runtime.query("read_if_digit(D)")
if digit_result:
    print(f"Read digit: {digit_result[0][Variable('D')]}")  # '5'

# テストケース2: 数字がない場合
runtime.io_manager.set_input_stream(StringStream("abc"))
letter_result = runtime.query("read_if_digit(L)")
print(f"Failed to read digit: {len(letter_result) == 0}")  # True
```

### Prologでの使用例

```prolog
% パーサー実装パターン
parse_number(Num) :-
    peek_char(First),
    First >= '0', First =< '9',
    collect_digits(Digits),
    atom_codes(Num, Digits).

% 先読みによる条件分岐
next_token_type(number) :-
    peek_char(C),
    C >= '0', C =< '9'.

next_token_type(letter) :-
    peek_char(C),
    C >= 'a', C =< 'z'.

next_token_type(eof) :-
    at_end_of_stream.

% 空白のスキップ
skip_whitespace :-
    peek_char(' '),
    get_char(_),
    skip_whitespace.

skip_whitespace :-
    peek_char(C),
    C \= ' '.
```

### 利用場面

- **対話的アプリケーション開発**: 入力待ちでUIが凍結しない制御
- **パーサー・トークナイザー実装**: 先読みによる構文解析
- **ライブラリとしての利用**: 予期しない入力待ちの回避
- **条件付き入力処理**: 入力内容に応じた処理の分岐
