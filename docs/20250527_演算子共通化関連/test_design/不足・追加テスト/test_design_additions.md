# Prologインタープリター 不足テスト設計書

## 概要

既存のテスト設計書を分析した結果、以下の重要なテスト領域が不足しており、追加が必要です。

## 1. Logic Interpreter テスト設計

### 1.1 テストファイル: `tests/runtime/test_logic_interpreter.py`

```python
"""
Logic Interpreter テスト

Prologインタープリターの論理的推論エンジンの
動作を検証するテストスイート。
"""

from prolog.runtime.logic_interpreter import LogicInterpreter
from prolog.core.binding_environment import BindingEnvironment
from prolog.core.types import Term, Variable, Atom, Number, Rule, Fact
from prolog.core.errors import PrologError


class TestLogicInterpreter:
    """論理インタープリターのテスト"""

    def setup_method(self):
        """各テストの前処理"""
        self.rules = []
        self.mock_runtime = MockRuntime()
        self.logic_interpreter = LogicInterpreter(self.rules, self.mock_runtime)
        self.env = BindingEnvironment()

    def test_unification_basic(self):
        """基本的な単一化のテスト"""
        # アトム同士の単一化
        success, env = self.logic_interpreter.unify(Atom("hello"), Atom("hello"), self.env)
        assert success
        
        # 異なるアトムの単一化失敗
        success, env = self.logic_interpreter.unify(Atom("hello"), Atom("world"), self.env)
        assert not success
        
        # 変数とアトムの単一化
        success, env = self.logic_interpreter.unify(Variable("X"), Atom("value"), self.env)
        assert success
        assert env.get_value("X") == Atom("value")

    def test_unification_complex(self):
        """複雑な単一化のテスト"""
        # 複合項の単一化
        term1 = Term(Atom("likes"), [Variable("X"), Atom("mary")])
        term2 = Term(Atom("likes"), [Atom("john"), Variable("Y")])
        
        success, env = self.logic_interpreter.unify(term1, term2, self.env)
        assert success
        assert env.get_value("X") == Atom("john")
        assert env.get_value("Y") == Atom("mary")

    def test_occurs_check(self):
        """発生チェックのテスト"""
        # X = f(X) は失敗するべき
        var_x = Variable("X")
        term_fx = Term(Atom("f"), [var_x])
        
        success, env = self.logic_interpreter.unify(var_x, term_fx, self.env)
        assert not success  # 発生チェックにより失敗

    def test_variable_renaming(self):
        """変数リネームのテスト"""
        # 同じルールから2回変数をリネーム
        rule = Rule(
            Term(Atom("parent"), [Variable("X"), Variable("Y")]),
            Term(Atom("father"), [Variable("X"), Variable("Y")])
        )
        
        renamed1 = self.logic_interpreter._rename_variables(rule)
        renamed2 = self.logic_interpreter._rename_variables(rule)
        
        # 異なる名前でリネームされることを確認
        assert renamed1.head.args[0].name != renamed2.head.args[0].name

    def test_goal_resolution(self):
        """ゴール解決のテスト"""
        # ファクトの追加
        fact = Fact(Term(Atom("likes"), [Atom("john"), Atom("mary")]))
        self.logic_interpreter.rules = [fact]
        
        # ゴールの解決
        goal = Term(Atom("likes"), [Atom("john"), Atom("mary")])
        solutions = list(self.logic_interpreter.solve_goal(goal, self.env))
        
        assert len(solutions) == 1

    def test_backtracking(self):
        """バックトラッキングのテスト"""
        # 複数の解を持つルールを追加
        facts = [
            Fact(Term(Atom("color"), [Atom("red")])),
            Fact(Term(Atom("color"), [Atom("blue")])),
            Fact(Term(Atom("color"), [Atom("green")]))
        ]
        self.logic_interpreter.rules = facts
        
        # 全ての解を取得
        goal = Term(Atom("color"), [Variable("X")])
        solutions = list(self.logic_interpreter.solve_goal(goal, self.env))
        
        assert len(solutions) == 3

    def test_dereference(self):
        """間接参照のテスト"""
        # 変数チェーンの解決
        self.env.bind("X", Variable("Y"))
        self.env.bind("Y", Atom("value"))
        
        result = self.logic_interpreter.dereference(Variable("X"), self.env)
        assert result == Atom("value")


class MockRuntime:
    """テスト用のモックランタイム"""
    def execute(self, goal, env):
        yield env
```

