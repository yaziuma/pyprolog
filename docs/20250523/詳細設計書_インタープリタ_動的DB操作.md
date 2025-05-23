# 詳細設計書: インタープリタにおける動的データベース操作の修正

## 1. 概要

本設計書は、PyPrologのインタープリタ (`prolog/runtime/interpreter.py`) における動的データベース操作述語 (`asserta/1`, `assertz/1`, `retract/1`) の実装を修正し、ルールや事実の追加・削除が実行時に正しくデータベース (`self.rules`) に反映され、その後のクエリで参照されるようにするための詳細設計を記述する。

## 2. 現状の問題点

改修概要設計書「4.2 インタープリタ (`prolog/runtime/interpreter.py`) の改修 - 5. 動的データベース操作の修正 (`asserta`, `assertz`, `retract`)」に記載の通り、これらの述語による変更がクエリ結果に反映されていない。例えば、`asserta` でルールを追加した直後にそのルールを参照するクエリを実行しても、解が見つからないケースがある。

## 3. 設計方針

`Runtime` クラスに `asserta`, `assertz`, `retract` メソッドを実装または修正し、これらが `self.rules` リスト (またはルールを格納する他のデータ構造) を適切に変更するようにする。これらの述語は、`Runtime.execute` メソッド内で専用の組み込み述語として処理される。

### 3.1 `asserta/1` と `assertz/1`

*   引数として与えられた項 (ルールまたは事実) を `self.rules` リストに追加する。
    *   `asserta(Clause)`: `Clause` を `self.rules` の先頭に追加する。
    *   `assertz(Clause)`: `Clause` を `self.rules` の末尾に追加する。
*   引数の `Clause` は、Prologの節 (Ruleオブジェクトまたはそれに変換可能なTerm) である必要がある。
    *   `Head :- Body` 形式の項は `Rule(Head, Body)` に変換。
    *   単一の項 `Head` (事実) は `Rule(Head, TRUE_TERM)` に変換。
*   これらの述語は成功時に `true` となり、副作用としてデータベースを変更する。通常、バックトラックで元に戻ることはない (論理的更新)。

### 3.2 `retract/1`

*   引数として与えられたテンプレート `ClauseTemplate` にマッチする最初のルールまたは事実を `self.rules` から削除する。
*   `ClauseTemplate` は、`Head :- Body` または単に `Head` の形をとる。
    *   `Head` 部分は、削除対象のルールのヘッドと単一化可能でなければならない。
    *   `Body` 部分 (もしあれば) は、削除対象のルールのボディと単一化可能 (または構造的に同等) でなければならない。
*   マッチング処理:
    1.  `self.rules` 内の各ルール `R` について、`ClauseTemplate` と `R` を比較する。
    2.  比較の際、`ClauseTemplate` 内の変数は新しいローカルなものとして扱う (つまり、`retract((foo(X) :- X))` の `X` は、呼び出し元の `X` とは独立)。
    3.  `ClauseTemplate` のヘッドと `R.head` を単一化試行。
    4.  `ClauseTemplate` にボディがあれば、それと `R.body` を単一化試行 (または構造的同等性チェック)。
    5.  両方が成功すれば、そのルール `R` がマッチする。
*   マッチした最初のルール `R` を `self.rules` から削除し、`retract/1` は成功する。この際、`ClauseTemplate` 内の変数が `R` の対応する部分によって束縛される。
*   マッチするルールが見つからなければ `retract/1` は失敗する。
*   バックトラックすると、次のマッチするルールを探して削除し、変数を束縛する (つまり、`retract/1` は再試行可能)。

## 4. 具体的な修正箇所と内容

### 4.1 `prolog.runtime.interpreter.Runtime` クラス

*   **`self.rules` のデータ構造:**
    *   現状リストであれば、先頭・末尾への追加、指定要素の削除が容易。

*   **`asserta(self, clause_term)` メソッド (組み込み述語として `execute` から呼び出される):**
    1.  `clause_term` を `Rule` オブジェクトに変換するヘルパー `_term_to_rule(term)` を利用。
    2.  変換した `Rule` オブジェクトを `self.rules.insert(0, new_rule)` のようにリストの先頭に追加。
    3.  成功 (`True`) を返す。

*   **`assertz(self, clause_term)` メソッド:**
    1.  `clause_term` を `_term_to_rule(term)` で `Rule` オブジェクトに変換。
    2.  変換した `Rule` オブジェクトを `self.rules.append(new_rule)` のようにリストの末尾に追加。
    3.  成功 (`True`) を返す。

*   **`_term_to_rule(self, term)` ヘルパーメソッド:**
    *   入力 `term` (Termオブジェクト) を解析。
    *   `term` が `Term(':-', [Head, Body])` なら `Rule(Head, Body)` を返す。
    *   `term` がそれ以外 (事実とみなす) なら `Rule(term, TRUE_TERM)` を返す。
    *   不正な形式ならエラー (例: `instantiation_error` や `type_error`)。

