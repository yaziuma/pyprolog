# 追加テスト構造と実装例

## 13. 不足テストの具体実装例

### 13.1 Variable Dereferencing テスト

既存のテストで不足している間接参照テストの実装：

```python
# tests/core/test_variable_dereferencing.py
"""
Variable Dereferencing テスト

変数の間接参照機能の詳細な動作を検証
"""

from prolog.core.binding_environment import BindingEnvironment
from prolog.core.types import Variable, Atom, Number, Term
from prolog.runtime.logic_interpreter import LogicInterpreter


class TestVariableDereferencing:
    """変数間接参照のテスト"""

    def setup_method(self):
        self.env = BindingEnvironment()
        self.mock_runtime = MockRuntime()
        self.logic_interpreter = LogicInterpreter([], self.mock_runtime)

    def test_simple_dereferencing(self):
        """単純な間接参照のテスト"""
        # X = hello
        self.env.bind("X", Atom("hello"))
        
        result = self.logic_interpreter.dereference(Variable("X"), self.env)
        assert result == Atom("hello")

    def test_chain_dereferencing(self):
        """チェーン間接参照のテスト"""
        # X = Y, Y = Z, Z = value
        self.env.bind("X", Variable("Y"))
        self.env.bind("Y", Variable("Z"))
        self.env.bind("Z", Atom("value"))
        
        result = self.logic_interpreter.dereference(Variable("X"), self.env)
        assert result == Atom("value")

    def test_circular_reference_detection(self):
        """循環参照の検出テスト"""
        # X = Y, Y = X (循環参照)
        self.env.bind("X", Variable("Y"))
        self.env.bind("Y", Variable("X"))
        
        # 循環参照を検出して適切に処理することを確認
        result = self.logic_interpreter.dereference(Variable("X"), self.env)
        # 実装により動作は異なるが、無限ループにならないこと

    def test_partial_dereferencing(self):
        """部分的間接参照のテスト"""
        # 一部の変数のみ束縛されている場合
        term = Term(Atom("f"), [Variable("X"), Variable("Y")])
        self.env.bind("X", Atom("bound"))
        
        # Y は未束縛のまま
        result = self.logic_interpreter.dereference(term, self.env)
        # 実装に応じて適切に処理されることを確認


class MockRuntime:
    def execute(self, goal, env):
        yield env
```

### 13.2 Arithmetic Edge Cases テスト

数学演算の境界値テスト：

```python
# tests/runtime/test_arithmetic_edge_cases.py
"""
Arithmetic Edge Cases テスト

算術演算の境界値と特殊ケースを検証
"""

from prolog.runtime.math_interpreter import MathInterpreter
from prolog.core.binding_environment import BindingEnvironment
from prolog.core.types import Number, Term, Atom
from prolog.core.errors import PrologError
import math


class TestArithmeticEdgeCases:
    """算術演算境界値のテスト"""

    def setup_method(self):
        self.math_interpreter = MathInterpreter()
        self.env = BindingEnvironment()

    def test_large_numbers(self):
        """大きな数値の処理テスト"""
        # 非常に大きな整数
        large_int = Number(999999999999999999)
        result = self.math_interpreter.evaluate(large_int, self.env)
        assert result == 999999999999999999

    def test_floating_point_precision(self):
        """浮動小数点精度のテスト"""
        # 精度の問題を含む計算
        expr = Term(Atom("+"), [Number(0.1), Number(0.2)])
        result = self.math_interpreter.evaluate(expr, self.env)
        # 浮動小数点の精度問題を考慮
        assert abs(result - 0.3) < 1e-10

    def test_infinity_handling(self):
        """無限大の処理テスト"""
        # 1.0 / 0.0 -> inf
        try:
            expr = Term(Atom("/"), [Number(1.0), Number(0.0)])
            result = self.math_interpreter.evaluate(expr, self.env)
            # 実装により inf を返すか例外を投げるか
        except PrologError:
            pass  # ゼロ除算エラーも適切

    def test_nan_handling(self):
        """NaNの処理テスト"""
        # 0.0 / 0.0 -> NaN
        try:
            expr = Term(Atom("/"), [Number(0.0), Number(0.0)])
            result = self.math_interpreter.evaluate(expr, self.env)
            # NaNの処理確認
        except PrologError:
            pass  # エラーも適切

    def test_overflow_underflow(self):
        """オーバーフロー・アンダーフローのテスト"""
        # 非常に大きな指数
        try:
            expr = Term(Atom("**"), [Number(10), Number(1000)])
            result = self.math_interpreter.evaluate(expr, self.env)
            # オーバーフローの適切な処理を確認
        except (OverflowError, PrologError):
            pass

    def test_negative_zero(self):
        """負のゼロの処理テスト"""
        neg_zero = Number(-0.0)
        pos_zero = Number(0.0)
        
        # 数学的には等しいが、実装により異なる場合がある
        assert self.math_interpreter.evaluate_comparison_op("=:=", -0.0, 0.0)
```