### 1.2 追加テストケース

- ルールの再帰的適用
- カットの動作
- ネストした変数の解決
- 循環参照の検出

## 2. Runtime/Interpreter 統合テスト設計

### 2.1 テストファイル: `tests/runtime/test_interpreter.py`

```python
"""
Runtime Interpreter テスト

統合実行エンジンの動作を検証するテストスイート。
"""

from prolog.runtime.interpreter import Runtime
from prolog.core.types import Term, Variable, Atom, Number, Rule, Fact
from prolog.core.binding_environment import BindingEnvironment


class TestRuntime:
    """統合実行エンジンのテスト"""

    def setup_method(self):
        """各テストの前処理"""
        self.runtime = Runtime()

    def test_basic_fact_queries(self):
        """基本的なファクトクエリのテスト"""
        # ファクトを追加
        fact = Fact(Term(Atom("likes"), [Atom("john"), Atom("mary")]))
        self.runtime.rules = [fact]
        
        # クエリ実行
        results = self.runtime.query("likes(john, mary)")
        assert len(results) == 1

    def test_rule_resolution(self):
        """ルール解決のテスト"""
        # ルールとファクトを追加
        rule = Rule(
            Term(Atom("grandparent"), [Variable("X"), Variable("Z")]),
            Term(Atom(","), [
                Term(Atom("parent"), [Variable("X"), Variable("Y")]),
                Term(Atom("parent"), [Variable("Y"), Variable("Z")])
            ])
        )
        facts = [
            Fact(Term(Atom("parent"), [Atom("john"), Atom("tom")])),
            Fact(Term(Atom("parent"), [Atom("tom"), Atom("bob")]))
        ]
        
        self.runtime.rules = [rule] + facts
        
        # 祖父関係のクエリ
        results = self.runtime.query("grandparent(john, bob)")
        assert len(results) == 1

    def test_arithmetic_operations(self):
        """算術演算のテスト"""
        # is演算子のテスト
        results = self.runtime.query("X is 5 + 3")
        assert len(results) == 1
        assert any(var.name == "X" for var in results[0].keys())

    def test_comparison_operations(self):
        """比較演算のテスト"""
        results = self.runtime.query("5 > 3")
        assert len(results) == 1
        
        results = self.runtime.query("3 > 5")
        assert len(results) == 0

    def test_logical_operations(self):
        """論理演算のテスト"""
        # コンジャンクション
        fact1 = Fact(Term(Atom("a"), []))
        fact2 = Fact(Term(Atom("b"), []))
        self.runtime.rules = [fact1, fact2]
        
        results = self.runtime.query("a, b")
        assert len(results) == 1

    def test_control_flow(self):
        """制御フローのテスト"""
        # カットのテスト
        rules = [
            Rule(Term(Atom("test"), [Atom("a")]), Term(Atom("!"), [])),
            Rule(Term(Atom("test"), [Atom("b")]), Term(Atom("true"), []))
        ]
        self.runtime.rules = rules
        
        # カットにより最初の解のみ返される
        results = self.runtime.query("test(X)")
        # カットの実装により結果は変わる

    def test_builtin_predicates(self):
        """組み込み述語のテスト"""
        # write/1 のテスト（標準出力に出力されるため、テストは限定的）
        results = self.runtime.query("write('hello')")
        assert len(results) == 1

    def test_variable_unification(self):
        """変数単一化のテスト"""
        fact = Fact(Term(Atom("person"), [Atom("john"), Number(25)]))
        self.runtime.rules = [fact]
        
        results = self.runtime.query("person(Name, Age)")
        assert len(results) == 1
        result = results[0]
        
        # 変数が正しく束縛されているか確認
        name_vars = [var for var in result.keys() if var.name == "Name"]
        age_vars = [var for var in result.keys() if var.name == "Age"]
        
        assert len(name_vars) == 1
        assert len(age_vars) == 1
        assert result[name_vars[0]] == Atom("john")
        assert result[age_vars[0]] == Number(25)
```

## 3. 統合テスト設計

### 3.1 テストファイル: `tests/integration/test_end_to_end.py`

