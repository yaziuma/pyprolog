# テスト統合・削減計画

**分析日**: 2026-02-04
**分析者**: Gemini 2.5 Pro + GPT-5.2 Codex
**対象**: pyprolog テストスイート（ベンチマーク除外）

---

## エグゼクティブサマリー

### 現状
- **総テストファイル数**: 43個
- **総テストケース数**: 約590個
- **検出された重複パターン**: 9つの主要パターン + ドキュメント重複2件
- **削減可能数**: 約30テスト（5%削減）＋アーキテクチャ改善による追加削減の可能性

### 主要な発見
1. **test_interpreter.py の肥大化**: 専用テストスイートと機能が重複
2. **医療診断シナリオの多重化**: 5箇所で同一データセットを使用
3. **I/O系の多層重複**: 4つのテストスイートで類似テストを実施
4. **ドキュメント上の重複**: 同名テストが2回記載（要修正）

### 重要な警告
⚠️ **単純な削除は危険**: レイヤー跨ぎ（unit/integration）の統合保証が失われる可能性
⚠️ **日本語サポートの境界面**: 最低1本のE2E日本語テスト必須
⚠️ **順序依存・副作用**: `asserta/assertz`、`cut`、`findall` は重複に見えても別価値

---

## 詳細分析

### 1. 重複パターン一覧

#### パターンA: test_interpreter.py の分解（Gemini発見）
**影響度**: 🔴 高
**重複箇所**:
- `test_list_operations` → `tests/runtime/test_list_operations.py` でカバー済み
- `test_arithmetic_operations`, `test_built_in_arithmetic` → `tests/runtime/test_math_interpreter.py` でカバー済み
- `test_dynamic_predicates` → `tests/runtime/test_dynamic_predicates.py` でカバー済み
- `test_built_in_unification` → `tests/runtime/test_built_in_unification.py` でカバー済み
- `test_io_operations` → `tests/runtime/test_io_predicates.py` でカバー済み

**推奨アクション**: これらを削除し、インタプリタループ自体の統合テストのみに集中

**リスク**: パーサ → ランタイム → I/O の接続点で起きる不整合を検出できなくなる可能性
**対策**: 最低限のE2Eテスト（1-2本）を残す

---

#### パターンB: 参照外しロジックの重複（Gemini発見）
**影響度**: 🟡 中
**重複箇所**:
- `tests/runtime/test_logic_interpreter.py`:
  - `test_circular_reference_detection`
  - `test_dereference`
  - `test_dereference_complex_chain`
- `tests/core/test_variable_dereferencing.py`:
  - `test_circular_reference_detection`
  - `test_simple_dereferencing`
  - `test_chain_dereferencing`

**推奨アクション**: `test_logic_interpreter.py` から削除し、`test_variable_dereferencing.py` を正式な情報源とする

**リスク**: 低（同一レイヤー内の重複）

---

#### パターンC: 医療診断テストの多重化（Codex拡張発見）
**影響度**: 🔴 高
**重複箇所**（Gemini: 2箇所 → Codex: 5箇所）:
1. `tests/japanese/test_medical_diagnosis_jp.py`（専用テストスイート）
2. `tests/integration/test_end_to_end.py::test_medical_diagnosis_japanese`
3. `tests/integration/test_fixed_medical.py`
4. `tests/runtime/test_math_interpreter.py`（symptom score）
5. `tests/runtime/test_enhanced_runtime.py`（medical_kb_basic）

**推奨アクション**:
1. 専用の日本語テストスイート（1）を正式な情報源とする
2. 他4箇所は削除
3. 医療KBデータを `tests/fixtures/medical_kb.pl` に集約して再利用

**リスク**: 日本語サポートの境界面（scanner/parser/functor-mapper/runtime）での不整合検出不能
**対策**: 最低1本の日本語E2Eテストを必ず維持

---

#### パターンD: リストメンバーシップの重複（Gemini発見）
**影響度**: 🟢 低
**重複箇所**:
- `tests/runtime/test_recursive_rules.py::test_member_predicate`
- `tests/runtime/test_list_operations.py::test_member_*`（包括的）

