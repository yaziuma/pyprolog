# `tests/test_interpreter.py` リファクタリングにおける課題と修正ログ (2025-05-20)

## 概要

`prolog/interpreter.py` の `Runtime` クラスおよび関連モジュールのリファクタリングに伴い、`tests/test_interpreter.py` のテストケースが多数失敗する問題が発生した。
本ドキュメントは、その修正過程と発生したエラー、およびその分析結果を記録する。

## 初期状態のテスト失敗 (リファクタリング直後)

`Runtime` クラスのメソッド ( `insert_rule_left`, `insert_rule_right`, `remove_rule`, `register_function` ) が未実装だったため、`AttributeError` が多数発生。

## 修正フェーズ1: `Runtime` へのメソッド追加

1.  **`insert_rule_left`, `insert_rule_right`, `remove_rule` の実装:**
    *   `prolog/interpreter.py` の `Runtime` クラスに、それぞれ `asserta`, `assertz`, `retract` のエイリアスとして実装。
    *   `retract` は部分的な実装であり、完全なユニフィケーションベースのマッチングは未実装。
    *   これにより、これらのメソッド呼び出しに関する `AttributeError` は解消。

2.  **`register_function` の実装:**
    *   `prolog/interpreter.py` の `Runtime` クラスにプレースホルダーとして実装。
    *   `prolog/types.py` から `TermFunction` をインポートし、`Runtime.execute` で `TermFunction` インスタンスを処理するロジックを追加。
        *   `TermFunction._execute_func()` を呼び出し、成功すれば `TRUE_TERM` を yield する単純な実装。
    *   これにより、`register_function` 呼び出しに関する `AttributeError` は解消。

3.  **`standardize_apart` のための `get_next_scope_id` の追加:**
    *   `Runtime.execute` 内でルールをフレッシュにする際に `binding_env.get_next_scope_id()` を呼び出していたが、`BindingEnvironment` に未実装だった。
    *   `prolog/binding_environment.py` の `BindingEnvironment` クラスに `_next_scope_id` カウンタと `get_next_scope_id()` メソッドを追加。
    *   これにより、`AttributeError: 'BindingEnvironment' object has no attribute 'get_next_scope_id'` が解消。

## 修正フェーズ2: `tests/test_interpreter.py` の修正と新たな問題

`AttributeError` 解消後、`tests/test_interpreter.py` を実行すると、依然として多くのテスト (18 failed, 9 passed) が失敗。
主な原因はアサーションの失敗 (`assert False is True` など)。

1.  **`test_insert_rule_left` / `test_insert_rule_right` のアサーション修正:**
    *   `asserta` はリストの先頭 (`rules[0]`)、`assertz` はリストの末尾 (`rules[-1]`) にルールを挿入するため、テスト内のアサーションインデックスを修正。
    *   誤: `runtime.rules[1]` (asserta), `runtime.rules[4]` (assertz)
    *   正: `runtime.rules[0]` (asserta), `runtime.rules[-1]` (assertz)

2.  **シングルトンインスタンスの参照修正:**
    *   テストケース内で `TRUE()` (旧 `prolog.types.TRUE`) が使用されていた箇所を `TRUE_TERM` (新 `prolog.core_types.TRUE_TERM`) に修正。
    *   同様に `FALSE` -> `FALSE_TERM`, `CUT` -> `CUT_SIGNAL` への置き換えが必要。

3.  **インポート文の修正:**
    *   `tests/test_interpreter.py` の先頭で `from prolog.types import Variable, Term, FALSE, TRUE, CUT` や `from prolog.interpreter import Rule` となっていた箇所を、リファクタリング後の正しいモジュール (`prolog.core_types`) からインポートするように修正。
        *   `from prolog.core_types import Variable, Term, Rule, FALSE_TERM, TRUE_TERM, CUT_SIGNAL`

4.  **`runtime.execute()` の戻り値に関するテストロジックの再検討:**
    *   旧 `execute` は `FALSE` インスタンスなどを yield していた可能性があるが、新 `execute` は `TRUE_TERM`, `FALSE_TERM`, `CUT_SIGNAL` または何も yield しない。
    *   テスト内で `runtime.execute()` の結果を直接評価している箇所は、新しい動作に合わせてロジックを見直す必要がある。
        *   例: `if not isinstance(item, FALSE):` -> `if item is not FALSE_TERM and item is not None:`

## 現在の状況と残存する課題 (2025-05-20 午後5:28時点)

`tests/test_interpreter.py` に対して上記の修正 (1, 2, 3, 4の一部) を適用した結果、Pylance および Ruff から多数の型エラーや未定義名エラーが報告されている。
これは、`replace_in_file` による一括置換がファイル全体に正しく適用されず、依然として古いシンボル参照 (特に `prolog.types` からのインポートや `TRUE`, `FALSE`, `CUT` の直接使用) が残存しているため。

**Pylance エラーの例:**
*   `Line 54: "args" は "None" の既知の属性ではありません` (多数の型で発生)
*   `Line 70: "match" は "None" の既知の属性ではありません`
*   `Line 104: "head" は "None" の既知の属性ではありません` (多数の型で発生)
*   `Line 775: "TRUE_TERM" が定義されていません` (インポート修正漏れ)

**Ruff エラーの例:**
*   `Line 775: Undefined name \`TRUE_TERM\`` (インポート修正漏れ)

これらのエラーは、`tests/test_interpreter.py` の先頭のインポート文が完全に `prolog.core_types` を参照するように修正され、ファイル全体で古いシンボル (`TRUE`, `FALSE`, `CUT`) が新しいシングルトン (`TRUE_TERM`, `FALSE_TERM`, `CUT_SIGNAL`) に置き換えられることで解消される見込み。

また、`Parser(...).parse_terms()` や `Parser(...).parse_query()` の戻り値の型と、テストケース内でのそのオブジェクトの扱い方 (e.g., `.args`, `.head` へのアクセス) が、Pylance の型チェックと整合していない箇所が多数見られる。これは `Parser` の返すオブジェクトの型定義や、テスト内での型アサーションの追加が必要であることを示唆している。

次のステップとして、`tests/test_interpreter.py` のインポート文とシンボル参照を完全に修正し、再度テストを実行してPylanceエラーの解消を目指す。