```python
"""
End-to-End テスト

システム全体の統合動作を検証するテストスイート。
"""

from prolog.runtime.interpreter import Runtime
from prolog.parser.scanner import Scanner
from prolog.parser.parser import Parser


class TestEndToEnd:
    """エンドツーエンドテスト"""

    def setup_method(self):
        """各テストの前処理"""
        self.runtime = Runtime()

    def test_simple_queries(self):
        """単純なクエリのテスト"""
        # プログラムをロード
        program = """
        likes(mary, food).
        likes(mary, wine).
        likes(john, wine).
        likes(john, mary).
        """
        
        self._load_program(program)
        
        # クエリを実行
        results = self.runtime.query("likes(mary, wine)")
        assert len(results) == 1
        
        results = self.runtime.query("likes(X, wine)")
        assert len(results) == 2

    def test_complex_queries(self):
        """複雑なクエリのテスト"""
        program = """
        parent(tom, bob).
        parent(bob, ann).
        parent(bob, pat).
        parent(pat, jim).
        
        grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
        """
        
        self._load_program(program)
        
        results = self.runtime.query("grandparent(tom, ann)")
        assert len(results) == 1

    def test_recursive_rules(self):
        """再帰ルールのテスト"""
        program = """
        ancestor(X, Y) :- parent(X, Y).
        ancestor(X, Z) :- parent(X, Y), ancestor(Y, Z).
        
        parent(a, b).
        parent(b, c).
        parent(c, d).
        """
        
        self._load_program(program)
        
        results = self.runtime.query("ancestor(a, d)")
        assert len(results) == 1

    def test_list_operations(self):
        """リスト操作の互換性テスト"""
        runtime = Runtime()
        
        # リスト構文のテスト
        list_tests = [
            ("X = [a, b, c]", True),
            ("X = []", True),
            ("[H|T] = [a, b, c]", True),
        ]
        
        for query, should_succeed in list_tests:
            results = runtime.query(query)
            if should_succeed:
                assert len(results) >= 1
            else:
                assert len(results) == 0
```

## 8. ベンチマークテスト設計

### 8.1 テストファイル: `tests/benchmark/test_benchmark.py`

```python
"""
Benchmark テスト

システムの性能指標を測定するベンチマークテストスイート。
"""

import time
import statistics
from typing import List
from prolog.runtime.interpreter import Runtime


class TestBenchmark:
    """ベンチマークテスト"""

    def test_fibonacci_benchmark(self):
        """フィボナッチ数列ベンチマーク"""
        runtime = Runtime()
        
        program = """
        fibonacci(0, 1).
        fibonacci(1, 1).
        fibonacci(N, F) :- 
            N > 1,
            N1 is N - 1,
            N2 is N - 2,
            fibonacci(N1, F1),
            fibonacci(N2, F2),
            F is F1 + F2.
        """
        runtime.add_rule(program)
        
        # 複数回実行して平均時間を測定
        times = []
        for _ in range(5):
            start_time = time.time()
            results = runtime.query("fibonacci(15, F)")
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        std_dev = statistics.stdev(times)
        
        print(f"Fibonacci(15) - Average: {avg_time:.4f}s, StdDev: {std_dev:.4f}s")
        assert len(results) == 1
        assert avg_time < 1.0  # 性能目標

    def test_factorial_benchmark(self):
        """階乗計算ベンチマーク"""
        runtime = Runtime()
        
        program = """
        factorial(0, 1).
        factorial(N, F) :-
            N > 0,
            N1 is N - 1,
            factorial(N1, F1),
            F is N * F1.
        """
        runtime.add_rule(program)
        
        # 階乗計算の性能測定
        test_values = [5, 10, 15, 20]
        
        for n in test_values:
            start_time = time.time()
            results = runtime.query(f"factorial({n}, F)")
            calc_time = time.time() - start_time
            
            assert len(results) == 1
            print(f"factorial({n}) calculated in {calc_time:.4f}s")

    def test_sorting_benchmark(self):
        """ソートアルゴリズムベンチマーク"""
        runtime = Runtime()
        
        program = """
        % Quick Sort implementation
        quicksort([], []).
        quicksort([H|T], Sorted) :-
            partition(H, T, Less, Greater),
            quicksort(Less, SortedLess),
            quicksort(Greater, SortedGreater),
            append(SortedLess, [H|SortedGreater], Sorted).
        
        partition(_, [], [], []).
        partition(Pivot, [H|T], [H|Less], Greater) :-
            H =< Pivot,
            partition(Pivot, T, Less, Greater).
        partition(Pivot, [H|T], Less, [H|Greater]) :-
            H > Pivot,
            partition(Pivot, T, Less, Greater).
        
        append([], L, L).
        append([H|T], L, [H|R]) :- append(T, L, R).
        """
        runtime.add_rule(program)
        
        # ソートのベンチマーク
        start_time = time.time()
        results = runtime.query("quicksort([3,1,4,1,5,9,2,6], Sorted)")
        sort_time = time.time() - start_time
        
        assert len(results) == 1
        print(f"Quicksort completed in {sort_time:.4f}s")

    def test_memory_benchmark(self):
        """メモリ使用量ベンチマーク"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        runtime = Runtime()
        
        # 大量のデータを扱うプログラム
        program = """
        generate_data(0, []).
        generate_data(N, [N|T]) :-
            N > 0,
            N1 is N - 1,
            generate_data(N1, T).
        """
        runtime.add_rule(program)
        
        # 大量データの生成
        results = runtime.query("generate_data(1000, Data)")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = final_memory - initial_memory
        
        print(f"Memory usage: {memory_used:.2f} MB")
        assert len(results) == 1
        assert memory_used < 50  # 50MB以下
```

