# PyProlog API利用ガイド

## インストールと基本的な使用方法

### インポート
```python
from prolog import Parser, Runtime, Scanner
from prolog.core.types import Rule, Variable, Term, Atom, Number
from prolog.core.errors import PrologError, InterpreterError
```

## 基本的なAPIの使用

### 1. ランタイムの初期化

```python
# 空のランタイムを作成
runtime = Runtime()

# ルールを事前定義してランタイムを作成
rules = [
    # パーサーで解析済みのルールリスト
]
runtime = Runtime(rules)
```

### 2. ルールの追加

#### ファイルからの読み込み
```python
# Prologファイルの読み込み
success = runtime.consult("example.pl")
if not success:
    print("ファイルの読み込みに失敗しました")
```

#### 文字列からの追加
```python
# ルール文字列の追加
success = runtime.add_rule("likes(mary, food).")
success = runtime.add_rule("happy(X) :- likes(X, food).")
```

### 3. クエリの実行

```python
# クエリの実行
results = runtime.query("likes(mary, food)")
print(f"結果数: {len(results)}")

# 変数を含むクエリ
results = runtime.query("likes(X, food)")
for result in results:
    print(f"X = {result.get('X', 'unknown')}")

# 複雑なクエリ
results = runtime.query("likes(X, Y), happy(X)")
for result in results:
    print(f"X = {result['X']}, Y = {result['Y']}")
```

## パーサーの直接使用

### Scanner（字句解析）
```python
from prolog.parser.scanner import Scanner

# 文字列をトークン化
scanner = Scanner("likes(mary, food).")
tokens = scanner.scan_tokens()

for token in tokens:
    print(f"{token.token_type}: {token.lexeme}")
```

### Parser（構文解析）
```python
from prolog.parser.parser import Parser
from prolog.parser.scanner import Scanner

# 文字列を解析してルール/ファクトに変換
text = "likes(mary, food). happy(X) :- likes(X, food)."
scanner = Scanner(text)
tokens = scanner.scan_tokens()
parser = Parser(tokens)
rules = parser.parse()

print(f"解析されたルール数: {len(rules)}")
```

## Prolog型の構築

### 基本型の作成
```python
from prolog.core.types import Atom, Variable, Number, Term, ListTerm

# 原子
atom = Atom("hello")

# 変数
var = Variable("X")

# 数値
num = Number(42)

# 複合項
term = Term(Atom("likes"), [Atom("mary"), Atom("food")])

# リスト
list_term = ListTerm([Atom("a"), Atom("b"), Atom("c")])
```

### 複雑な項の構築
```python
# ネストした項: foo(bar(X), [1, 2, 3])
nested_term = Term(
    Atom("foo"),
    [
        Term(Atom("bar"), [Variable("X")]),
        ListTerm([Number(1), Number(2), Number(3)])
    ]
)
```

## バインディング環境の操作

```python
from prolog.core.binding_environment import BindingEnvironment
from prolog.core.types import Variable, Atom

# 新しい環境を作成
env = BindingEnvironment()

# 変数を束縛
env.bind("X", Atom("hello"))
env.bind("Y", Number(42))

# 値を取得
value = env.get_value("X")
print(f"X = {value}")

# 環境のコピー
env_copy = env.copy()

# 単一化
var1 = Variable("A")
var2 = Variable("B")
unified, new_env = env.unify(var1, Atom("test"))
if unified:
    print("単一化成功")
```

## エラーハンドリング

```python
try:
    results = runtime.query("invalid syntax query")
except PrologError as e:
    print(f"Prologエラー: {e}")
except InterpreterError as e:
    print(f"インタープリターエラー: {e}")
except Exception as e:
    print(f"予期しないエラー: {e}")
```

## I/O管理