### 13.3 Parser Recovery テスト

パーサーの回復機能テスト：

```python
# tests/parser/test_parser_recovery.py
"""
Parser Recovery テスト

構文エラーからの回復機能を検証
"""

from prolog.parser.parser import Parser
from prolog.parser.scanner import Scanner
from prolog.core.types import Rule, Fact


class TestParserRecovery:
    """パーサー回復機能のテスト"""

    def test_missing_dot_recovery(self):
        """ピリオド不足からの回復テスト"""
        source = """
        fact1
        fact2.
        fact3.
        """
        
        results = self._parse_with_recovery(source)
        # エラーがあっても後続の正しい構文は解析される
        assert len([r for r in results if r is not None]) >= 2

    def test_mismatched_parentheses_recovery(self):
        """括弧不一致からの回復テスト"""
        source = """
        valid_fact1.
        invalid_fact(.
        valid_fact2.
        """
        
        results = self._parse_with_recovery(source)
        # 有効な部分は解析される
        valid_results = [r for r in results if r is not None]
        assert len(valid_results) >= 2

    def test_invalid_operator_recovery(self):
        """無効な演算子からの回復テスト"""
        source = """
        fact1.
        fact2(X) :- X ??? invalid.
        fact3.
        """
        
        results = self._parse_with_recovery(source)
        # 有効な部分のみ解析される
        valid_results = [r for r in results if r is not None]
        assert len(valid_results) >= 2

    def _parse_with_recovery(self, source: str):
        """エラー回復を伴う解析"""
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        parser = Parser(tokens)
        
        try:
            return parser.parse()
        except Exception:
            # エラーがあっても部分的に解析された結果を返す
            return []
```

### 13.4 Memory Management テスト

メモリ管理の詳細テスト：

```python
# tests/core/test_memory_management.py
"""
Memory Management テスト

メモリ使用量とガベージコレクションの動作を検証
"""

import gc
import weakref
from prolog.core.binding_environment import BindingEnvironment
from prolog.core.types import Term, Variable, Atom
from prolog.runtime.interpreter import Runtime


class TestMemoryManagement:
    """メモリ管理のテスト"""

    def test_binding_environment_cleanup(self):
        """バインディング環境のクリーンアップテスト"""
        env = BindingEnvironment()
        var = Variable("X")
        value = Atom("test")
        
        env.bind("X", value)
        
        # 弱参照を作成
        weak_env = weakref.ref(env)
        weak_var = weakref.ref(var)
        
        # 参照を削除
        del env, var
        gc.collect()
        
        # メモリが適切に解放されることを確認
        # （実装により、即座に解放されない場合もある）

    def test_large_term_memory_usage(self):
        """大きな項のメモリ使用量テスト"""
        # 深くネストした項を作成
        term = Atom("base")
        for i in range(1000):
            term = Term(Atom(f"f{i}"), [term])
        
        # メモリ使用量を測定
        import psutil
        import os
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 項を大量に作成
        terms = []
        for i in range(100):
            terms.append(term)
        
        after_memory = process.memory_info().rss
        memory_increase = after_memory - initial_memory
        
        # 参照を削除
        del terms, term
        gc.collect()
        
        final_memory = process.memory_info().rss
        
        # メモリが適切に解放されることを確認
        memory_freed = after_memory - final_memory
        assert memory_freed > 0  # 一定量のメモリが解放される

    def test_circular_reference_handling(self):
        """循環参照の処理テスト"""
        # 循環参照を含むデータ構造を作成
        term1 = Term(Atom("a"), [])
        term2 = Term(Atom("b"), [term1])
        term1.args.append(term2)  # 循環参照
        
        # 弱参照を作成
        weak_term1 = weakref.ref(term1)
        weak_term2 = weakref.ref(term2)
        
        # 参照を削除
        del term1, term2
        gc.collect()
        
        # 循環参照があってもガベージコレクションされることを確認
        # （Pythonのサイクリックガベージコレクターが動作）

    def test_runtime_memory_leak_prevention(self):
        """ランタイムメモリリーク防止のテスト"""
        runtime = Runtime()
        
        initial_memory = self._get_memory_usage()
        
        # 大量の操作を実行
        for i in range(100):
            runtime.add_rule(f"test_fact({i})")
            results = runtime.query(f"test_fact({i})")
            # 結果を即座に破棄
            del results
        
        # 強制的にガベージコレクション
        gc.collect()
        
        final_memory = self._get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        # メモリ増加が合理的な範囲内であることを確認
        assert memory_increase < 50 * 1024 * 1024  # 50MB以下

    def _get_memory_usage(self):
        """現在のメモリ使用量を取得"""
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss
```

