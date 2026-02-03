# Future Improvements

## 完全な RecursionError 解消（depth=1000達成）

### 課題: `_execute_body_direct()` の反復実装

**現状**:
- Phase 3完了後の最大再帰深度: ~175
- 制限要因: `_execute_body_direct()` が conjunction を再帰的に処理

**問題コード**:
```python
# LogicInterpreter._execute_body_direct()
if functor_name == "," and len(body.args) == 2:
    left_goal, right_goal = body.args[0], body.args[1]
    try:
        # ❌ 再帰呼び出し
        for left_env in self._execute_body_direct(left_goal, env):
            yield from self._execute_body_direct(right_goal, left_env)
    except CutException:
        raise
    return
```

**解決策**:
`_execute_body_direct()` を反復的に実装する：

1. **明示的スタックアプローチ**:
   - `ExecutionState` と同様のフレームベースのスタックを使用
   - Conjunction を GoalSeqFrame のように処理
   - Disjunction を OperatorFrame のように処理

2. **実装案**:
```python
def _execute_body_direct_iterative(
    self, body: PrologType, env: BindingEnvironment
) -> Iterator[BindingEnvironment]:
    """Iterative implementation of body execution."""
    stack = []
    stack.append(BodyFrame(body=body, env=env))

    while stack:
        frame = stack[-1]

        if isinstance(frame, ConjunctionFrame):
            # Handle conjunction iteratively
            if frame.current_index >= len(frame.goals):
                yield frame.env
                stack.pop()
            else:
                next_goal = frame.goals[frame.current_index]
                stack.append(BodyFrame(body=next_goal, env=frame.env))

        elif isinstance(frame, AtomicFrame):
            # Delegate to _execute_single_goal
            result = frame.step(self.runtime)
            if result is None:
                stack.pop()
            else:
                yield result

        # ... handle disjunction, negation, etc.
```

3. **必要な新クラス**:
   - `BodyFrame`: 抽象基底クラス
   - `ConjunctionFrame`: Conjunction処理用
   - `DisjunctionFrame`: Disjunction処理用
   - `NegationFrame`: Negation処理用
   - `AtomicFrame`: Atomic goal処理用

4. **期待される成果**:
   - depth=1000での成功（設計目標達成）
   - Python再帰制限の完全回避
   - パフォーマンス: 95%以上維持（設計要件）

5. **実装難易度**: 高
   - 推定工数: 8-12時間
   - 複雑度: Phase 1-3の合計に匹敵
   - リスク: 既存機能への影響、デバッグの困難さ

6. **優先度**: 中
   - 現状（depth=175）で多くのユースケースをカバー
   - 極端に深い再帰が必要なケースは稀
   - パフォーマンスとの トレードオフを考慮

### 代替案: 再帰制限の引き上げ

```python
import sys
sys.setrecursionlimit(3000)  # デフォルト1000 → 3000
```

**メリット**:
- 簡単に実装可能
- depth=500程度まで対応可能

**デメリット**:
- スタックオーバーフローのリスク増加
- 根本的解決ではない
- プラットフォーム依存の問題

### 推奨アプローチ

1. **短期**: 現状維持（depth=175で十分なカバレッジ）
2. **中期**: 必要に応じて再帰制限を引き上げ（2000-3000程度）
3. **長期**: 反復実装を検討（ユーザーからの要求がある場合）

---

**関連**: #execute-single-goal-refactoring
**ステータス**: 今後の課題
**更新日**: 2026-02-03
