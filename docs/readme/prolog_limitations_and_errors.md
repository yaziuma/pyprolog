# PyProlog 制限事項とエラーハンドリング

## 現在の制限事項

### 1. 未実装機能

#### DCG (Definite Clause Grammar)

```prolog
% 未対応
sentence --> noun_phrase, verb_phrase.
noun_phrase --> [the], noun.
```

#### モジュールシステム

```prolog
% 未対応
:- module(mymodule, [exported_predicate/1]).
```

#### 制約処理 (CLP)

```prolog
% 未対応
:- use_module(library(clpfd)).
X #> 0, X #< 10.
```

#### テーブル化・メモ化

```prolog
% 未対応
:- table fibonacci/2.
```

### 2. 部分実装機能

#### 一部の組み込み述語

以下の述語は未実装または部分実装：

- `bagof/3`, `setof/3` (メタ述語)
- `once/1`, `ignore/1` (制御述語)
- `call/1`, `call/2`, `call/3` (メタ呼び出し)
- `catch/3`, `throw/1` (例外処理)
- `write/1`, `read/1` (基本 I/O)
- `op/3` (演算子定義)

#### ファイル I/O

基本的なファイル操作述語が限定的：

```prolog
% 制限的な対応
see(File), seen.
tell(File), told.
```

#### 数値処理

一部の数学関数が未実装：

```prolog
% 一部未対応
X is sin(3.14159).  % 三角関数
X is log(10).       % 対数関数
```

### 3. 言語仕様の制限

#### 演算子優先度

ISO Prolog 完全準拠ではない場合があります。

#### 文字コード処理

Unicode 文字列の完全対応は限定的です。

#### メモリ管理

大規模データに対する最適化が不十分な場合があります。

## エラー種別と対処法

### 1. 構文エラー (ScannerError, ParserError)

#### 字句解析エラー

```python
from prolog import Runtime
from prolog.core.errors import ScannerError

runtime = Runtime()

try:
    runtime.add_rule("invalid@syntax.")
except ScannerError as e:
    print(f"字句解析エラー: {e}")
    # 対処: 構文を修正してください
```

#### 構文解析エラー

```python
from prolog.core.errors import ParserError

try:
    runtime.add_rule("foo(a b).")  # カンマが欠落
except ParserError as e:
    print(f"構文解析エラー: {e}")
    # 対処: foo(a, b). のように修正
```

### 2. 実行時エラー (PrologError)

#### instantiation_error

必要な引数が未束縛の場合に発生：

```python
try:
    # argの第1引数が未束縛
    results = runtime.query("arg(N, foo(a, b), X)")
except PrologError as e:
    print(f"未束縛エラー: {e}")
    # 対処: arg(1, foo(a, b), X) のように引数を束縛
```

#### type_error

引数の型が期待と異なる場合：

```python
try:
    # functorの第1引数が数値（項でない）
    results = runtime.query("functor(123, Name, Arity)")
except PrologError as e:
    print(f"型エラー: {e}")
    # 対処: functor(foo(a), Name, Arity) のように項を渡す
```

#### domain_error

引数の値が定義域外の場合：

```python
try:
    # argの第1引数が0以下
    results = runtime.query("arg(0, foo(a, b), X)")
except PrologError as e:
    print(f"定義域エラー: {e}")
    # 対処: arg(1, foo(a, b), X) のように1以上の値を使用
```

#### existence_error

存在しない述語の呼び出し：

```python
try:
    results = runtime.query("undefined_predicate(X)")
except PrologError as e:
    print(f"存在エラー: {e}")
    # 対処: 述語を事前に定義するか、typoを修正
```

### 3. 算術エラー

#### division_by_zero

ゼロ除算：

```python
try:
    results = runtime.query("X is 5 / 0")
except PrologError as e:
    print(f"ゼロ除算エラー: {e}")
    # 対処: 除数が0でないことを事前にチェック
```