*   **`retract(self, clause_template_term)` メソッド (組み込み述語として `execute` から呼び出されるジェネレータ):**
    *   このメソッドは、バックトラックによって複数のルールを削除できるようにジェネレータとして実装する必要がある。
    1.  `clause_template_term` を `_term_to_rule()` で `Rule` オブジェクト `template_rule` に変換。
    2.  `self.rules` のコピーに対してイテレートするか、インデックスを使いながら注意深くイテレートする (リスト編集中にイテレートするため)。
    3.  各ルール `db_rule` in `self.rules` について:
        a.  `template_rule` と `db_rule` をマッチングさせる。
            i.  **重要:** マッチングの際、`template_rule` 内の変数はフレッシュ化する (呼び出し元の束縛に影響されず、また影響を与えないようにするための一時的なもの)。`db_rule` はそのままでよい。
            ii. `fresh_template_head = freshen_term(template_rule.head, ...)`
            iii. `fresh_template_body = freshen_term(template_rule.body, ...)`
            iv. `temp_binding_env = BindingEnvironment()` (このマッチング試行専用の環境)
            v.  `temp_binding_env.unify(fresh_template_head, db_rule.head)` が成功するか？
            vi. `temp_binding_env.unify(fresh_template_body, db_rule.body)` が成功するか？ (ボディのマッチングはより複雑。構造的同等性か、`Body` が変数の場合はその変数が `db_rule.body` に束縛されるなど。)
        b.  両方の単一化 (またはマッチング) が成功した場合:
            i.  `self.rules.remove(db_rule)` でデータベースから削除。
            ii. `clause_template_term` (元の引数) と `db_rule` を現在の呼び出し元の `self.binding_env` で単一化する (これにより `retract` の引数内の変数が束縛される)。
            iii.成功 (`True`) を `yield` する。
            iv. (バックトラックに備えて) `self.rules` に `db_rule` を元に戻し、`self.binding_env` の変更も元に戻す処理が必要。これは `retract` の標準的な動作とは異なる場合がある (一度削除したら戻らないことが多い)。Prologの標準的な `retract/1` は、バックトラックで次の解を探す際に、**削除したルールは元に戻さない**。代わりに、次のマッチするルールを探し、それを削除して成功する。
    4.  ループが終了してもマッチがなければ失敗。

    *   **`retract/1` のバックトラック動作の再考:**
        標準的な `retract/1` は、解を返した後、バックトラックすると **次の** マッチする節を探して削除する。一度削除した節は永続的に削除される。これを実現するには、`execute` 内での `retract` の呼び出し方が重要になる。`retract` 自体は1つのマッチを見つけて削除し、成功を通知する。`execute` がそれを `yield` し、ユーザーが次の解を要求した場合に `retract` を再度呼び出す (または `retract` が内部で次のマッチを探すループを持つ)。

### 4.2 `prolog.runtime.interpreter.Runtime.execute()`

*   **修正内容 (述語 `asserta/1`, `assertz/1`, `retract/1` の処理):**
    *   `goal` が `Term('asserta', [Clause])` の場合:
        *   `self.asserta(Clause)` を呼び出す。
        *   成功すれば `TRUE_TERM` を yield。
    *   `goal` が `Term('assertz', [Clause])` の場合:
        *   `self.assertz(Clause)` を呼び出す。
        *   成功すれば `TRUE_TERM` を yield。
    *   `goal` が `Term('retract', [ClauseTemplate])` の場合:
        *   `self.retract(ClauseTemplate)` を呼び出す (これはジェネレータの想定)。
        *   `retract` から `yield` された各成功に対して、`TRUE_TERM` (または束縛を反映した `goal`) を `yield` する。

## 5. テストケースの例

```prolog
?- assertz(foo(a)).
% Expected: true.
?- foo(X).
% Expected: X = a.

?- asserta(bar(x) :- write(x)), assertz(bar(y) :- print(y)).
% Expected: true.
?- listing(bar).
% Expected: bar(x) :- write(x).
%           bar(y) :- print(y). (listing/1の実装が必要)

?- assertz(data(1)), assertz(data(2)), assertz(data(3)).
% Expected: true.
?- retract(data(X)).
% Expected: X = 1; X = 2; X = 3; false.
?- listing(data).
% Expected: (何も表示されない、全てretractされたため)

% ルールのretract
?- assertz((greet(Name) :- format('Hello, ~w!', [Name]))).
% Expected: true.
?- retract((greet(X) :- Body)).
% Expected: X = Name (内部変数), Body = format('Hello, ~w!', [Name]).
?- greet(world).
% Expected: false (ルールが削除されたため).
```

## 6. 懸念事項と対策

*   **`retract/1` のマッチングの複雑さ:** `retract((Head:-Body))` の `Body` が変数の場合、その変数はマッチしたルールのボディ全体に束縛される。このマッチングロジックを正確に実装する必要がある。`unify` を使うが、変数のスコープに注意。
*   **データベース変更の永続性:** `assert/retract` による変更は、通常、バックトラックで元に戻らない。これは、これらの述語が論理的なデータベースを更新するため。実装上、`self.rules` への変更は直接的。
*   **`retract/1` の再試行可能性:** バックトラックによって `retract/1` が次のマッチする節を探す動作を正しく実装する。これは `Runtime.retract` をジェネレータにし、`execute` がそれを適切に呼び出すことで実現できる。
*   **動的述語と静的述語の区別:** ISO Prologでは、動的に変更可能な述語は `:- dynamic p/N.` で宣言する必要がある。現状のPyPrologではこの区別がないかもしれないが、将来的には考慮点。

## 7. その他

`listing/0` や `listing/1` のようなデバッグ用述語も、これらの動的データベース操作のテストとデバッグに非常に役立つため、合わせて実装を検討すると良い。