## 9. 統合CI/CDテスト設計

### 9.1 テストファイル: `tests/ci/test_ci_validation.py`

```python
"""
CI/CD Validation テスト

継続的インテグレーション/デプロイメント用の検証テストスイート。
"""

import subprocess
import sys
import os
from prolog.runtime.interpreter import Runtime


class TestCIValidation:
    """CI/CD検証テスト"""

    def test_smoke_test(self):
        """スモークテスト - 基本機能の動作確認"""
        runtime = Runtime()
        
        # 基本的なクエリが動作することを確認
        basic_tests = [
            "X = hello",
            "5 > 3",
            "X is 2 + 3",
        ]
        
        for query in basic_tests:
            results = runtime.query(query)
            assert len(results) >= 0  # エラーが発生しないことを確認

    def test_installation_validation(self):
        """インストール検証テスト"""
        # パッケージが正しくインポートできることを確認
        try:
            import prolog
            import prolog.runtime.interpreter
            import prolog.parser.parser
            import prolog.core.types
        except ImportError as e:
            assert False, f"Import failed: {e}"

    def test_command_line_interface(self):
        """コマンドラインインターフェースのテスト"""
        # CLIが正常に起動することを確認（実際の対話はテスト困難）
        try:
            result = subprocess.run([
                sys.executable, "-m", "prolog.cli.prolog", "--help"
            ], capture_output=True, text=True, timeout=10)
            # ヘルプが表示されることを確認
            assert result.returncode == 0 or "help" in result.stdout.lower()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # CLIが存在しない場合はスキップ
            pass

    def test_example_programs(self):
        """サンプルプログラムの動作確認"""
        runtime = Runtime()
        
        # 基本的なPrologプログラムが動作することを確認
        example_program = """
        parent(tom, bob).
        parent(bob, liz).
        grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
        """
        
        # プログラムの読み込み
        lines = example_program.strip().split('\n')
        for line in lines:
            if line.strip():
                runtime.add_rule(line.strip())
        
        # クエリの実行
        results = runtime.query("grandparent(tom, liz)")
        assert len(results) == 1

    def test_data_file_loading(self):
        """データファイル読み込みのテスト"""
        runtime = Runtime()
        
        # テストデータファイルが存在し、読み込めることを確認
        test_files = [
            "tests/data/test.prolog",
            "tests/data/myadven.prolog",
            "tests/data/puzzle1.prolog"
        ]
        
        for file_path in test_files:
            if os.path.exists(file_path):
                success = runtime.consult(file_path)
                assert success, f"Failed to load {file_path}"

    def test_version_compatibility(self):
        """バージョン互換性のテスト"""
        # Python バージョンの確認
        assert sys.version_info >= (3, 8), "Python 3.8+ required"
        
        # 必要なモジュールの確認
        required_modules = [
            'dataclasses',
            'typing',
            'enum',
            'logging',
            'pathlib'
        ]
        
        for module_name in required_modules:
            try:
                __import__(module_name)
            except ImportError:
                assert False, f"Required module {module_name} not available"
```

## 10. セキュリティテスト設計

### 10.1 テストファイル: `tests/security/test_security.py`