**推奨アクション**: `test_recursive_rules.py` から削除

**リスク**: 低

---

#### パターンE: listing述語テストの重複（Gemini発見）
**影響度**: 🟡 中
**重複箇所**:
- `tests/runtime/test_listing_predicates.py::test_listing_zero_predicate_basic`
- `tests/integration/test_listing_export_integration.py::test_listing_shows_all_predicates`

**推奨アクション**: 単体テストを統合テストスイートにマージ

**リスク**: 中（レイヤー跨ぎの可能性）

---

#### パターンF: I/O系の多層重複（Codex発見）
**影響度**: 🔴 高
**重複箇所**:
- `tests/runtime/test_io_predicates.py`
- `tests/runtime/test_peek_char.py`
- `tests/runtime/test_exception_propagation.py`
- `tests/unified_input/*`

**推奨アクション**:
1. 基本I/O操作は `test_io_predicates.py` に集約
2. `test_peek_char.py` のエッジケースのみ残す
3. 並行実行系（`unified_input/*`）は別価値として維持

**リスク**: 高（スレッド/統一入力の退行）
**対策**: 並行実行系テストは削除しない

---

#### パターンG: 算術/比較の重複（Codex発見）
**影響度**: 🟡 中
**重複箇所**:
- `tests/runtime/test_math_interpreter.py`
- `tests/runtime/test_arithmetic_edge_cases.py`
- `tests/runtime/test_interpreter.py`

**推奨アクション**: パラメータ化テストで統合（`test_math_interpreter.py` に集約）

**リスク**: 低

---

#### パターンH: メタ述語の重複（Codex発見）
**影響度**: 🟡 中
**重複箇所**:
- `tests/runtime/test_meta_predicates.py`
- `tests/runtime/test_interpreter.py`
- `tests/integration/test_end_to_end.py`

**推奨アクション**: `test_meta_predicates.py` に集約

**リスク**: 中（レイヤー跨ぎの可能性）

---

#### パターンI: cut/否定/バックトラックの重複（Codex発見）
**影響度**: 🔴 高
**重複箇所**:
- `tests/runtime/test_logic_interpreter.py`
- `tests/runtime/test_iterative_execution.py`
- `tests/runtime/test_interpreter.py`
- `tests/integration/test_end_to_end.py`

**推奨アクション**: 慎重に統合（順序・副作用の保証が重要）

**リスク**: 高（順序依存・副作用の退行）
**対策**: 削除前に順序保証の確認が必須

---

#### パターンJ: 演算子の重複（Codex発見）
**影響度**: 🟢 低
**重複箇所**:
- `tests/core/test_operators.py`
- `tests/core/test_new_operators.py`
- `tests/parser/test_parser.py`（operator precedence）

**推奨アクション**: パーサーテストは別価値として維持、core系は統合可能

**リスク**: 低

---

#### 🚨 **パターンK: ドキュメント上の重複（Codex発見・最優先）**
**影響度**: 🔴 最優先修正
**重複箇所**:
1. `tests/unified_input/test_unified_input_system.py`: **`test_initial_state` が2回記載**
2. `tests/runtime/test_peek_char.py`: **`test_at_end_of_stream_progression` が2回記載**

**推奨アクション**:
1. 実ファイルを確認し、実際に重複しているか検証
2. 重複していれば統合、なければドキュメント修正

**リスク**: なし（ドキュメント整合性の問題）

---

## 実装プラン

### フェーズ1: ドキュメント整合性修正（最優先）
**期間**: 即時
**タスク**:
- [ ] `test_initial_state` の重複確認・修正
- [ ] `test_at_end_of_stream_progression` の重複確認・修正
- [ ] `docs/non_benchmark_test_cases.md` を再生成

**リスク**: なし

---

### フェーズ2: 同一レイヤー内の重複削減
**期間**: 1-2週間
**タスク**:
- [ ] パターンB: 参照外しロジックの統合
- [ ] パターンD: リストメンバーシップの削除
- [ ] パターンG: 算術/比較のパラメータ化統合
- [ ] パターンJ: 演算子テストの統合

