# フォールバック実装の徹底調査（Phase 0）

**調査日**: 2026-02-04
**対象**: pyprolog プロジェクト全体
**目的**: 既存コードに「旧実装を残すフォールバック」が存在しないか検証

## 重要な区別

- **❌ NG**: 旧実装を残すフォールバック（例: `use_old_implementation` フラグ）
- **✅ OK**: Prolog的な意味があるフォールバック（例: ルールマッチング失敗時に次のルールを試す）

---

## 検出されたフォールバック

### ❌ NG: 削除対象（旧実装保持）

**1 件検出**

#### 1. `pyprolog/runtime/interpreter.py:82` - `use_iterative_execution` フラグ

```python
self.use_iterative_execution = False  # Feature flag for iterative execution
```

**用途**:
- デフォルトは `False`（再帰的実行）
- `True` にすると `execute_iterative()` を使用（スタックベース実行）
- RecursionError を回避するための新実装だが、デフォルトでは旧実装を使用

**判定理由**:
- 設計ドキュメント（`execute_single_goal_integrated_design.md`）のPhase 4に「Flip `use_iterative_execution = True`」とあり、**新実装への移行が未完了**
- 現状は旧実装（再帰版）と新実装（iterative版）を共存させている
- これは典型的な「旧実装を残すフォールバック」パターン

**影響範囲**:
- `interpreter.py:483-485`: フラグによる分岐
- `interpreter.py:880-965`: `execute_iterative()` メソッド本体
- 設計ドキュメント複数件で言及
- `tests/benchmark/test_benchmarks.py:42`: ベンチマークでのみ有効化

**削除推奨アクション**:
1. 全テスト（532件）を `use_iterative_execution=True` で実行し、全通過を確認
2. デフォルトを `True` に変更
3. 旧実装（再帰版の分岐）を削除
4. フラグ自体を削除

---

### ✅ OK: Prolog的意味あり（削除不要）

**6 パターン検出**

#### 1. `pyprolog/runtime/execution_frames.py:189` - コメント「fallback/transition case」

```python
# This is a fallback/transition case
```

**用途**:
- `OperatorFrame` で conjunction `,` が来た場合、`GoalSeqFrame` に変換するための暫定処理
- Prolog のルールマッチング的な意味での「次の処理へのフォールバック」

**OK理由**:
- 旧実装保持ではなく、フレームタイプ間の遷移ロジック
- Prolog の実行モデル上の正当な分岐

---

#### 2. `pyprolog/core/binding_environment.py:44` - `index2_miss_or_fallback` 統計カウンタ

```python
"index2_miss_or_fallback": 0,
```

**用途**:
- インデックスヒットしなかった場合のフォールバックパスを計測
- パフォーマンス分析用の統計値

**OK理由**:
- 実装切り替えではなく、インデックス最適化の有無を測定する統計情報
- 「フォールバック」はここでは「最適化できなかった経路」の意味

---

#### 3. `pyprolog/runtime/io_manager.py:72,81` - `enable_threading()` / `disable_threading()`

```python
def enable_threading(self):
    """マルチスレッドモード（真の継続実行）を有効化"""
    self.unified_input.enable_threading()

def disable_threading(self):
    """シングルスレッドモードに切り替え"""
    self.unified_input.disable_threading()
```

**用途**:
- REPL での対話実行時にマルチスレッドモード（真の継続実行）を有効化
- バッチ実行時はシングルスレッドモード

**OK理由**:
- 旧実装/新実装の切り替えではなく、**実行環境に応じた機能切り替え**
- REPL（対話）とバッチ（非対話）で異なる入出力制御が必要（Prolog処理系の正当な要求）
- どちらも現役の実装で、環境に応じて使い分けている

---

#### 4. `pyprolog/runtime/interpreter.py:487` - コメント「for legacy recursive path」

```python
# Check if logical operator (for legacy recursive path)
```

**用途**:
- `use_iterative_execution=False` の際の論理演算子処理パス

**現状判定**:
- **Phase 4 未完了の副作用**
- `use_iterative_execution` フラグが削除されればこのコメントも不要になる
- フラグ削除後、このパスは削除対象

---

#### 5. `pyprolog/runtime/builtins.py` - `clause_val` 型による分岐

**用途**:
- `asserta/assertz/retract` での入力値の型に応じた処理
- Variable/Atom/Term の型によって異なる処理が必要

**OK理由**:
- 旧実装保持ではなく、**Prolog のデータ型に応じた正当な分岐**
- Prolog 言語仕様上、型による処理の違いは必須

---

#### 6. `execute` / `solve_goal` のバリアント

**検出された複数の execute メソッド**:
- `execute()`: 標準エントリポイント
- `execute_iterative()`: スタックベース版
- `execute_with_trace()`: トレース機能付き
- `_execute_internal()`: 内部実装
- `_execute_builtin()`: 組み込み述語用
- 他多数

**用途**:
- それぞれ異なる責務を持つメソッド
- 名前の接頭辞/接尾辞で役割を区別（`_` = プライベート、`with_trace` = 機能拡張）

**OK理由**:
- 機能分離されたメソッド群であり、旧実装保持ではない
- ただし `execute_iterative()` は Phase 4 完了後に `execute()` と統合される可能性あり

---

### ⚠️ 要確認

**0 件**

---

## サマリー

| 判定 | 件数 | 内容 |
|------|------|------|
| ❌ 削除対象 | **1** | `use_iterative_execution` フラグ |
| ⚠️ 要確認 | **0** | - |
| ✅ 問題なし | **6** | Prolog的意味のあるフォールバック、統計情報、機能切り替え |

---

## 結論

### 検出された禁止パターン: 1件

**`use_iterative_execution` フラグ** が唯一の「旧実装を残すフォールバック」に該当。

### 削除方針

設計ドキュメント（`execute_single_goal_integrated_design.md`）の Phase 4 に従い：

1. ✅ **Phase 1-3 完了確認**: `_execute_single_goal()` の独立化、iterative実装の完成
2. ⏳ **Phase 4 実行**:
   - 全テスト（532件）を `use_iterative_execution=True` で実行
   - パフォーマンス検証（ベンチマークで95-98%維持）
   - デフォルトを `True` に変更
   - 旧実装（再帰版分岐）の削除
   - フラグ自体の削除

### その他の検出パターン

- **`enable_threading/disable_threading`**: 実行環境に応じた機能切り替えで正当
- **`index2_miss_or_fallback`**: 統計情報で問題なし
- **`fallback/transition case` コメント**: フレーム遷移ロジックで問題なし
- **型による分岐**: Prolog言語仕様上必須

---

## 次のアクション

1. **Phase 4 の実行**: `use_iterative_execution` を段階的にデフォルト化
2. **検証完了後の削除**: フラグと旧実装の完全削除
3. **ドキュメント更新**: 削除完了をデザインドキュメントに記録

---

## 調査メタデータ

**検索パターン**:
- `use_*` フラグ
- `feature_flag|enable_|disable_|legacy|fallback|old_implementation`
- `if.*use_|if.*legacy|if.*old_`
- `deprecated|obsolete|TODO.*remove`
- `execute` / `solve_goal` のバリアント

**対象ディレクトリ**: `pyprolog/`（テストディレクトリ除く）

**調査完了**: 2026-02-04
