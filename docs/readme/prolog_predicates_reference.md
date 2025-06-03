# PyProlog組み込み述語リファレンス

## 型チェック述語

### var/1
**構文**: `var(+Term)`
**説明**: 引数が未束縛変数かどうかを判定
**成功条件**: 引数が Variable 型で未束縛の場合
**実装**: [`VarPredicate`](../prolog/runtime/builtins.py:18)

```prolog
?- var(X).
true.

?- var(hello).
false.
```

### atom/1
**構文**: `atom(+Term)`
**説明**: 引数が原子かどうかを判定
**成功条件**: 引数が Atom 型の場合
**実装**: [`AtomPredicate`](../prolog/runtime/builtins.py:27)

```prolog
?- atom(hello).
true.

?- atom(123).
false.
```

### number/1
**構文**: `number(+Term)`
**説明**: 引数が数値かどうかを判定
**成功条件**: 引数が Number 型の場合
**実装**: [`NumberPredicate`](../prolog/runtime/builtins.py:36)

```prolog
?- number(123).
true.

?- number(hello).
false.
```

## 項操作述語

### functor/3
**構文**: `functor(?Term, ?Name, ?Arity)`
**説明**: 項の述語名とアリティを取得・構築
**モード**:
- `functor(+Term, -Name, -Arity)`: 項から述語名・アリティ取得
- `functor(-Term, +Name, +Arity)`: 述語名・アリティから項構築
**実装**: [`FunctorPredicate`](../prolog/runtime/builtins.py:46)

```prolog
?- functor(foo(a, b), Name, Arity).
Name = foo, Arity = 2.

?- functor(Term, bar, 3).
Term = bar(_, _, _).
```

### arg/3
**構文**: `arg(+N, +Term, ?Arg)`
**説明**: 項のN番目の引数を取得
**引数**:
- `N`: 引数の位置（1から開始）
- `Term`: 対象の項
- `Arg`: N番目の引数
**実装**: [`ArgPredicate`](../prolog/runtime/builtins.py:105)

```prolog
?- arg(2, foo(a, b, c), X).
X = b.
```

### =../2 (univ)
**構文**: `Term =.. List`
**説明**: 項をリスト表現に変換（またはその逆）
**モード**:
- `+Term =.. -List`: 項をリストに変換
- `-Term =.. +List`: リストから項を構築
**実装**: [`UnivPredicate`](../prolog/runtime/builtins.py:125)

```prolog
?- foo(a, b) =.. L.
L = [foo, a, b].

?- T =.. [bar, x, y].
T = bar(x, y).
```

## 動的述語管理

### asserta/1
**構文**: `asserta(+Clause)`
**説明**: 節をデータベースの先頭に追加
**引数**: `Clause` - 追加する節（ファクトまたはルール）
**実装**: [`DynamicAssertAPredicate`](../prolog/runtime/builtins.py:195)

```prolog
?- asserta(likes(mary, food)).
true.

?- asserta((happy(X) :- likes(X, food))).
true.
```

### assertz/1
**構文**: `assertz(+Clause)`
**説明**: 節をデータベースの末尾に追加
**引数**: `Clause` - 追加する節（ファクトまたはルール）
**実装**: [`DynamicAssertZPredicate`](../prolog/runtime/builtins.py:221)

```prolog
?- assertz(likes(john, beer)).
true.
```

## リスト処理述語

### member/2
**構文**: `member(?Elem, ?List)`
**説明**: リストのメンバーシップ判定・生成
**モード**:
- `member(+Elem, +List)`: 要素がリストに含まれるかチェック
- `member(-Elem, +List)`: リストの要素を一つずつ生成
- `member(+Elem, -List)`: 要素を含むリストを生成（無限）
**実装**: [`MemberPredicate`](../prolog/runtime/builtins.py:244)

```prolog
?- member(b, [a, b, c]).
true.

?- member(X, [1, 2, 3]).
X = 1 ;
X = 2 ;
X = 3.
```

### append/3
**構文**: `append(?List1, ?List2, ?List3)`
**説明**: リストの結合・分割
**モード**:
- `append(+List1, +List2, -List3)`: 2つのリストを結合
- `append(+List1, -List2, +List3)`: List3からList1を除いた残りを取得
- `append(-List1, -List2, +List3)`: List3を2つのリストに分割
**実装**: [`AppendPredicate`](../prolog/runtime/builtins.py:266)

```prolog
?- append([1, 2], [3, 4], L).
L = [1, 2, 3, 4].

?- append(X, Y, [1, 2, 3]).
X = [], Y = [1, 2, 3] ;
X = [1], Y = [2, 3] ;
X = [1, 2], Y = [3] ;
X = [1, 2, 3], Y = [].
```