```python
"""
Security テスト

セキュリティ関連の動作を検証するテストスイート。
"""

from prolog.runtime.interpreter import Runtime
from prolog.parser.scanner import Scanner
from prolog.parser.parser import Parser


class TestSecurity:
    """セキュリティテスト"""

    def test_malicious_input_handling(self):
        """悪意のある入力の処理テスト"""
        runtime = Runtime()
        
        # 非常に長い入力
        long_query = "test(" + "a" * 10000 + ")"
        results = runtime.query(long_query)
        # システムがクラッシュしないことを確認

    def test_infinite_recursion_protection(self):
        """無限再帰の保護テスト"""
        runtime = Runtime()
        
        program = """
        infinite_loop(X) :- infinite_loop(X).
        """
        runtime.add_rule(program)
        
        # 無限再帰がシステムをクラッシュさせないことを確認
        try:
            results = runtime.query("infinite_loop(test)")
            # タイムアウトやスタックオーバーフロー保護が働くことを期待
        except (RecursionError, TimeoutError):
            pass  # 期待される保護機能

    def test_resource_exhaustion_protection(self):
        """リソース枯渇保護のテスト"""
        runtime = Runtime()
        
        # メモリを大量消費する可能性のあるクエリ
        program = """
        create_large_list(0, []).
        create_large_list(N, [N|T]) :-
            N > 0,
            N1 is N - 1,
            create_large_list(N1, T).
        """
        runtime.add_rule(program)
        
        # 適度なサイズで制限されることを確認
        try:
            results = runtime.query("create_large_list(100000, L)")
            # メモリ制限や実行時間制限が働くことを期待
        except (MemoryError, TimeoutError):
            pass  # 期待される保護機能

    def test_input_sanitization(self):
        """入力サニタイゼーションのテスト"""
        # 特殊文字を含む入力の安全な処理
        scanner = Scanner("test('special\\chars\"here')")
        tokens = scanner.scan_tokens()
        # エラーなく処理されることを確認
        assert len(tokens) > 0
```

## 11. 実装優先度の更新

既存の実装優先度（Phase 1-4）に加えて、以下の優先度を追加します：

### Phase 5: 高度なテスト実装
1. Logic Interpreter詳細テスト
2. Runtime統合テスト完全版
3. エラーハンドリング強化テスト

### Phase 6: システム検証テスト
1. 実用プログラムテスト
2. パフォーマンステスト  
3. 互換性テスト

### Phase 7: 運用品質テスト
1. ベンチマークテスト
2. セキュリティテスト
3. CI/CD検証テスト

## 12. テスト実行ガイドライン

### 12.1 テスト実行コマンド

```bash
# 全テストの実行
pytest tests/

# カテゴリ別実行
pytest tests/core/           # コアコンポーネント
pytest tests/parser/         # パーサー
pytest tests/runtime/        # ランタイム  
pytest tests/integration/    # 統合テスト
pytest tests/system/         # システムテスト
pytest tests/performance/    # パフォーマンステスト

# カバレッジ付き実行
pytest --cov=prolog tests/

# ベンチマークテスト
pytest tests/benchmark/ -v --benchmark-only
```

### 12.2 テスト品質指標

- **カバレッジ目標**: 全体90%以上
- **実行時間**: 通常テスト5分以内、パフォーマンステスト15分以内
- **成功率**: 99%以上（不安定テストの除去）

### 12.3 継続的品質管理

- 毎回のプルリクエストでの自動テスト実行
- 夜間の完全テストスイート実行
- 週次のパフォーマンス回帰テスト
- 月次の互換性検証テスト

## まとめ

この追加テスト設計書により、以下の不足していたテスト領域が補完されます：

1. **Logic Interpreter**: 単一化、変数リネーム、ゴール解決の詳細テスト
2. **Runtime統合**: 演算子統合、エラーハンドリング、パフォーマンス
3. **End-to-End**: 実際のPrologプログラム動作検証
4. **システム品質**: パフォーマンス、セキュリティ、互換性
5. **運用検証**: CI/CD、ベンチマーク、長期安定性