**リスク**: 低
**削減効果**: 約10-15テスト

---

### フェーズ3: データ共有化・fixture化
**期間**: 1週間
**タスク**:
- [ ] 医療KBデータを `tests/fixtures/medical_kb.pl` に集約
- [ ] 日本語テストデータを `tests/fixtures/japanese_samples.pl` に集約
- [ ] 各テストファイルからfixtureを参照するように修正

**リスク**: 低
**削減効果**: コード重複削減（テスト数は変わらず）

---

### フェーズ4: 統合テストの再設計（慎重に）
**期間**: 2-3週間
**タスク**:
- [ ] パターンA: `test_interpreter.py` の分解計画を策定
- [ ] パターンC: 医療診断テストの統合計画を策定
- [ ] パターンF: I/O系の統合計画を策定
- [ ] **各計画についてCodexにレビューを依頼**
- [ ] カバレッジ計測（削減前後）
- [ ] 段階的に削減実施

**リスク**: 高（レイヤー跨ぎの統合保証）
**削減効果**: 約10-15テスト

**必須条件**:
- 削減前のカバレッジ: 記録
- 削減後のカバレッジ: 維持または向上
- 最低1本の日本語E2Eテスト維持
- 並行実行系テストは削除しない

---

### フェーズ5: アーキテクチャ改善（オプション）
**期間**: 4週間以上
**タスク**:
- [ ] テスト分類マーカーの導入: `@pytest.mark.layer("unit|integration|system")`
- [ ] 機能単位の再配置: `tests/features/unification/`, `tests/features/io/`
- [ ] `test_end_to_end.py` を代表シナリオ数本に絞る
- [ ] パフォーマンステストを `@pytest.mark.slow` で分離

**リスク**: 中（大規模リファクタリング）
**削減効果**: 長期的なメンテナンス性向上

---

## リスク管理ガイドライン

### 削除前チェックリスト
- [ ] カバレッジ計測（削減前）
- [ ] 削除対象テストが検証している機能を特定
- [ ] 他のテストで同じ機能がカバーされているか確認
- [ ] レイヤー跨ぎの統合保証が失われないか確認
- [ ] 日本語サポート境界面のテストが維持されているか確認
- [ ] 順序依存・副作用のテストが維持されているか確認

### 削除後チェックリスト
- [ ] カバレッジ計測（削減後）
- [ ] カバレッジが維持されているか確認（同等または向上）
- [ ] 全テストが成功するか確認
- [ ] 統合テスト（E2E）が成功するか確認
- [ ] 日本語テストが成功するか確認

### 緊急時のロールバック計画
- Git履歴から削除前の状態を復元
- カバレッジレポートを比較
- 失われた機能を特定し、テストを復活

---

## 期待効果

### 短期的効果（フェーズ1-2）
- テスト数: 590 → 575（約2.5%削減）
- 実行時間: わずかに短縮
- メンテナンス負荷: 軽減

### 中期的効果（フェーズ3-4）
- テスト数: 575 → 560（約5%削減）
- 実行時間: 5-10%短縮
- コード重複: 大幅削減
- メンテナンス負荷: 大幅軽減

### 長期的効果（フェーズ5）
- テストアーキテクチャの明確化
- 機能追加時のテスト配置が明確に
- 新規メンバーのオンボーディング容易化

---

## 付録A: 分析ツール出力

### Gemini分析
- 出力ファイル: `.claude/docs/research/test-duplication-analysis.md`
- 主要発見: 5パターン、5%削減可能

### Codex分析
- 主要発見: 9パターン + ドキュメント重複2件
- 重要な警告: レイヤー跨ぎの統合保証、順序依存・副作用、日本語サポート境界面

---

## 付録B: 参考資料

- `docs/non_benchmark_test_cases.md`: 全テストケース一覧
- `.claude/docs/research/test-duplication-analysis.md`: Gemini分析結果
- Codex分析結果: `/tmp/claude-1000/-home-yuichi-projects-prolog-mcp-group-pyprolog/tasks/b5267a1.output`

---

**次のステップ**: フェーズ1（ドキュメント整合性修正）から開始することを推奨