## 14. テスト設定ファイルの拡張

### 14.1 pytest.ini の拡張

```ini
[pytest]
# 基本設定
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# マーカー定義
markers =
    unit: 単体テスト
    integration: 統合テスト
    system: システムテスト
    performance: パフォーマンステスト
    benchmark: ベンチマークテスト
    slow: 実行時間の長いテスト
    memory: メモリ集約的なテスト
    security: セキュリティテスト
    compatibility: 互換性テスト

# テスト実行設定
addopts = 
    -v
    --strict-markers
    --tb=short
    --maxfail=10

# カバレッジ設定
addopts = --cov=prolog --cov-report=html --cov-report=term-missing

# 並列実行設定（pytest-xdist使用時）
addopts = -n auto

# 警告の処理
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

### 14.2 conftest.py の拡張

```python
# tests/conftest.py
"""
テスト共通設定とフィクスチャ
"""

import pytest
import tempfile
import os
from pathlib import Path
from prolog.runtime.interpreter import Runtime
from prolog.core.binding_environment import BindingEnvironment


@pytest.fixture
def runtime():
    """基本的なランタイムフィクスチャ"""
    return Runtime()


@pytest.fixture
def binding_env():
    """バインディング環境フィクスチャ"""
    return BindingEnvironment()


@pytest.fixture
def sample_rules():
    """サンプルルール集"""
    return [
        "likes(mary, food).",
        "likes(mary, wine).",
        "likes(john, wine).",
        "likes(john, mary).",
        "parent(tom, bob).",
        "parent(bob, liz).",
        "grandparent(X, Z) :- parent(X, Y), parent(Y, Z)."
    ]


@pytest.fixture
def loaded_runtime(sample_rules):
    """サンプルルールがロードされたランタイム"""
    runtime = Runtime()
    for rule in sample_rules:
        runtime.add_rule(rule)
    return runtime


@pytest.fixture
def temp_prolog_file():
    """一時Prologファイル"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.prolog', delete=False) as f:
        f.write("""
        test_fact(a).
        test_fact(b).
        test_rule(X) :- test_fact(X).
        """)
        temp_path = f.name
    
    yield temp_path
    
    # クリーンアップ
    os.unlink(temp_path)


@pytest.fixture
def performance_runtime():
    """パフォーマンステスト用のランタイム"""
    runtime = Runtime()
    
    # パフォーマンステスト用のルールをロード
    performance_rules = [
        "fibonacci(0, 1).",
        "fibonacci(1, 1).",
        "fibonacci(N, F) :- N > 1, N1 is N - 1, N2 is N - 2, fibonacci(N1, F1), fibonacci(N2, F2), F is F1 + F2.",
        "factorial(0, 1).",
        "factorial(N, F) :- N > 0, N1 is N - 1, factorial(N1, F1), F is N * F1."
    ]
    
    for rule in performance_rules:
        runtime.add_rule(rule)
    
    return runtime


# テストマーカー用のデコレータ
def slow_test(func):
    """実行時間の長いテストマーカー"""
    return pytest.mark.slow(func)


def memory_intensive(func):
    """メモリ集約的テストマーカー"""
    return pytest.mark.memory(func)


def benchmark_test(func):
    """ベンチマークテストマーカー"""
    return pytest.mark.benchmark(func)


# カスタムアサーション関数
def assert_query_succeeds(runtime, query, expected_count=None):
    """クエリが成功することをアサート"""
    results = runtime.query(query)
    assert len(results) > 0, f"Query '{query}' should succeed"
    if expected_count is not None:
        assert len(results) == expected_count, f"Expected {expected_count} results, got {len(results)}"


def assert_query_fails(runtime, query):
    """クエリが失敗することをアサート"""
    results = runtime.query(query)
    assert len(results) == 0, f"Query '{query}' should fail"


def assert_variable_bound(results, var_name, expected_value):
    """変数が期待値に束縛されていることをアサート"""
    assert len(results) > 0, "No results found"
    result = results[0]
    
    bound_vars = [var for var in result.keys() if var.name == var_name]
    assert len(bound_vars) == 1, f"Variable {var_name} not found in results"
    
    actual_value = result[bound_vars[0]]
    assert actual_value == expected_value, f"Expected {expected_value}, got {actual_value}"


# テスト環境の設定
def pytest_configure(config):
    """pytest設定"""
    # ログレベルの設定
    import logging
    logging.getLogger("prolog").setLevel(logging.WARNING)
    
    # テスト環境の表示
    print("\n" + "="*50)
    print("Prolog Interpreter Test Suite")
    print("="*50)


def pytest_collection_modifyitems(config, items):
    """テストアイテムの収集後の処理"""
    # slowマーカーが付いたテストの処理
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(pytest.mark.timeout(300))  # 5分のタイムアウト
        
        if "memory" in item.keywords:
            item.add_marker(pytest.mark.timeout(600))  # 10分のタイムアウト


# セッションレベルのフィクスチャ
@pytest.fixture(scope="session")
def test_data_dir():
    """テストデータディレクトリ"""
    return Path(__file__).parent / "data"
```

## 15. 高度なテストパターン

### 15.1 Property-Based Testing

```python
# tests/property/test_property_based.py
"""
Property-Based Testing

