# Simple Prolog Interpreter in Python (uv 版)

[](https://www.google.com/search?q=LICENSE)

このプロジェクトは、Python で実装されたシンプルな Prolog インタープリタです。
ここでは、高速な Python パッケージインストーラーおよびリゾルバーである `uv` を使用した開発手順を説明します。

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
算術演算やリスト操作も可能です。詳細な例は元の README を参照してください。

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
    '''

    tokens = Scanner(source).tokenize()
    rules = Parser(tokens).parse_rules()

    runtime = Runtime(rules)

    goal_text = 'location(X, office).'
    goal = Parser(Scanner(goal_text).tokenize()).parse_terms()

    # goal から 'X' 変数を取得する正しい方法は、
    # Parser がどのように Term オブジェクトを構築するかに依存します。
    # ここでは単純化のため、goal.args[0] が 'X' に対応すると仮定します。
    # 実際のProlog実装では、変数を名前で参照する機構があるかもしれません。
    # この例では、元のREADMEの構造を踏襲します。
    # goal の構造を確認し、適切に変数 'X' を取得してください。
    # 例:
    # query_vars = {}
    # for term in goal:
    #     for i, arg in enumerate(term.args):
    #         if isinstance(arg, Var) and arg.name == 'X': # Var型と仮定
    #             query_vars['X'] = arg
    # x_var = query_vars.get('X')

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


    if has_solution:
        print('Query has solution(s)')
    else:
        print('Query has no solution')

if __name__ == "__main__":
    main()
```

## 6\. その他の `uv` コマンド (参考)

`uv` は他にも多くの便利な機能を提供しています。

- **依存関係ツリーの表示**:
  ```bash
  uv pip tree
  # またはプロジェクト依存関係の場合
  # uv tree
  ```
- **インストール済みパッケージの一覧**:
  ```bash
  uv pip list
  ```
- **キャッシュの管理**:
  ```bash
  uv cache clean  # キャッシュエントリを削除
  uv cache dir    # キャッシュディレクトリのパスを表示
  ```
- **`uv` 自体のアップデート**:
  ```bash
  uv self update
  ```

詳細なコマンドやオプションについては、`uv --help` や [uv 公式ドキュメント](https://astral.sh/uv) を参照してください。

## Acknowledgments

This was inspired and based on this [article](https://curiosity-driven.org/prolog-interpreter).