#### overflow

数値オーバーフロー：

```python
try:
    results = runtime.query("X is 10 ** 1000")
except PrologError as e:
    print(f"オーバーフローエラー: {e}")
    # 対処: より小さな値を使用
```

### 4. リストエラー

#### 不正なリスト構造

```python
try:
    # memberの第2引数がリストでない
    results = runtime.query("member(X, not_a_list)")
except PrologError as e:
    print(f"リストエラー: {e}")
    # 対処: member(X, [a, b, c]) のようにリストを渡す
```

## デバッグ手法

### 1. ログの活用

```python
import logging
from prolog.util.logger import logger

# デバッグレベルのログを有効にする
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# クエリ実行時の詳細ログが出力される
results = runtime.query("your_complex_query")
```

### 2. 段階的なクエリテスト

複雑なクエリは段階的にテスト：

```python
# 複雑なクエリ: findall(X, (parent(X, Y), parent(Y, Z)), L)

# ステップ1: 基本クエリ
runtime.query("parent(tom, bob)")

# ステップ2: ネストした関係
runtime.query("parent(X, Y), parent(Y, Z)")

# ステップ3: findall適用
runtime.query("findall(X, (parent(X, Y), parent(Y, Z)), L)")
```

### 3. 型チェック述語の活用

```python
# 引数の型を事前にチェック
query = """
    (var(X) ->
        writeln('X is unbound')
    ;
        (atom(X) ->
            writeln('X is an atom')
        ;
            writeln('X is something else')
        )
    )
"""
```

## パフォーマンスの制限

### 1. メモリ使用量

大量のデータを扱う場合の注意点：

```python
# 避けるべき: 大量の解をメモリに保持
results = runtime.query("findall(X, very_large_data(X), L)")

# 推奨: イテレータベースの処理
for result in runtime.query("very_large_data(X)"):
    process_one_result(result)
    if some_condition():
        break
```

### 2. 計算複雑性

指数的な計算量になる可能性があるパターン：

```python
# 注意: 左再帰は無限ループの可能性
runtime.add_rule("ancestor(X, Y) :- ancestor(X, Z), parent(Z, Y).")
runtime.add_rule("ancestor(X, Y) :- parent(X, Y).")

# より効率的: 右再帰
runtime.add_rule("ancestor(X, Y) :- parent(X, Y).")
runtime.add_rule("ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).")
```

### 3. バックトラック制御

無制限なバックトラックを制御：

```python
# カットを使用して選択点を制限
runtime.add_rule("max(X, Y, X) :- X >= Y, !.")
runtime.add_rule("max(X, Y, Y).")
```

## 既知の問題と回避策

### 1. 演算子結合性

複雑な演算子の組み合わせで予期しない結果：

```python
# 回避策: 括弧を明示的に使用
results = runtime.query("X is (1 + 2) * 3")  # 明確
# 避ける: X is 1 + 2 * 3  # 曖昧な場合
```

### 2. 変数スコープ

ネストした構造での変数名衝突：

```python
# 注意: 同じ変数名Xが異なるスコープで使用
query = "findall(X, (member(X, [1,2]), findall(X, member(X, [a,b]), L)), Result)"

# 回避策: 異なる変数名を使用
query = "findall(X, (member(X, [1,2]), findall(Y, member(Y, [a,b]), L)), Result)"
```

### 3. リスト構造の制限

深くネストしたリストでの性能問題：

```python
# 回避策: リストの深さを制限し、必要に応じて分割処理
```

## 今後の改善予定

### 近期的改善

1. エラーメッセージの詳細化
2. より多くの組み込み述語の実装
3. パフォーマンス最適化

### 長期的改善

1. ISO Prolog 完全準拠
2. モジュールシステム実装
3. 制約処理システム
4. 並列実行サポート

---

_このドキュメントは現在の実装に基づいています。バージョンアップに伴い制限事項は改善される可能性があります。_