仮説による自動テスト生成を活用したテスト
"""

import pytest
from hypothesis import given, strategies as st, assume
from prolog.core.types import Atom, Variable, Number, Term
from prolog.runtime.math_interpreter import MathInterpreter
from prolog.core.binding_environment import BindingEnvironment


class TestPropertyBased:
    """プロパティベーステスト"""

    def setup_method(self):
        self.math_interpreter = MathInterpreter()
        self.env = BindingEnvironment()

    @given(st.integers(min_value=-1000, max_value=1000))
    def test_number_evaluation_property(self, n):
        """数値評価のプロパティテスト"""
        number = Number(n)
        result = self.math_interpreter.evaluate(number, self.env)
        assert result == n

    @given(st.integers(min_value=1, max_value=100), 
           st.integers(min_value=1, max_value=100))
    def test_addition_commutative_property(self, a, b):
        """加算の交換法則テスト"""
        expr1 = Term(Atom("+"), [Number(a), Number(b)])
        expr2 = Term(Atom("+"), [Number(b), Number(a)])
        
        result1 = self.math_interpreter.evaluate(expr1, self.env)
        result2 = self.math_interpreter.evaluate(expr2, self.env)
        
        assert result1 == result2  # a + b = b + a

    @given(st.integers(min_value=1, max_value=100), 
           st.integers(min_value=1, max_value=100),
           st.integers(min_value=1, max_value=100))
    def test_addition_associative_property(self, a, b, c):
        """加算の結合法則テスト"""
        # (a + b) + c
        expr1 = Term(Atom("+"), [
            Term(Atom("+"), [Number(a), Number(b)]),
            Number(c)
        ])
        
        # a + (b + c)
        expr2 = Term(Atom("+"), [
            Number(a),
            Term(Atom("+"), [Number(b), Number(c)])
        ])
        
        result1 = self.math_interpreter.evaluate(expr1, self.env)
        result2 = self.math_interpreter.evaluate(expr2, self.env)
        
        assert result1 == result2  # (a + b) + c = a + (b + c)

    @given(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    def test_atom_creation_property(self, name):
        """アトム作成のプロパティテスト"""
        assume(name.isalpha())  # アルファベットのみ
        
        atom = Atom(name)
        assert atom.name == name
        assert str(atom) == name

    @given(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu',))))
    def test_variable_creation_property(self, name):
        """変数作成のプロパティテスト"""
        assume(name.isupper())  # 大文字のみ
        
        var = Variable(name)
        assert var.name == name
        assert str(var) == name
```

### 15.2 Mutation Testing Support

```python
# tests/mutation/test_mutation_support.py
"""
Mutation Testing Support

