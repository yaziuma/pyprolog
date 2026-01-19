# 後方互換性 記載調査レポート

## 調査概要
- 対象: `pyprolog/` と `tests/` 配下のコード
- 検索語: 「後方互換」「互換性」「レガシー」
- 目的: 後方互換性に関する明示的な記載の所在と内容を列挙

## ソースコード内の記載
- `pyprolog/runtime/io_manager.py:91-120`
  - 「従来API（後方互換性）」と明示し、`read_*_from_current` などのレガシーAPIを保持。
  - コメントで「既存のGetCharPredicateとの互換性のため保持」「新しいIOPredicate統合後は使用されない」と記載。
- `pyprolog/util/functor_mapper.py:136-147`
  - 「後方互換性のためのメソッド（既存のインターフェースを維持）」として旧命名メソッドをラップ。
- `pyprolog/util/logger.py:69-80`
  - `setup_logger()` を「レガシー互換性のために残された関数」と明記。
- `pyprolog/core/operators.py:361-362`
  - 演算子登録で「後方互換性のため、記号のみのキーも保持」と記載。
- `pyprolog/core/binding_environment.py:69`
  - `unify()` が「merge_bindings.py との互換性のため」と記載。
- `pyprolog/runtime/enhanced_runtime.py:245-263`
  - トレース表示の docstring が「レガシー・詳細版」と表現（互換性維持を示唆）。

## テストコード内の記載
- `tests/unified_input/test_io_manager_integration.py:5,50,54,145,436`
  - 新旧API共存や「完全な後方互換性」の維持を前提にしたテスト説明・コメント。
- `tests/util/test_functor_mapper.py:181,184,190`
  - 後方互換性メソッドの検証を明記。
- `tests/integration/test_end_to_end.py:307-311`
  - 「標準Prologとの互換性」テストの記載（後方互換性とは別種だが互換性を強調）。

## 補足
- ドキュメント（`README.md` や `docs/`）にも「後方互換性」記載が多数ありますが、本レポートはコード内の明示記述に限定しています。

---

## 追加調査（特定条件のみ解決可能/テスト専用ハック/互換性）

### テスト専用ハック・限定条件
- `tests/tools/test_explain_tool.py`
  - 失敗が既知である旨のコメント（`TODO: This test fails...`）が残っており、現状の不具合を前提にしたテストになっている。

## IOPredicate統合の調査結果（コード＋git log）
- 結論: 統合は実装済みだが、旧経路が残るため完全置き換えは未完。

### コード上の根拠
- `pyprolog/runtime/io_predicates.py` に IOPredicate 具象実装（get_char/read_line/peek_char）が存在し、統一入力システム対応版として実装済み。
- `pyprolog/runtime/io_predicate.py` が `runtime.io_manager.request_input(...)` を使用する統一経路を持つ一方、`_request_input_legacy()` によるフォールバックが残存。
- `pyprolog/runtime/builtins.py` の factory が `UNIFIED_INPUT_AVAILABLE` で統一版/従来版を分岐。
- `pyprolog/runtime/io_manager.py` に「従来API（後方互換性）」の記載があり、`read_*_from_current` が保持。

### git log の根拠
- 直近ログには「統一入力システム本体実装完了」「統一入力システム完全実装と既存I/Oテスト互換性修復」などのコミットはあるが、IOPredicate統合完了を直接示すコミット名は見当たらない。
- 例: `9d6aaa5 feat: 統一入力システム本体実装完了`
- 例: `48fce68 feat: 統一入力システム完全実装と既存I/Oテスト互換性修復`
