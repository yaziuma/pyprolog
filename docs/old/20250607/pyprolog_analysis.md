# pyprologインタープリターの問題分析と改善提案

## 問題の症状

医療診断Prologシステムにおいて、`患者診断/5`述語が以下の動作を示す：

- 述語実行は開始される
- 内部の`診断/4`や関連述語呼び出し時にサイレントフェイル
- エラーメッセージなし
- デバッグ出力で呼び出し直前まで実行確認、その後無応答

## 推定される根本原因

### 1. 複雑な引数処理における失敗

```python
# pyprolog/runtime/interpreter.py の execute メソッド
def execute(self, goal: Any, env: BindingEnvironment) -> Iterator[BindingEnvironment]:
    # 引数が5個の複雑な項（リスト、変数、アトム、数値混在）
    # の処理で内部的に失敗している可能性
```

**問題箇所候補：**
- 引数の型変換処理
- 環境スタックの管理
- メモリ管理の問題

### 2. findall/3とsort/3の組み合わせ

```prolog
findall([疾患名, 信頼度], 
        (疾患(疾患名), 信頼度計算(...), 信頼度 > 0.1), 
        未ソートリスト),
sort(2, @>=, 未ソートリスト, 診断リスト)
```

**課題：**
- `findall/3`実装の不完全性
- `sort/3`の未実装または不安定性
- 複雑なゴール処理での例外処理不備

### 3. 環境バインディングの破綻

```python
# pyprolog/core/binding_environment.py
class BindingEnvironment:
    def unify(self, term1, term2):
        # 複雑な項の単一化時にバインディング環境が
        # 破綻している可能性
```

## 改善提案

### 1. 詳細トレース機能の実装

```python
class Runtime:
    def __init__(self, rules=None, debug_trace=False):
        self.debug_trace = debug_trace
        self.trace_stack = []
    
    def execute(self, goal, env):
        if self.debug_trace:
            self.trace_call(goal, env)
        try:
            for result in self._execute_internal(goal, env):
                if self.debug_trace:
                    self.trace_exit(goal, result)
                yield result
        except Exception as e:
            if self.debug_trace:
                self.trace_fail(goal, e)
            raise
    
    def trace_call(self, goal, env):
        indent = "  " * len(self.trace_stack)
        print(f"{indent}CALL: {goal} with {env.bindings}")
        self.trace_stack.append(goal)
    
    def trace_exit(self, goal, result):
        indent = "  " * (len(self.trace_stack) - 1)
        print(f"{indent}EXIT: {goal} -> {result.bindings}")
        self.trace_stack.pop()
    
    def trace_fail(self, goal, error):
        indent = "  " * (len(self.trace_stack) - 1)
        print(f"{indent}FAIL: {goal} - {error}")
        self.trace_stack.pop()
```

### 2. エラー報告の強化

```python
def execute(self, goal, env):
    try:
        # 既存の実行ロジック
        pass
    except Exception as e:
        # Pythonレベルの例外を詳細ログ出力
        logger.error(f"Python exception in goal {goal}: {e}", exc_info=True)
        # Prologレベルでの適切なエラー報告
        raise PrologError(f"Execution failed for {goal}: {str(e)}")
```

### 3. 組み込み述語の実装確認

**必要な組み込み述語：**
- `sort/3` - ソート機能
- `length/2` - リスト長計算
- `sum_list/2` - リスト合計
- `member/2` - メンバーチェック（既に実装済み）

```python
class SortPredicate(BuiltinPredicate):
    def __init__(self, key_arg, order_arg, list_arg, result_arg):
        super().__init__(key_arg, order_arg, list_arg, result_arg)
    
    def execute(self, runtime, env):
        # sort/4 の実装
        # sort(Key, Order, List, Sorted)
        pass

class LengthPredicate(BuiltinPredicate):
    def __init__(self, list_arg, length_arg):
        super().__init__(list_arg, length_arg)
    
    def execute(self, runtime, env):
        # length/2 の実装
        pass
```

### 4. ストレステストの実装

```python
def test_complex_predicate_calls():
    """複雑な述語呼び出しパターンのテスト"""
    runtime = Runtime(debug_trace=True)
    
    # 5引数の複雑な述語テスト
    test_cases = [
        "test_pred([a,b,c], 30, [cond1], var1, var2)",
        "nested_call(arg1, complex_term(x,y), [1,2,3], result)",
        "findall_test(X, (fact(X), X > 0), List)"
    ]
    
    for test_case in test_cases:
        try:
            result = runtime.query(test_case)
            print(f"SUCCESS: {test_case} -> {result}")
        except Exception as e:
            print(f"FAILED: {test_case} -> {e}")

def test_builtin_predicates():
    """組み込み述語の個別テスト"""
    runtime = Runtime()
    
    # 各組み込み述語の単体テスト
    tests = [
        "findall(X, member(X, [1,2,3]), L)",
        "sort(0, @<, [3,1,2], S)",
        "length([a,b,c], N)",
        "sum_list([1,2,3], Sum)"
    ]
    
    for test in tests:
        # 個別テスト実行
        pass
```

## 医療診断KB用の回避策

### 段階的デバッグアプローチ

```prolog
% 1. 最小限のテスト述語
simple_test :- write('Simple test passed'), nl.

% 2. 単一疾患テスト
single_disease_test(Disease) :-
    疾患(Disease),
    write('Found disease: '), write(Disease), nl.

% 3. 症状マッチテスト
symptom_match_test(Disease, Symptoms) :-
    症状マッチスコア(Disease, Symptoms, Score),
    write('Score for '), write(Disease), write(': '), write(Score), nl.

% 4. 段階的な患者診断テスト
patient_diagnosis_minimal(Symptoms, Result) :-
    % findallを使わない簡略版
    疾患(Disease),
    症状マッチスコア(Disease, Symptoms, Score),
    Score > 0.1,
    Result = [Disease, Score].
```

### 代替実装パターン

```prolog
% findall/3を使わない診断実装
診断_代替(患者症状, 患者年齢, 患者既往歴, 診断リスト) :-
    bagof(
        [疾患名, 信頼度],
        診断候補(疾患名, 患者症状, 患者年齢, 患者既往歴, 信頼度),
        診断リスト
    ).

診断候補(疾患名, 症状リスト, 年齢, 既往歴, 信頼度) :-
    疾患(疾患名),
    信頼度計算(疾患名, 症状リスト, 年齢, 既往歴, 信頼度),
    信頼度 > 0.1.
```

## 結論

この問題は以下の要因の組み合わせによると推測されます：

1. **複雑な引数処理の不備** - 5引数述語での内部処理失敗
2. **組み込み述語の未実装/不安定性** - `findall/3`, `sort/3`等
3. **例外処理の不完全性** - サイレントフェイルの原因
4. **デバッグ機能の不足** - 問題特定の困難さ

最優先で実装すべきは**詳細トレース機能**と**エラー報告の強化**です。これにより問題の正確な発生箇所を特定し、根本的な修正が可能になります。