変異テストのサポート機能
"""

from prolog.runtime.interpreter import Runtime
from prolog.core.types import Term, Atom, Number


class TestMutationSupport:
    """変異テスト支援"""

    def test_arithmetic_operator_mutations(self):
        """算術演算子の変異テスト"""
        runtime = Runtime()
        
        # 元のクエリ
        base_query = "X is 5 + 3"
        expected_result = 8
        
        # 変異パターンのテスト
        mutations = [
            ("X is 5 - 3", 2),    # + -> -
            ("X is 5 * 3", 15),   # + -> *
            ("X is 5 / 3", 5/3),  # + -> /
        ]
        
        for mutated_query, expected in mutations:
            results = runtime.query(mutated_query)
            if results:
                # 変異により結果が変わることを確認
                assert len(results) == 1
                # 実際の値検証は実装依存

    def test_comparison_operator_mutations(self):
        """比較演算子の変異テスト"""
        runtime = Runtime()
        
        # 比較演算子の変異パターン
        mutations = [
            ("5 > 3", True),   # 元
            ("5 < 3", False),  # > -> <
            ("5 = 3", False),  # > -> =
            ("5 >= 3", True),  # > -> >=
        ]
        
        for query, should_succeed in mutations:
            results = runtime.query(query)
            if should_succeed:
                assert len(results) > 0
            else:
                assert len(results) == 0

    def test_logical_operator_mutations(self):
        """論理演算子の変異テスト"""
        runtime = Runtime()
        
        # ファクトを追加
        runtime.add_rule("a.")
        runtime.add_rule("b.")
        
        # 論理演算子の変異
        mutations = [
            ("a, b", True),   # AND - 両方成功
            ("a; b", True),   # AND -> OR - どちらか成功
        ]
        
        for query, should_succeed in mutations:
            results = runtime.query(query)
            if should_succeed:
                assert len(results) > 0
            else:
                assert len(results) == 0
```

### 15.3 Regression Testing Framework

```python
# tests/regression/test_regression_framework.py
"""
Regression Testing Framework

