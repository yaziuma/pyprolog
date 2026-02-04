# _execute_body_direct 反復化実装計画 v2

**作成日**: 2026-02-04
**ステータス**: 設計完了、実装待機
**レビュー**: Codex による改善版（初版レビューの懸念点を反映）

---

## 概要

### 目的
- `_execute_body_direct()` の再帰実装を反復実装に置換
- RecursionError を完全解消（depth 175 → 無制限）
- Prolog セマンティクス（cut, negation, backtracking）を保持

### 現状の問題
- `_execute_body_direct()` が再帰的（`logic_interpreter.py:984`）
- `use_iterative_execution = True` でも RecursionError が発生
- 中量ベンチマーク 2/5 が失敗

---

## アプローチ

### 設計方針
- 既存の `ExecutionState` / フレーム構造を拡張
- `_execute_body_direct` を明示的スタック駆動の反復実装に置換
- `execute_iterative` と同じフレーム駆動コアを共有
- **旧実装へのフォールバックは一切なし**（プロジェクトルール遵守）

### 論理演算子の処理
- **連言 (,/2)**: フラット化 + 継続フレームで処理
- **選言 (;/2)**: 選択点（ChoicePoint）で分岐
- **否定 (\+/1)**: "内側が成功したら即失敗" フレームで処理
- **Cut (!/0)**: 現状の例外伝播の意味論を維持、選択点の破棄後に再送出

---

## データ構造

### Frame（継続/状態）

#### GoalFrame（既存）
- **用途**: 原子ゴール用
- **保持データ**: `_execute_single_goal` のイテレータ

#### GoalSeqFrame（再設計）
- **用途**: 連言の継続を管理
- **変更点**: **前段ゴールのフレームをスタック上に保持**
- **目的**: バックトラック可能にする（初版レビューの懸念を解消）
- **動作**:
  - 後段を段階的にプッシュ
  - 途中の GoalFrame を捨てない
  - バックトラック時に前段の解探索へ戻れる

#### NegationFrame（新規）
- **用途**: `\+/1` 専用
- **保持データ**:
  - `entry_stack_depth`: 否定開始時のスタック深度
  - `entry_choice_depth`: 否定開始時の選択点深度
  - `inner_started`: 内側ゴールが開始されたか
  - `inner_succeeded`: 内側ゴールが成功したか
- **Cut 処理**: 内側の Cut を捕捉して成功扱い（否定失敗）
- **束縛漏れ防止**: トレイル巻き戻しを確実に実行

### ChoicePoint（既存）
- **用途**: 選言の分岐管理
- **保持データ**:
  - `stack_depth`: スタック深度
  - `alternative_frame`: 右分岐のフレーム

### ExecutionState
- **Cut Barrier の追加**:
  - `_execute_body_direct` 開始時のスタック深度を記録
  - `apply_cut()` で当該スコープの選択点を削除
  - Cut のスコープを正確に限定（初版レビューの懸念を解消）

---

## アルゴリズム

### 反復ドライバ（execute_iterative と共有）

#### 1. 初期化
```python
state = ExecutionState()
state.cut_barrier = len(state.frame_stack)  # Cut barrier 設定
```

#### 2. ゴール投入（push_goal）
- **`,/2` (連言)**:
  - 連言をフラット化して `GoalSeqFrame` に変換

- **`;/2` (選言)**:
  - 右枝の `ChoicePoint` を先に登録
  - 左枝をプッシュ

- **`\+/1` (否定)**:
  - `NegationFrame` をプッシュ
  - その内側ゴールをプッシュ

- **その他**:
  - `GoalFrame` をプッシュ

#### 3. ループ処理

**GoalFrame の処理**:
- 解を返したら:
  - 親が `GoalSeqFrame` なら **フレームを保持したまま** 次ゴールをプッシュ
  - 親がいなければ `yield`
- 枯渇したら:
  - ポップ
  - `choice_points` があれば `backtrack()`

**GoalSeqFrame の処理**:
- "次ゴールを押す" 継続として動作
- **途中の GoalFrame を捨てない**
- バックトラック時に前段の解探索へ戻れる

**NegationFrame の処理**:
- 内側が **1件でも成功**:
  - `inner_succeeded = True`
  - `entry_stack_depth` / `entry_choice_depth` へ復元
  - **否定は失敗**（何も yield しない）

- 内側が **完全失敗**:
  - `yield env` して終了

- 内側で `CutException`:
  - **成功扱い**（否定失敗）にする

#### 4. CutException の処理
- **NegationFrame 内**:
  - 捕捉して **成功扱い**（否定失敗）

- **それ以外**:
  - `apply_cut()` で選択点を削除
  - **再送出**（現行の意味論維持）