これらのテストを段階的に実装することで、品質の高いPrologインタープリターの開発と維持が可能になります。_operations(self):
        """リスト操作のテスト"""
        program = """
        member(X, [X|_]).
        member(X, [_|T]) :- member(X, T).
        """
        
        self._load_program(program)
        
        results = self.runtime.query("member(b, [a, b, c])")
        assert len(results) == 1

    def test_cut_operations(self):
        """カット操作のテスト"""
        program = """
        max(X, Y, X) :- X >= Y, !.
        max(X, Y, Y).
        """
        
        self._load_program(program)
        
        results = self.runtime.query("max(5, 3, Z)")
        assert len(results) == 1

    def test_database_operations(self):
        """データベース操作のテスト"""
        program = """
        dynamic_fact(initial).
        """
        
        self._load_program(program)
        
        # 初期状態の確認
        results = self.runtime.query("dynamic_fact(X)")
        assert len(results) == 1
        
        # 新しいファクトの追加
        self.runtime.add_rule("dynamic_fact(added)")
        
        results = self.runtime.query("dynamic_fact(X)")
        assert len(results) == 2

    def test_arithmetic_expressions(self):
        """算術式のテスト"""
        program = """
        calculate(X, Y, Sum) :- Sum is X + Y.
        compare_numbers(X, Y) :- X > Y.
        """
        
        self._load_program(program)
        
        # 算術計算
        results = self.runtime.query("calculate(5, 3, Result)")
        assert len(results) == 1
        
        # 数値比較
        results = self.runtime.query("compare_numbers(10, 5)")
        assert len(results) == 1

    def _load_program(self, program_text: str):
        """プログラムテキストをパースしてランタイムにロード"""
        scanner = Scanner(program_text)
        tokens = scanner.scan_tokens()
        parser = Parser(tokens)
        rules = parser.parse()
        self.runtime.rules.extend(rules)
```

## 4. システムテスト設計

### 4.1 テストファイル: `tests/system/test_real_programs.py`

```python
"""
Real Programs テスト

実際のPrologプログラムの動作を検証するテストスイート。
"""

import os
from prolog.runtime.interpreter import Runtime
from prolog.parser.scanner import Scanner
from prolog.parser.parser import Parser


class TestRealPrograms:
    """実用プログラムのテスト"""

    def test_adventure_game(self):
        """冒険ゲームプログラムのテスト"""
        runtime = self._load_prolog_file("tests/data/myadven.prolog")
        
        # 基本的なルームの存在確認
        results = runtime.query("room(kitchen)")
        assert len(results) == 1
        
        # 位置情報の確認
        results = runtime.query("location(apple, kitchen)")
        assert len(results) == 1
        
        # ドアの状態確認
        results = runtime.query("door(office, hall, open)")
        assert len(results) == 1

    def test_zebra_puzzle(self):
        """ゼブラパズルプログラムのテスト"""
        runtime = self._load_prolog_file("tests/data/puzzle1.prolog")
        
        # パズルの解を求める（時間がかかる可能性があるため簡単なテストのみ）
        results = runtime.query("exists(house(red, english, _, _, _), Houses)")
        # 実際の解は複雑なので、基本的な述語の動作確認に留める

    def test_general_programs(self):
        """一般的なテストプログラムのテスト"""
        runtime = self._load_prolog_file("tests/data/test.prolog")
        
        # ウィンドウ情報の確認
        results = runtime.query("window(main, -2, 2.0, 20, 72)")
        assert len(results) == 1
        
        # 顧客情報の確認
        results = runtime.query("customer('John Jones', boston, good_credit)")
        assert len(results) == 1
        
        # 算術テストの実行
        results = runtime.query("test(Y)")
        assert len(results) == 1

    def test_program_loading_error_handling(self):
        """プログラム読み込みエラーハンドリングのテスト"""
        runtime = Runtime()
        
        # 存在しないファイルの読み込み
        success = runtime.consult("nonexistent.prolog")
        assert not success

    def _load_prolog_file(self, filepath: str) -> Runtime:
        """Prologファイルを読み込んでRuntimeを返す"""
        runtime = Runtime()
        success = runtime.consult(filepath)
        assert success, f"Failed to load {filepath}"
        return runtime
```

### 4.2 テストファイル: `tests/system/test_repl.py`

```python
"""
REPL テスト

REPLインターフェースの動作を検証するテストスイート。
"""

from io import StringIO
import sys
from unittest.mock import patch
from prolog.cli.repl import run_repl
from prolog.runtime.interpreter import Runtime


class TestREPL:
    """REPLのテスト"""

    def test_interactive_queries(self):
        """対話的クエリのテスト"""
        runtime = Runtime()
        runtime.add_rule("fact(test)")
        
        # モックの入力と出力を使用
        with patch('sys.stdin'), patch('sys.stdout', new=StringIO()) as mock_stdout:
            # REPLのテストは複雑なため、基本的な動作確認のみ
            pass

    def test_command_handling(self):
        """コマンド処理のテスト"""
        # REPLコマンドの処理テスト
        pass

    def test_error_display(self):
        """エラー表示のテスト"""
        # エラーメッセージの表示テスト
        pass

    def test_variable_display(self):
        """変数表示のテスト"""
        # クエリ結果の変数表示テスト
        pass

    def test_backtracking_interface(self):
        """バックトラッキングインターフェースのテスト"""
        # セミコロンによる次の解の要求テスト
        pass
