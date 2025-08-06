# pyprologライブラリ例外処理分析

## 分析概要
`PrologInputRequiredException`がpyprologライブラリ内でどのように処理されているかの詳細分析結果。

## pyprologソースコード分析

### 1. Runtime.query()メソッドの例外処理

#### ファイル: `pyprolog/runtime/interpreter.py`

**重要な箇所（行590-674）:**

```python
def query(self, query_string: str) -> List[Dict[Variable, Any]]:
    logger.debug(f"QUERY: Executing query: {query_string}")
    solutions = []
    try:
        # ... クエリの解析とゴール抽出 ...
        
        try:
            logger.debug(f"QUERY: Starting execute loop for goal: {query_goal}")
            for i, env_solution in enumerate(self.execute(query_goal, initial_env)):
                # ... ソリューション処理 ...
                solutions.append(result)
        except CutException:
            logger.info("Cut execution stopped further solutions at query level...")
        
        logger.debug(f"QUERY: Completed with {len(solutions)} solutions")
        return solutions

    except PrologError as pe:  # PrologError系の例外
        logger.warning(f"PrologError during query execution: {pe}", exc_info=True)
        raise pe  # PrologErrorは再発生

    except Exception as e:  # その他の予期しない例外
        logger.error(
            f"Unexpected query execution error during query '{query_string}': {e}",
            exc_info=True,
        )
        # Re-raise the exception to make it visible in test output
        raise e  # 他の例外も再発生
```

### 2. GetCharPredicate.execute()の処理

#### ファイル: `pyprolog/runtime/builtins.py`（行704-749）

```python
class GetCharPredicate(BuiltinPredicate):
    def execute(self, runtime: "Runtime", env: BindingEnvironment) -> Iterator[BindingEnvironment]:
        # IOManagerから文字を取得
        char_str = runtime.io_manager.read_char_from_current()  # ここで例外発生
        
        # 文字の処理とAtom化
        if char_str == "":  # EOF
            target_atom = Atom("end_of_file")
        elif len(char_str) == 1:  # 単一文字
            target_atom = Atom(char_str)
        # ... 以下、unification処理 ...
```

## 例外処理の問題点分析

### 3. 確認された事実

#### ✅ pyprologの例外処理は正常
1. **`Runtime.query()`は例外を適切に処理している**
2. **`PrologError`は行666で再発生させる**  
3. **`Exception`（その他）は行674で再発生させる**
4. **例外ログも適切に出力している（行669-671）**

#### ❌ 実際の動作での問題
1. **コンソールにはエラーログが出力されている**:
   ```
   [2025-08-06 14:24:30] ERROR pyprolog.runtime.interpreter - 
   Unexpected query execution error during query 'get_char(X).': Character input required for variable X
   ```

2. **しかし、我々のコードには例外が到達していない**:
   ```python
   # prolog_mcp/core/prolog_wrapper.py の _execute_prolog_query() 
   raw_results = self.runtime.query(query_string)  # 例外が来るはずだが...
   # 実際には空リスト [] が返される
   ```

### 4. 問題の根本原因推定

#### 仮説1: 例外クラスの継承問題
- `PrologInputRequiredException`がpyprologの`PrologError`を継承していない
- そのため`Exception`ハンドラー（行668）でキャッチされる
- しかし何らかの理由で`raise e`（行674）が機能していない

#### 仮説2: イテレーター内での例外処理
- `self.execute(query_goal, initial_env)`はイテレーター（行634）
- イテレーター内部で例外が発生した場合、特殊な処理が必要
- StopIterationや内部的な例外処理により、例外が握りつぶされている可能性

#### 仮説3: ジェネレーター/イテレーターの例外伝播問題  
- `GetCharPredicate.execute()`は`Iterator[BindingEnvironment]`を返す
- ジェネレーター内での例外は、呼び出し側に適切に伝播されない場合がある

## 実装上の発見

### 5. pyprologの設計パターン
- **Iterator Pattern**: クエリ実行は遅延評価でソリューションを生成
- **Exception Handling**: PrologErrorとその他のExceptionを区別して処理
- **Logging**: 全ての例外をログ出力（デバッグに有効）

### 6. IOManager統合の課題
- pyprologは標準的なIOManagerインターフェースを想定
- `read_char_from_current()`は通常、文字列またはEOFを返すことを期待
- **Python例外を投げることは想定外の動作**


---
**分析者**: Claude Code  
**日時**: 2025年8月6日 14:45 JST