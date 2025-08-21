# PyProlog - Advanced Prolog Interpreter in Python

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-112%20Passing-green.svg)](#testing)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

このプロジェクトは、**日本語変数名サポート**と**高度な開発ツール**を備えた、Python で実装された本格的な Prolog インタープリタです。`uv` を使用した高速開発環境とツール拡張機能を特徴とします。

## 🚀 主な特徴

### ✨ 言語サポート
- **日本語変数名・ファンクター名完全サポート**: `患者診断(症状, 年齢, 結果)`
- **Unicode文字対応**: あらゆる言語の文字を使用可能
- **70種類以上の演算子**: 算術、比較、論理、制御演算子を完備

### 🛠️ 開発ツール
- **`prolog_explain`**: クエリの推論過程を可視化（テキスト/ツリー/JSON形式）
- **`prolog_search`**: 大規模知識ベースの高速検索
- **`prolog_validate`**: 静的解析による品質チェック

### 🎯 実用機能
- **包括的な組み込み述語**: 36種類以上の標準述語（`atom_number/2`新追加）
- **自動型変換**: 数値文字列の自動判定・変換機能
- **高速CLIインターフェース**: インタラクティブREPLと一括処理
- **豊富なI/O機能**: ファイル読み書き、ストリーム処理、複数回入力対応
- **メタ述語サポート**: `findall/3`, 動的述語管理

## 📊 プロジェクト状況（最新）

**2025年8月21日 - 入力システム大幅強化 (v0.5.0)**

✅ **型変換システム追加**: `atom_number/2`述語で安全な文字列⇔数値変換  
✅ **自動入力変換**: `read_line/1`と`get_char/1`で数値文字列を自動判定  
✅ **複数入力対応**: 繰り返し入力・バリデーション処理を完全サポート  
✅ **IOシステム統合**: write/nl演算子がストリーム処理と完全統合  
✅ **全124テスト合格**: 新機能含む全テストが正常動作

## 🚀 クイックスタート

### 最速で試す（3分で動作確認）

```bash
# 1. プロジェクトをクローン
git clone <repository-url>
cd pyprolog

# 2. 依存関係をインストール
uv sync

# 3. 基本的な Prolog クエリを実行
uvx python -m pyprolog.cli.prolog tests/data/puzzle1.prolog

# 4. 日本語医療診断システムを試す
uvx python -c "
from pyprolog.runtime.interpreter import Runtime
r = Runtime()
r.consult('tests/data/medical_diagnosis_kb_japanese.pl')
solutions = r.query('患者診断([発熱, 咳], 30, [], [], Result).')
print(f'診断結果: {solutions}')
"
```

### インタラクティブREPLで対話的に実行

```bash
# インタラクティブモードで起動
uvx python -m pyprolog.cli.interactive_repl

# REPLで日本語変数を使用
?- 年齢 = 25, 年齢 > 20.
年齢 = 25.

?- append([a, b], [c, d], リスト).
リスト = [a, b, c, d].
```

## 🛠️ 開発ツールの使用例

### prolog_explain: 推論過程の可視化
```python
from pyprolog.tools.explain_tool import ExplainTool
tool = ExplainTool(runtime)
result = tool.explain("member(X, [1, 2, 3])", format="tree")
print(result)
```

### prolog_search: 知識ベース検索
```python
from pyprolog.tools.search_tool import SearchTool
tool = SearchTool(runtime)
results = tool.search("patient", search_type="predicate")
```

### prolog_validate: 静的解析
```python
from pyprolog.tools.validate_tool import ValidateTool
tool = ValidateTool(runtime)
issues = tool.validate(check_type="all")
```

## 📋 インストール・セットアップ

### 前提条件
- Python 3.8以上
- `uv`パッケージマネージャー

### uv のインストール

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

詳細は [uv 公式ドキュメント](https://astral.sh/uv) を参照してください。

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

## 🎯 主要機能詳細

### 📝 組み込み述語 (35種類以上)

#### 基本I/O
- `write/1`, `nl/0`, `tab/0`, `tab/1`
- `get_char/1`, `peek_char/1`, `read_line/1`
- `at_end_of_stream/0`

#### 型チェック
- `var/1`, `atom/1`, `number/1`
- `functor/3`, `arg/3`, `=../2`

#### リスト操作
- `member/2`, `append/3`
- `[H|T]` パターンマッチング

#### メタ述語
- `findall/3`: 解の収集
- `asserta/1`, `assertz/1`: 動的述語追加
- `retract/1`: 述語削除

#### 算術・比較演算子
- **算術**: `+`, `-`, `*`, `/`, `mod`, `**`, `is/2`
- **比較**: `=:=`, `=\=`, `<`, `=<`, `>`, `>=`
- **等価性**: `=`（単一化）, `==`（同一性）
- **非等価性**: `<>`, `!=`（推奨）, `\=`

### 🌐 日本語サポート

完全な Unicode サポートにより、変数名・ファンクター名・アトムに日本語を使用可能：

```prolog
% 医療診断の例
疾患症状(風邪, 発熱, 0.8).
疾患症状(風邪, 咳, 0.7).

患者診断(症状リスト, 年齢, 基礎疾患, 生活習慣, 診断結果) :-
    症状マッチング(症状リスト, 疾患確率リスト),
    最高確率疾患(疾患確率リスト, 診断結果).
```

### 🔧 開発ツール

#### prolog_explain - 推論過程の可視化
```python
tool = ExplainTool(runtime)

# テキスト形式
result = tool.explain("append([1,2], [3], L)", format="text")
# CALL: append([1,2], [3], L)
# EXIT: append([1,2], [3], [1,2,3])
# SUCCESS: L = [1,2,3]

# JSON形式（他ツールとの連携用）
result = tool.explain("member(X, [a,b,c])", format="json")
```

#### prolog_search - 知識ベース検索
```python
tool = SearchTool(runtime)

# 述語名検索
results = tool.search("patient", search_type="predicate")

# 引数パターン検索
results = tool.search("patient(_, adult)", search_type="argument")

# 全文検索
results = tool.search("diagnosis", search_type="full_text")
```

#### prolog_validate - 静的解析
```python
tool = ValidateTool(runtime)

# 全項目チェック
issues = tool.validate(check_type="all")

# 未定義述語のチェック
issues = tool.validate(check_type="undefined")

# 到達不能ルールの検出
issues = tool.validate(check_type="unreachable")
```

### ⚡ パフォーマンス特徴

- **大規模KB対応**: 75ルール以下で最適性能
- **高速検索**: インデックス付きパターンマッチング
- **メモリ効率**: 遅延評価による省メモリ実行
- **並行処理**: 複数クエリの並列実行サポート

詳細な機能リストと使用例については `docs/pyprolog_実装済み機能・述語リスト.md` を参照してください。

## 🧪 テストとコード品質

### 包括的なテストスイート（112テスト）

```bash
# 全テスト実行
uvx pytest --cov=pyprolog tests

# 特定のカテゴリのみ実行
uvx pytest tests/integration/ -v    # 統合テスト
uvx pytest tests/japanese/ -v      # 日本語サポートテスト
uvx pytest tests/tools/ -v         # 開発ツールテスト
```

### テストカテゴリ
- **統合テスト (43)**: エンドツーエンド機能テスト
- **日本語テスト (16)**: Unicode文字サポート検証
- **ツールテスト (53)**: explain/search/validateツール検証
- **単体テスト**: パーサー、ランタイム、コア機能

### コード品質管理

```bash
# リンティングとフォーマット
uvx ruff check .          # 問題チェック
uvx ruff format .         # コードフォーマット
uvx ruff check . --fix    # 自動修正

# 開発用依存関係のインストール
uv add --dev ruff pytest pytest-cov
```

### テスト結果例
```
========================== 112 passed in 0.36s ==========================
✅ 統合テスト: 43/43 合格
✅ 日本語テスト: 16/16 合格  
✅ ツールテスト: 53/53 合格
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

## 5.3. 型変換と複数入力機能（v0.5.0新機能）

PyProlog 0.5.0から、`atom_number/2`述語による型変換と、入力述語の自動数値変換機能が追加されました。

### atom_number/2述語の使用例

```python
from pyprolog import Runtime

runtime = Runtime()

# 文字列 → 数値変換
results = runtime.query("atom_number('42', X)")
print(f"X = {results[0]['X']}")  # X = 42

# 数値 → 文字列変換  
results = runtime.query("atom_number(Atom, 3.14)")
print(f"Atom = {results[0]['Atom']}")  # Atom = '3.14'

# 型チェック（成功例）
results = runtime.query("atom_number('100', 100)")
print(f"Success: {len(results) > 0}")  # Success: True

# 型チェック（失敗例）
results = runtime.query("atom_number('abc', 123)")
print(f"Success: {len(results) > 0}")  # Success: False
```

### 自動数値変換機能

```python
from pyprolog.runtime.io_streams import StringStream

# 数値文字列の自動変換
runtime.io_manager.set_input_stream(StringStream("42\nabc\n3.14\n"))

# read_line/1で自動変換される
for i in range(3):
    results = runtime.query("read_line(X)")
    if results:
        val = results[0]['X']
        print(f"Input {i+1}: {val} (Type: {type(val).__name__})")
# Output:
# Input 1: 42 (Type: Number)    <- 自動変換
# Input 2: abc (Type: Atom)     <- 文字列のまま  
# Input 3: 3.14 (Type: Number)  <- 自動変換
```

### 複数入力プログラムの例

複数回の入力を必要とするPrologプログラムも簡単に作成できます：

```prolog
% multiple_input_calculator.pl
calculate_sum :-
    write('数値を2つ入力してください'), nl,
    read_line(First),
    read_line(Second), 
    Sum is First + Second,
    write('合計: '), write(Sum), nl.
```

```python
# Python側での使用
runtime.consult("multiple_input_calculator.pl")
runtime.io_manager.set_input_stream(StringStream("10\n20\n"))
results = runtime.query("calculate_sum")
# 出力: "数値を2つ入力してください\n合計: 30"
```

## 5.4. 非ブロッキング入力機能（新機能）

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

## 🤝 コントリビューション

コントリビューションを歓迎します！以下の手順でお願いします：

1. **Issues を確認**: バグ報告や機能要望をGitHubのIssuesで確認
2. **フォーク & ブランチ**: リポジトリをフォークし、機能ブランチを作成
3. **開発**: 
   ```bash
   # 開発環境のセットアップ
   uv sync
   
   # テストの実行
   uvx pytest tests/ -v
   
   # コード品質チェック
   uvx ruff check . --fix
   uvx ruff format .
   ```
4. **プルリクエスト**: 変更内容の詳細な説明と共にPRを作成

### 開発ガイドライン
- 新機能にはテストを追加
- `CLAUDE.md` の開発指針に従う
- 日本語文字のサポートを考慮
- 既存の112テストが全て通ることを確認

## 📚 ドキュメント・参考資料

### プロジェクト内ドキュメント
- [`CLAUDE.md`](CLAUDE.md): 開発者向け詳細ガイド
- [`docs/tool_enhancement_proposals/`](docs/tool_enhancement_proposals/): ツール設計書
- [`sample_usage/`](sample_usage/): 使用例とデモ
- [`tests/`](tests/): 包括的なテスト例

### 外部リンク
- [uv公式ドキュメント](https://astral.sh/uv): パッケージマネージャー
- [Prolog言語仕様](https://www.swi-prolog.org/): 標準的なProlog参考資料

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 🎯 作者・保守者

このプロジェクトは [Claude Code](https://claude.ai/code) との協力により開発・保守されています。

---

**PyProlog** で日本語プログラミングとProlog推論の世界をお楽しみください！🚀