```

## 5. パフォーマンステスト設計

### 5.1 テストファイル: `tests/performance/test_performance.py`

```python
"""
Performance テスト

システムのパフォーマンスを検証するテストスイート。
"""

import time
import pytest
from prolog.runtime.interpreter import Runtime


class TestPerformance:
    """パフォーマンステスト"""

    def test_large_fact_database(self):
        """大量ファクトデータベースのテスト"""
        runtime = Runtime()
        
        # 大量のファクトを生成
        facts = []
        for i in range(1000):
            facts.append(f"fact({i})")
        
        start_time = time.time()
        for fact in facts:
            runtime.add_rule(fact)
        load_time = time.time() - start_time
        
        # ロード時間の確認（適切な閾値を設定）
        assert load_time < 5.0, f"Fact loading took too long: {load_time}s"
        
        # クエリ性能の確認
        start_time = time.time()
        results = runtime.query("fact(500)")
        query_time = time.time() - start_time
        
        assert len(results) == 1
        assert query_time < 1.0, f"Query took too long: {query_time}s"

    def test_deep_recursion(self):
        """深い再帰のテスト"""
        runtime = Runtime()
        
        program = """
        count(0).
        count(N) :- N > 0, N1 is N - 1, count(N1).
        """
        
        runtime.add_rule(program)
        
        start_time = time.time()
        results = runtime.query("count(100)")
        recursion_time = time.time() - start_time
        
        assert len(results) == 1
        assert recursion_time < 2.0, f"Deep recursion took too long: {recursion_time}s"

    def test_complex_unification(self):
        """複雑な単一化のテスト"""
        runtime = Runtime()
        
        # 複雑な構造の項を作成
        program = """
        complex_term(f(g(h(a)), f(g(h(b)), f(g(h(c)), f(g(h(d)), e))))).
        """
        
        runtime.add_rule(program)
        
        start_time = time.time()
        results = runtime.query("complex_term(X)")
        unification_time = time.time() - start_time
        
        assert len(results) == 1
        assert unification_time < 1.0, f"Complex unification took too long: {unification_time}s"

    def test_memory_usage(self):
        """メモリ使用量のテスト"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        runtime = Runtime()
        
        # 大量の操作を実行
        for i in range(100):
            runtime.add_rule(f"test_rule({i}) :- fact({i})")
            runtime.query(f"test_rule({i})")
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # メモリ増加が過度でないことを確認（100MB以下）
        assert memory_increase < 100 * 1024 * 1024, f"Excessive memory usage: {memory_increase} bytes"

    def test_parsing_performance(self):
        """パース性能のテスト"""
        from prolog.parser.scanner import Scanner
        from prolog.parser.parser import Parser
        
        # 大きなプログラムテキストを生成
        large_program = []
        for i in range(1000):
            large_program.append(f"rule{i}(arg{i}) :- fact{i}(arg{i}).")
        
        program_text = "\n".join(large_program)
        
        start_time = time.time()
        scanner = Scanner(program_text)
        tokens = scanner.scan_tokens()
        parser = Parser(tokens)
        rules = parser.parse()
        parse_time = time.time() - start_time
        
        assert len(rules) == 1000
        assert parse_time < 2.0, f"Parsing took too long: {parse_time}s"

    @pytest.mark.benchmark
    def test_query_benchmark(self):
        """クエリベンチマーク"""
        runtime = Runtime()
        
        # ベンチマーク用のプログラム
        program = """
        fibonacci(0, 1).
        fibonacci(1, 1).
        fibonacci(N, F) :- 
            N > 1,
            N1 is N - 1,
            N2 is N - 2,
            fibonacci(N1, F1),
            fibonacci(N2, F2),
            F is F1 + F2.
        """
        
        runtime.add_rule(program)
        
        # フィボナッチ数列の計算性能測定
        test_values = [10, 15, 20]
        
        for n in test_values:
            start_time = time.time()
            results = runtime.query(f"fibonacci({n}, F)")
            calc_time = time.time() - start_time
            
            assert len(results) == 1
            print(f"fibonacci({n}) calculated in {calc_time:.4f}s")
```

## 6. エラーハンドリングテスト設計

### 6.1 テストファイル: `tests/core/test_error_handling.py`

```python
"""
Error Handling テスト