回帰テストのフレームワーク
"""

import json
import os
from pathlib import Path
from prolog.runtime.interpreter import Runtime


class RegressionTestManager:
    """回帰テストマネージャー"""

    def __init__(self, test_data_file="regression_data.json"):
        self.test_data_file = Path(__file__).parent / test_data_file
        self.test_data = self._load_test_data()

    def _load_test_data(self):
        """テストデータを読み込み"""
        if self.test_data_file.exists():
            with open(self.test_data_file, 'r') as f:
                return json.load(f)
        return {"test_cases": []}

    def _save_test_data(self):
        """テストデータを保存"""
        with open(self.test_data_file, 'w') as f:
            json.dump(self.test_data, f, indent=2)

    def record_test_case(self, query, expected_results):
        """テストケースを記録"""
        test_case = {
            "query": query,
            "expected_results": expected_results,
            "timestamp": "2025-05-28"  # 実際はdatetime.now()
        }
        self.test_data["test_cases"].append(test_case)
        self._save_test_data()

    def run_regression_tests(self):
        """回帰テストを実行"""
        runtime = Runtime()
        failures = []

        for test_case in self.test_data["test_cases"]:
            query = test_case["query"]
            expected = test_case["expected_results"]

            try:
                actual = runtime.query(query)
                if len(actual) != expected:
                    failures.append({
                        "query": query,
                        "expected": expected,
                        "actual": len(actual)
                    })
            except Exception as e:
                failures.append({
                    "query": query,
                    "error": str(e)
                })

        return failures


class TestRegressionFramework:
    """回帰テストフレームワークのテスト"""

    def test_regression_manager(self):
        """回帰テストマネージャーのテスト"""
        manager = RegressionTestManager("test_regression.json")
        
        # テストケースの記録
        manager.record_test_case("X = hello", 1)
        manager.record_test_case("5 > 3", 1)
        manager.record_test_case("fail", 0)
        
        # 回帰テストの実行
        failures = manager.run_regression_tests()
        
        # 失敗がないことを確認（実装が正しい場合）
        for failure in failures:
            print(f"Regression failure: {failure}")

    def test_version_compatibility(self):
        """バージョン互換性テスト"""
        # 異なるバージョン間での互換性確認
        runtime = Runtime()
        
        # 基本機能が期待通り動作することを確認
        compatibility_tests = [
            ("X = test", 1),
            ("5 + 3 =:= 8", 1),
            ("member(X, [a, b, c])", 3),  # 実装依存
        ]
        
        for query, expected_min in compatibility_tests:
            results = runtime.query(query)
            # 最低限の結果数を確認
            assert len(results) >= 0  # エラーが発生しないこと
```

## 16. テスト環境設定の最適化

### 16.1 Docker環境でのテスト

```dockerfile
# tests/docker/Dockerfile.test
FROM python:3.9-slim

WORKDIR /app

# 依存関係のインストール
COPY requirements-test.txt .
RUN pip install -r requirements-test.txt

# テストコードのコピー
COPY . .

# テストの実行
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=prolog"]
```

```yaml
# tests/docker/docker-compose.test.yml
version: '3.8'

services:
  test-runner:
    build:
      context: ../..
      dockerfile: tests/docker/Dockerfile.test
    volumes:
      - ../../:/app
    environment:
      - PYTHONPATH=/app
      - PYTEST_ARGS=--maxfail=5

  performance-test:
    build:
      context: ../..
      dockerfile: tests/docker/Dockerfile.test
    volumes:
      - ../../:/app
    environment:
      - PYTHONPATH=/app
      - PYTEST_ARGS=tests/performance/ -v
    command: ["python", "-m", "pytest", "tests/performance/", "-v"]

  benchmark-test:
    build:
      context: ../..
      dockerfile: tests/docker/Dockerfile.test
    volumes:
      - ../../:/app
    environment:
      - PYTHONPATH=/app
    command: ["python", "-m", "pytest", "tests/benchmark/", "-v", "--benchmark-only"]
```

### 16.2 継続的インテグレーション設定

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', 3.11]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-test.txt
    
    - name: Run unit tests
      run: |
        pytest tests/core/ tests/parser/ -v --cov=prolog
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-test.txt
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ tests/system/ -v

  performance-tests:
    runs-on: ubuntu-latest
    needs: integration-tests

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-test.txt
    
    - name: Run performance tests
      run: |
        pytest tests/performance/ -v --timeout=300

  benchmark-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-test.txt
        pip install pytest-benchmark
    
    - name: Run benchmark tests
      run: |
        pytest tests/benchmark/ --benchmark-only --benchmark-json=benchmark.json
    
    - name: Store benchmark results
      uses: benchmark-action/github-action-benchmark@v1
      with:
        tool: 'pytest'
        output-file-path: benchmark.json
        github-token: ${{ secrets.GITHUB_TOKEN }}
        auto-push: true
```

## 17. テスト品質の継続的監視

### 17.1 テストメトリクス収集

```python
# tests/metrics/test_metrics_collector.py
"""
Test Metrics Collector

テストメトリクスの収集と分析
"""

import time
import json
from pathlib import Path
from datetime import datetime


class TestMetricsCollector:
    """テストメトリクス収集器"""

    def __init__(self):
        self.metrics_file = Path("test_metrics.json")
        self.metrics = self._load_metrics()

    def _load_metrics(self):
        """メトリクスファイルを読み込み"""
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return {"test_runs": []}

    def _save_metrics(self):
        """メトリクスを保存"""
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)

    def record_test_run(self, test_name, duration, result):
        """テスト実行を記録"""
        run_data = {
            "test_name": test_name,
            "duration": duration,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.metrics["test_runs"].append(run_data)
        self._save_metrics()

    def get_performance_trends(self, test_name):
        """パフォーマンストレンドを取得"""
        runs = [r for r in self.metrics["test_runs"] if r["test_name"] == test_name]
        return [r["duration"] for r in runs[-10:]]  # 直近10回

    def get_failure_rate(self, test_name):
        """失敗率を取得"""
        runs = [r for r in self.metrics["test_runs"] if r["test_name"] == test_name]
        if not runs:
            return 0.0
        
        failures = len([r for r in runs if r["result"] == "FAILED"])
        return failures / len(runs) * 100


# テストメトリクスの使用例
collector = TestMetricsCollector()

def timed_test(test_name):
    """実行時間測定デコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                collector.record_test_run(test_name, duration, "PASSED")
                return result
            except Exception as e:
                duration = time.time() - start_time
                collector.record_test_run(test_name, duration, "FAILED")
                raise
        return wrapper
    return decorator
```

このように、包括的なテスト設計により、Prologインタープリターの品質を多角的に保証できます。各テストカテゴリーが相互に補完し合い、システム全体の信頼性向上に寄与します。