## メタ述語

### findall/3
**構文**: `findall(+Template, +Goal, -List)`
**説明**: ゴールの全ての解を収集してリストに格納
**引数**:
- `Template`: 収集する項のテンプレート
- `Goal`: 実行するゴール
- `List`: 解のリスト
**実装**: [`FindallPredicate`](../prolog/runtime/builtins.py:325)

```prolog
?- findall(X, member(X, [1, 2, 3]), L).
L = [1, 2, 3].

?- findall([X, Y], (member(X, [a, b]), member(Y, [1, 2])), L).
L = [[a, 1], [a, 2], [b, 1], [b, 2]].
```

## 入出力述語

### get_char/1
**構文**: `get_char(?Char)`
**説明**: 現在の入力ストリームから1文字読み込み
**モード**:
- `get_char(-Char)`: 文字を読み込んで変数に束縛
- `get_char(+Char)`: 読み込んだ文字が指定文字と一致するかチェック
**実装**: [`GetCharPredicate`](../prolog/runtime/builtins.py:410)

```prolog
?- get_char(C).
% 入力: a
C = a.

?- get_char(x).
% 入力: x
true.

?- get_char(x).
% 入力: y
false.
```

## 算術・比較演算子

### is/2
**構文**: `?Result is +Expression`
**説明**: 算術式を評価して結果を単一化
**実装**: [`_create_is_evaluator()`](../prolog/runtime/interpreter.py:73)

```prolog
?- X is 3 + 4.
X = 7.

?- Y is 2 * 5 - 1.
Y = 9.
```

### 算術比較演算子

#### =:=/2 (算術等価)
**構文**: `+Expr1 =:= +Expr2`
**説明**: 2つの算術式を評価して等しいかチェック

#### =\=/2 (算術非等価)
**構文**: `+Expr1 =\= +Expr2`
**説明**: 2つの算術式を評価して異なるかチェック

#### </2, =</2, >/2, >=/2
**構文**: `+Expr1 Op +Expr2`
**説明**: 算術式の大小比較

```prolog
?- 3 + 4 =:= 7.
true.

?- 5 > 3.
true.

?- 2 * 3 =< 10.
true.
```

### 算術演算子

サポートされている算術演算子：
- `+`, `-` (二項・単項)
- `*`, `/` (乗算・除算)
- `//` (整数除算)
- `mod` (剰余)
- `**` (べき乗)

## 単一化・等価演算子

### =/2 (単一化)
**構文**: `?Term1 = ?Term2`
**説明**: 2つの項を単一化

### \=/2 (非単一化)
**構文**: `?Term1 \= ?Term2`
**説明**: 2つの項が単一化できないことをチェック

### ==/2 (同一性)
**構文**: `?Term1 == ?Term2`
**説明**: 2つの項が同一かチェック（変数は束縛状態も考慮）

### \==/2 (非同一性)
**構文**: `?Term1 \== ?Term2`
**説明**: 2つの項が同一でないことをチェック

```prolog
?- X = Y.
X = _G123, Y = _G123.

?- foo(X) = foo(bar).
X = bar.

?- 3 == 3.
true.

?- X == Y.
false.
```

## 論理演算子

### ,/2 (連言)
**構文**: `+Goal1, +Goal2`
**説明**: 両方のゴールが成功する場合に成功

### ;/2 (選言)
**構文**: `+Goal1 ; +Goal2`
**説明**: いずれかのゴールが成功する場合に成功

### \+/1 (否定)
**構文**: `\+ +Goal`
**説明**: ゴールが失敗する場合に成功（否定として失敗）

```prolog
?- member(X, [1, 2, 3]), X > 2.
X = 3.

?- member(X, [1, 2]); member(X, [3, 4]).
X = 1 ;
X = 2 ;
X = 3 ;
X = 4.

?- \+ member(5, [1, 2, 3]).
true.
```

## 制御構造

### ->/2 (条件分岐)
**構文**: `+Condition -> +Then`
**説明**: 条件が成功すれば Then を実行

### !/0 (カット)
**構文**: `!`
**説明**: バックトラック制御（選択点の除去）

```prolog
?- (X = 1 -> Y = yes; Y = no).
X = 1, Y = yes.

max(X, Y, Max) :- X >= Y, !, Max = X.
max(X, Y, Y).
```

## エラー処理

各述語は以下の条件でエラーを発生させる可能性があります：

- **instantiation_error**: 必要な引数が未束縛
- **type_error**: 引数の型が不正
- **domain_error**: 引数の値が定義域外
- **existence_error**: 存在しない述語の呼び出し

---

*各述語の詳細な動作については、実装コードとテストケースを参照してください。*