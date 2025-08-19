# PyProlog Issue Report: Interactive Input Exception Propagation in Nested Predicates

**Reporter**: prolog_mcp project team  
**Date**: 2025-08-07  
**PyProlog Version**: Source code analysis from docs/library_code/pyprolog-main  
**Status**: ✅ **RESOLVED** (Version 0.3.1)

---

## ✅ 修正完了報告

### 修正結果
この問題は **PyProlog v0.3.1** で完全に修正されました。ネストされた述語でのIOManager例外が正常に伝播されるようになりました。

### 修正内容
1. **Runtime.execute()のAtom処理改善** - `nl`などのIOオペレータの適切な処理
2. **BuiltinPredicate例外処理強化** - `get_char/1`、`read_line/1`述語での例外透過性確保
3. **LogicInterpreter例外透過性確保** - IOManager例外の適切な伝播
4. **オペレータレベル例外処理強化** - コンジャンクション等での重要例外の確実な伝播

### テストファイル
- `tests/runtime/test_exception_propagation.py` - 包括的な例外伝播テスト
- `tests/runtime/test_read_line_exception.py` - read_line述語専用テスト

### 利用方法
修正されたPyPrologでは、以下のようにカスタムIOManagerを使用してインタラクティブ入力例外を処理できます：

```python
from pyprolog.runtime.interpreter import Runtime
from pyprolog.runtime.io_manager import IOManager

class CustomIOManager(IOManager):
    def read_char_from_current(self) -> str:
        # インタラクティブ入力が必要な場合の例外
        raise YourCustomException("Interactive input required")

runtime = Runtime()
runtime.io_manager = CustomIOManager()

# ネストされた述語でも例外が正常に伝播される
try:
    runtime.query("start_diagnosis.")  # ネストされた述語
except YourCustomException:
    # 適切に例外をキャッチできる
    handle_interactive_input()
```

詳細な分析は `docs/pyprolog_exception_handling_analysis.md` を参照してください。

---

## Issue Summary (Original Report)

PyProlog's `Runtime.query()` does not propagate IO exceptions from custom IOManager implementations when interactive input predicates (`get_char/1`, `read_line/1`) are executed within nested predicates.

## Problem Description

### Expected Behavior
When a custom IOManager raises exceptions during `get_char/1` or `read_line/1` execution, these exceptions should propagate to the caller of `Runtime.query()`, regardless of nesting depth.

### Actual Behavior
- **Direct predicates work**: `runtime.query("get_char(X).")` → Exception propagates correctly
- **Nested predicates fail**: `runtime.query("start_diagnosis.")` → Exception caught internally, returns `[]` (empty result)

## Technical Details

### Code Analysis

**PyProlog Implementation**:
```python
# pyprolog/runtime/builtins.py:722
class GetCharPredicate(BuiltinPredicate):
    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        char_str = runtime.io_manager.read_char_from_current()  # ← Exception source
        # ... unification logic

# pyprolog/runtime/builtins.py:784  
class ReadLinePredicate(BuiltinPredicate):
    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        line_str = runtime.io_manager.read_line_from_current()  # ← Exception source
        # ... unification logic
```

**Custom IOManager** (raises exceptions for interactive input):
```python
class InteractiveIOManager:
    def read_char_from_current(self) -> str:
        raise PrologInputRequiredException(input_type="char", variable="X")
        
    def read_line_from_current(self) -> Optional[str]:
        raise PrologInputRequiredException(input_type="line", variable="X")
```

### Execution Flow Comparison

#### ✅ Working: Direct Predicate
```
runtime.query("get_char(X).")
└── GetCharPredicate.execute()
    └── io_manager.read_char_from_current()
        └── PrologInputRequiredException ── propagates to caller ✓
```

#### ❌ Failing: Nested Predicate
```
runtime.query("start_diagnosis.")
└── start_diagnosis rule execution
    └── ask_question(1) rule execution
        └── GetCharPredicate.execute() or ReadLinePredicate.execute()
            └── io_manager.read_char_from_current() or read_line_from_current()
                └── PrologInputRequiredException ── caught internally, not propagated ✗
└── Returns [] (empty result)
```

### Test Case

**Prolog Program**:
```prolog
start_diagnosis :- 
    write('Starting diagnosis'), nl,
    ask_question(1).

ask_question(ID) :-
    write('Enter input: '),
    read_line(Input),  % ← This should trigger exception propagation
    write('You entered: '), write(Input), nl.
```

**Expected Result**: `PrologInputRequiredException` propagates to `Runtime.query()` caller  
**Actual Result**: Query completes with `[]` (no solutions)

### Log Evidence

**Direct `read_line(X)` call**:
```
Line input request detected: variable=X, session=interactive_xxx
Started waiting for input: variable=X, type=line, request_id=xxx
Input required: line for X
```

**Nested `start_diagnosis` call**:
```
Runtime.query returned: []
Query completed normally: []
Duration: 35.30ms
```

## Impact

This limitation prevents building interactive Prolog applications that use complex predicate hierarchies with user input. Many real-world Prolog programs structure interactive logic in nested predicates, making this a significant constraint.

## Use Case

Building MCP (Model Context Protocol) server that provides interactive Prolog functionality to AI agents. The server needs to:
1. Execute complex Prolog programs with nested interactive predicates
2. Suspend execution when user input is required  
3. Resume execution after receiving input

Current limitation blocks implementation of sophisticated interactive diagnostic systems, educational Prolog environments, and conversational AI applications.

## Requested Investigation

Please investigate whether PyProlog's runtime execution model can be enhanced to:

1. **Exception Propagation**: Ensure IOManager exceptions propagate through nested predicate execution
2. **Execution Suspension**: Allow runtime queries to be suspended/resumed at arbitrary nesting levels
3. **Custom Exception Handling**: Provide hooks for custom exception handling during rule execution

Any guidance on architectural approaches or workarounds would be highly appreciated.

## Environment

- **Integration**: MCP Server with FastMCP framework
- **IOManager**: Custom implementation replacing standard stdio
- **Exception Type**: Custom `PrologInputRequiredException` 
- **Execution Pattern**: `Runtime.query()` with custom IOManager injection

## Additional Information

Complete source code and test cases available in the prolog_mcp repository. Happy to provide additional details or collaborate on potential solutions.