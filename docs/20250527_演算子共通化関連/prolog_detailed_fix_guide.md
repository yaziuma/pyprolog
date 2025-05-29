# Prologインタープリター 詳細修正手順ガイド

> Phase 0 の修正手順と結果は [prolog_detailed_fix_guide_phase0_completed.md](./prolog_detailed_fix_guide_phase0_completed.md) を参照してください。

## Phase 1: LogicInterpreter テストの有効化

### Step 5: LogicInterpreter の実装状況確認と修正

**📝 修正対象**: `tests/runtime/test_logic_interpreter.py`

**🎯 目的**: 23個のスキップされているテストの有効化

**📋 修正内容**:

#### 5.1 setup_method の修正

```python
def setup_method(self):
    """各テストの前処理"""
    self.rules = []
    self.env = BindingEnvironment()
    
    # LogicInterpreter の実際の初期化
    try:
        from prolog.runtime.logic_interpreter import LogicInterpreter
        # MockRuntimeを作成してLogicInterpreterを初期化
        mock_runtime = MockRuntime()
        self.logic_interpreter = LogicInterpreter(self.rules, mock_runtime)
    except (ImportError, AttributeError) as e:
        print(f"LogicInterpreter initialization failed: {e}")
        self.logic_interpreter = None
```

#### 5.2 MockRuntime の改良

```python
class MockRuntime:
    """テスト用のモックランタイム（改良版）"""
    
    def __init__(self):
        self.facts = []
        self.rules = []
    
    def execute(self, goal, env):
        """ゴール実行のモック実装"""
        from prolog.core.types import Atom, Term
        
        # 簡単なモック実装
        if isinstance(goal, Atom):
            if goal.name == "true":
                yield env
            elif goal.name == "fail":
                return  # 何も yield しない
        elif isinstance(goal, Term):
            if goal.functor.name == "true":
                yield env
            # その他のゴールは失敗として扱う
        
    def add_fact(self, fact):
        """ファクトを追加"""
        self.facts.append(fact)
    
    def add_rule(self, rule):
        """ルールを追加"""
        self.rules.append(rule)
```

**🧪 テスト方法**:
```bash
python -m pytest tests/runtime/test_logic_interpreter.py -v
```

---

## Phase 1 完了確認

### LogicInterpreter テスト有効化後の確認

```bash
# LogicInterpreter テストの実行
python -m pytest tests/runtime/test_logic_interpreter.py -v

# 全体テスト実行
python -m pytest tests/ -v
```

### 期待される結果

- **スキップ数の減少**: 23 skipped → 0-5 skipped
- **実装されている機能のテスト成功**
- **未実装機能の明確化**

---

## Phase 2: 段階的リファクタリング（安全確認後）

### Phase 0, 1完了後に実施

Phase 0と1が完全に成功した場合のみ、以下のリファクタリングを実施：

1. **未使用クラスの削除**
2. **Number クラスの統合**  
3. **merge_bindings の BindingEnvironment への統合**
4. **アーキテクチャの改善**

---

## チェックリスト

## チェックリスト

> Phase 0 のチェックリストは [prolog_detailed_fix_guide_phase0_completed.md](./prolog_detailed_fix_guide_phase0_completed.md) を参照してください。

### ✅ Phase 1 チェックリスト
- [ ] LogicInterpreter テストの有効化
- [ ] MockRuntime の改良
- [ ] 23件のスキップを最小化

### ✅ Phase 2 チェックリスト（Phase 0, 1完了後）
- [ ] 安全性確認
- [ ] 段階的リファクタリング実施
- [ ] 最終的な品質向上

このガイドに従うことで、**安全かつ確実に問題を解決**し、その後段階的にシステムを改善できます。