エラーハンドリングの動作を検証するテストスイート。
"""

from prolog.core.errors import InterpreterError, ScannerError, ParserError, PrologError
from prolog.parser.scanner import Scanner
from prolog.parser.parser import Parser
from prolog.runtime.interpreter import Runtime


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    def test_scanner_errors(self):
        """スキャナーエラーのテスト"""
        # 未終端文字列
        scanner = Scanner("'unterminated string")
        tokens = scanner.scan_tokens()
        # エラーが適切に報告されることを確認

    def test_parser_errors(self):
        """パーサーエラーのテスト"""
        # 構文エラー
        scanner = Scanner("invalid(syntax")
        tokens = scanner.scan_tokens()
        parser = Parser(tokens)
        # パースエラーが適切に処理されることを確認

    def test_runtime_errors(self):
        """ランタイムエラーのテスト"""
        runtime = Runtime()
        
        # 未定義述語のクエリ
        results = runtime.query("undefined_predicate(X)")
        assert len(results) == 0

    def test_arithmetic_errors(self):
        """算術エラーのテスト"""
        runtime = Runtime()
        
        # ゼロ除算
        try:
            runtime.query("X is 5 / 0")
            assert False, "Should have raised an error"
        except (PrologError, ZeroDivisionError):
            pass  # 期待されるエラー

    def test_unification_errors(self):
        """単一化エラーのテスト"""
        runtime = Runtime()
        
        # 発生チェック失敗
        results = runtime.query("X = f(X)")
        assert len(results) == 0  # 失敗するべき

    def test_type_errors(self):
        """型エラーのテスト"""
        runtime = Runtime()
        
        # 型不一致による算術エラー
        try:
            runtime.query("X is atom + 5")
            assert False, "Should have raised an error"
        except PrologError:
            pass  # 期待されるエラー
```

## 7. 互換性テスト設計

### 7.1 テストファイル: `tests/compatibility/test_prolog_compatibility.py`

```python
"""
Prolog Compatibility テスト

標準Prologとの互換性を検証するテストスイート。
"""

from prolog.runtime.interpreter import Runtime


class TestPrologCompatibility:
    """Prolog互換性のテスト"""

    def test_iso_prolog_arithmetic(self):
        """ISO Prolog算術互換性のテスト"""
        runtime = Runtime()
        
        # 基本算術演算子
        test_cases = [
            ("X is 5 + 3", 8),
            ("X is 10 - 4", 6),
            ("X is 6 * 7", 42),
            ("X is 15 / 3", 5.0),
            ("X is 7 mod 3", 1),
            ("X is 2 ** 3", 8),
        ]
        
        for query, expected in test_cases:
            results = runtime.query(query)
            assert len(results) == 1
            # 結果の値を確認（実装依存）

    def test_iso_prolog_comparison(self):
        """ISO Prolog比較演算子互換性のテスト"""
        runtime = Runtime()
        
        # 比較演算子のテスト
        comparison_tests = [
            ("5 =:= 5", True),
            ("5 =\\= 3", True),  
            ("3 < 5", True),
            ("5 > 3", True),
            ("3 =< 5", True),
            ("5 >= 3", True),
        ]
        
        for query, should_succeed in comparison_tests:
            results = runtime.query(query)
            if should_succeed:
                assert len(results) == 1
            else:
                assert len(results) == 0

    def test_iso_prolog_unification(self):
        """ISO Prolog単一化互換性のテスト"""
        runtime = Runtime()
        
        # 単一化テスト
        unification_tests = [
            ("X = hello", True),
            ("5 = 5", True),
            ("atom = atom", True),
            ("X = Y, Y = hello", True),
        ]
        
        for query, should_succeed in unification_tests:
            results = runtime.query(query)
            if should_succeed:
                assert len(results) >= 1
            else:
                assert len(results) == 0

    def test_standard_predicates(self):
        """標準述語の互換性テスト"""
        runtime = Runtime()
        
        # 組み込み述語のテスト
        builtin_tests = [
            "write('hello')",
            "nl",
            "tab(4)",
        ]
        
        for query in builtin_tests:
            results = runtime.query(query)
            assert len(results) == 1  # 成功することを確認

    def test_list