### ストリームの設定
```python
from prolog.runtime.io_streams import StringStream

# 文字列ストリームを作成
input_stream = StringStream("hello\nworld\n")
output_buffer = []
output_stream = StringStream("", output_buffer)

# ランタイムにストリームを設定
runtime.io_manager.set_input_stream(input_stream)
runtime.io_manager.set_output_stream(output_stream)

# get_char述語のテスト
results = runtime.query("get_char(C)")
print(f"読み込んだ文字: {results[0]['C']}")
```

## 高度な使用例

### 動的述語の管理
```python
# 実行時にルールを追加
runtime.query("asserta(likes(john, pizza))")
runtime.query("assertz(likes(jane, sushi))")

# 追加されたファクトをクエリ
results = runtime.query("likes(X, Y)")
for result in results:
    print(f"{result['X']} likes {result['Y']}")
```

### メタ述語の使用
```python
# findallで全ての解を収集
runtime.add_rule("parent(tom, bob).")
runtime.add_rule("parent(tom, liz).")
runtime.add_rule("parent(bob, ann).")
runtime.add_rule("parent(bob, pat).")

# 全ての親子関係を収集
results = runtime.query("findall([X, Y], parent(X, Y), L)")
parent_list = results[0]['L']
print(f"全ての親子関係: {parent_list}")
```

### 算術演算
```python
# 算術式の評価
results = runtime.query("X is 3 + 4 * 2")
print(f"計算結果: {results[0]['X']}")

# 比較演算
results = runtime.query("5 > 3")
print(f"5 > 3: {len(results) > 0}")

# 変数を含む算術
runtime.query("X = 10, Y is X * 2, Y > 15")
```

### リスト処理
```python
# member述語でリスト要素を検索
results = runtime.query("member(b, [a, b, c])")
print(f"bは[a,b,c]のメンバー: {len(results) > 0}")

# append述語でリスト操作
results = runtime.query("append([1, 2], [3, 4], L)")
result_list = results[0]['L']
print(f"リスト結合結果: {result_list}")

# リストの分割
results = runtime.query("append(X, Y, [1, 2, 3, 4])")
for result in results:
    print(f"X={result['X']}, Y={result['Y']}")
```

## パフォーマンス考慮事項

### 効率的なクエリの書き方
```python
# 良い例: より具体的な条件を先に
runtime.query("number(X), X > 5, member(X, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])")

# 避けるべき例: 生成的なクエリを先に
# runtime.query("member(X, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]), number(X), X > 5")
```

### メモリ使用量の管理
```python
# 大量の解を扱う場合はfindallではなくイテレータを使用
results = runtime.query("member(X, [1, 2, 3, 4, 5])")
for result in results:
    # 各解を個別に処理
    process_result(result)
```

## デバッグとトラブルシューティング

### ログ設定
```python
import logging
from prolog.util.logger import logger

# デバッグレベルのログを有効化
logger.setLevel(logging.DEBUG)

# クエリ実行時の詳細ログ
results = runtime.query("your_query_here")
```

### 共通のエラーパターン

#### 構文エラー
```python
# 不正な構文
try:
    runtime.add_rule("invalid syntax here")
except PrologError as e:
    print(f"構文エラー: {e}")
```

#### 型エラー
```python
# 不正な型の引数
try:
    results = runtime.query("functor(123, Name, Arity)")
except PrologError as e:
    print(f"型エラー: {e}")
```

#### 未束縛変数エラー
```python
# 必要な引数が未束縛
try:
    results = runtime.query("arg(N, term, value)")  # Nが未束縛
except PrologError as e:
    print(f"未束縛変数エラー: {e}")
```

## 拡張と統合

### カスタム述語の追加
PyPrologは組み込み述語を拡張する機能を提供しています。新しい述語は[`BuiltinPredicate`](../prolog/runtime/builtins.py:10)クラスを継承して実装できます。

### Python関数との統合
Prolog述語からPython関数を呼び出すメカニズムも利用可能です。詳細は[`TermFunction`](../prolog/parser/types.py:112)クラスを参照してください。

---

*このAPIガイドは実装されている機能に基づいています。追加の機能や変更については、ソースコードとテストケースを参照してください。*