---

## 統合ポイント

### pyprolog/runtime/execution_frames.py
- `GoalSeqFrame` の責務変更:
  - 連言の継続管理（バックトラック可能に）

- `NegationFrame` の追加:
  - `\+/1` 用フレーム

- `ExecutionState.push_goal()` の修正:
  - `;/2` と `\+/1` を正しくフレーム化/選択点化

### pyprolog/runtime/interpreter.py
- `execute_iterative()` の更新:
  - 上記フレーム駆動ループに更新
  - `choice_points` が実際に効くようにする

- 連言/選言/否定の扱い:
  - `ExecutionState` に寄せる
  - `execute_iterative` と `_execute_body_direct` のロジックを一致

### pyprolog/runtime/logic_interpreter.py
- `_execute_body_direct` の **完全置換**:
  - 再帰実装を削除
  - 共有の反復ドライバを呼び出す

- **旧再帰版へのフォールバックは削除**（禁止事項対応）

---

## 移行戦略

### 段階的実装（ただし最終的に完全置換）

#### Phase 1: ExecutionState/フレームの拡張
- `GoalSeqFrame` 再設計（バックトラック対応）
- `NegationFrame` 追加
- `push_goal` 修正
- ユニットテスト

#### Phase 2: execute_iterative の更新
- 新ループで動作させる
- 選択点・バックトラックを有効化
- 統合テスト

#### Phase 3: _execute_body_direct の置換
- 新ループ利用に置換
- **再帰版削除**（フォールバックなし）
- 全テスト（532件）実行

#### Phase 4: テスト追加と検証
- 深い連言、選言+cut、否定+cut、混合ネスト
- depth 500+ で RecursionError 発生しないことを確認
- パフォーマンス検証

### 重要な注意事項
**移行完了後は旧再帰版は残さない**（プロジェクトルール遵守）

---

## リスクと対策

### 1. 連言のバックトラック欠落
- **リスク**: 既存 `GoalSeqFrame` は前段ゴールを捨てるため誤動作
- **対策**: フレーム保持型の継続に再設計

### 2. Cut のスコープ誤り
- **リスク**: ChoicePoint の削除範囲がずれると意味論が崩れる
- **対策**: `_execute_body_direct` 開始時に `cut_barrier` を明示設定、`apply_cut()` で限定削除

### 3. 否定の Cut 処理
- **リスク**: `\+` 内の Cut が外へ漏れると不正
- **対策**: `NegationFrame` で Cut を捕捉し「内側成功扱い」に統一

### 4. 解の重複/欠落
- **リスク**: 選択点復元順やフレーム再投入が不適切だと解列が変わる
- **対策**: 代表的な Prolog パターン（連言×選言×否定）で期待解列を固定化

### 5. 性能劣化
- **リスク**: フレーム生成が増える
- **対策**: 連言は事前フラット化、フレーム生成回数を抑制

---

## テストケース（追加必須）

### Cut スコープ
```prolog
% Cut が正しい範囲を刈る
test1 :- (a, !, b) ; c.
test2 :- a, (!, b ; c).
```

### 否定の束縛漏れ
```prolog
% X の束縛が外に出ない
test3 :- \+(X=1), X=2.
test4 :- (\+ (X=1)), X=1.  % 失敗すべき
```

### 否定内の Cut
```prolog
% Cut が \+ の外側を刈らない
test5 :- \+ (a, !, fail).
test6 :- \+ (a, !, true).
```

### バックトラック順序
```prolog
% 正しい順序で探索
test7 :- (A ; B), C.
test8 :- A, (B ; C), D.
```

### 選言内の Cut
```prolog
% B が探索されないこと
test9 :- (A, ! ; B).
```

---

## 工数見積もり

- **Phase 1**: 2日（フレーム拡張）
- **Phase 2**: 2日（execute_iterative 更新）
- **Phase 3**: 1日（_execute_body_direct 置換）
- **Phase 4**: 2日（テスト追加と検証）

**合計**: 7日（Codex 推奨: 6-8日）

---

## 関連ドキュメント

- **初版計画**: `.claude/docs/design/execute_body_direct_iterative_plan.md`
- **Codex レビュー**: Codex による改善提案を反映
- **RecursionError 調査**: `.claude/docs/research/recursion-error-solutions.md`
- **フォールバック調査**: `.claude/docs/research/fallback_investigation_phase0.md`

---

## 承認状況

- **計画策定**: ✅ 完了
- **Codex レビュー**: ✅ 完了（改善版）
- **実装開始**: 待機中

---

**作成者**: Claude Sonnet 4.5 + Codex 5.2
**レビュー者**: Codex 5.2
