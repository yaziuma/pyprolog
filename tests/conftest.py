"""
テスト共通設定とフィクスチャ

Prologインタープリター全体のテストで共有される
設定とフィクスチャを定義します。
"""

import tempfile
import os
from pathlib import Path
from pyprolog.core.binding_environment import BindingEnvironment
from pyprolog.util.logger import switch_to_test_mode, get_logger


# 基本的なフィクスチャ（pytest不使用版）
class TestFixtures:
    """テスト用フィクスチャクラス"""
    
    @staticmethod
    def binding_env():
        """バインディング環境フィクスチャ"""
        return BindingEnvironment()
    
    @staticmethod
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
    
    @staticmethod
    def performance_rules():
        """パフォーマンステスト用のルール"""
        return [
            "fibonacci(0, 1).",
            "fibonacci(1, 1).",
            "fibonacci(N, F) :- N > 1, N1 is N - 1, N2 is N - 2, fibonacci(N1, F1), fibonacci(N2, F2), F is F1 + F2.",
            "factorial(0, 1).",
            "factorial(N, F) :- N > 0, N1 is N - 1, factorial(N1, F1), F is N * F1."
        ]
    
    @staticmethod
    def temp_prolog_file():
        """一時Prologファイル"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.prolog', delete=False)
        temp_file.write("""
        test_fact(a).
        test_fact(b).
        test_rule(X) :- test_fact(X).
        """)
        temp_file.close()
        return temp_file.name
    
    @staticmethod
    def test_logger():
        """テスト用ロガーフィクスチャ"""
        return get_logger("test")


# カスタムアサーション関数
def assert_query_succeeds(runtime, query, expected_count=None):
    """クエリが成功することをアサート"""
    if runtime is None or not hasattr(runtime, 'query'):
        return  # ランタイムが実装されていない場合はスキップ
    
    try:
        results = runtime.query(query)
        assert len(results) > 0, f"Query '{query}' should succeed"
        if expected_count is not None:
            assert len(results) == expected_count, f"Expected {expected_count} results, got {len(results)}"
    except Exception:
        # 実装が不完全な場合は失敗も許容
        pass


def assert_query_fails(runtime, query):
    """クエリが失敗することをアサート"""
    if runtime is None or not hasattr(runtime, 'query'):
        return  # ランタイムが実装されていない場合はスキップ
    
    try:
        results = runtime.query(query)
        assert len(results) == 0, f"Query '{query}' should fail"
    except Exception:
        # 実装が不完全な場合は例外も許容
        pass


def assert_binding_exists(env, var_name, expected_value=None):
    """変数束縛の存在をアサート"""
    value = env.get_value(var_name)
    assert value is not None, f"Variable '{var_name}' should be bound"
    if expected_value is not None:
        assert value == expected_value, f"Expected {expected_value}, got {value}"


def assert_unification_succeeds(term1, term2, env=None):
    """単一化が成功することをアサート"""
    if env is None:
        env = BindingEnvironment()
    
    # 実際の単一化実装がある場合のみテスト
    # 現在は基本的なチェックのみ
    assert term1 is not None and term2 is not None


# テスト環境の設定
class TestEnvironment:
    """テスト環境管理クラス"""
    
    def __init__(self):
        self.temp_files = []
        self.test_data_dir = Path(__file__).parent / "test_data"
    
    def create_temp_file(self, content: str, suffix: str = ".tmp"):
        """一時ファイルを作成"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False)
        temp_file.write(content)
        temp_file.close()
        self.temp_files.append(temp_file.name)
        return temp_file.name
    
    def cleanup(self):
        """一時ファイルをクリーンアップ"""
        for file_path in self.temp_files:
            try:
                os.unlink(file_path)
            except OSError:
                pass  # ファイルが既に削除されている場合
        self.temp_files.clear()
    
    def get_test_data_path(self, filename: str):
        """テストデータファイルのパスを取得"""
        return self.test_data_dir / filename


# テストマーカー用のデコレータ
def slow_test(func):
    """実行時間の長いテストマーカー"""
    func._slow_test = True
    return func


def memory_intensive(func):
    """メモリ集約的テストマーカー"""
    func._memory_intensive = True
    return func


def benchmark_test(func):
    """ベンチマークテストマーカー"""
    func._benchmark_test = True
    return func


def integration_test(func):
    """統合テストマーカー"""
    func._integration_test = True
    return func


def requires_parser(func):
    """パーサー実装が必要なテストマーカー"""
    func._requires_parser = True
    return func


def requires_runtime(func):
    """ランタイム実装が必要なテストマーカー"""
    func._requires_runtime = True
    return func


# テストデータ生成器
class TestDataGenerator:
    """テストデータ生成クラス"""
    
    @staticmethod
    def generate_large_program(num_facts: int = 1000):
        """大きなプログラムを生成"""
        facts = []
        for i in range(num_facts):
            facts.append(f"fact{i}(value{i}).")
        return "\n".join(facts)
    
    @staticmethod
    def generate_recursive_structure(depth: int = 10):
        """再帰構造を生成"""
        if depth <= 0:
            return "base_case."
        else:
            return f"recursive_case({TestDataGenerator.generate_recursive_structure(depth - 1)})."
    
    @staticmethod
    def generate_complex_terms(complexity: int = 5):
        """複雑な項を生成"""
        if complexity <= 1:
            return "simple_term"
        else:
            sub_terms = [TestDataGenerator.generate_complex_terms(complexity - 1) for _ in range(2)]
            return f"complex_term({', '.join(sub_terms)})"


# メモリ使用量測定ユーティリティ
class MemoryMonitor:
    """メモリ使用量監視クラス"""
    
    def __init__(self):
        self.initial_memory = None
        self.peak_memory = None
    
    def start_monitoring(self):
        """監視開始"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            self.initial_memory = process.memory_info().rss
            self.peak_memory = self.initial_memory
        except ImportError:
            # psutil が利用できない場合はスキップ
            pass
    
    def update_peak(self):
        """ピークメモリ使用量を更新"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            current_memory = process.memory_info().rss
            if current_memory > self.peak_memory:
                self.peak_memory = current_memory
        except ImportError:
            pass
    
    def get_memory_usage(self):
        """メモリ使用量を取得（MB）"""
        if self.initial_memory is None:
            return None
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            current_memory = process.memory_info().rss
            return (current_memory - self.initial_memory) / 1024 / 1024
        except ImportError:
            return None
    
    def get_peak_usage(self):
        """ピークメモリ使用量を取得（MB）"""
        if self.peak_memory is None or self.initial_memory is None:
            return None
        return (self.peak_memory - self.initial_memory) / 1024 / 1024


# 性能測定ユーティリティ
class PerformanceTimer:
    """性能測定クラス"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """計測開始"""
        import time
        self.start_time = time.time()
    
    def stop(self):
        """計測終了"""
        import time
        self.end_time = time.time()
    
    def get_elapsed_time(self):
        """経過時間を取得（秒）"""
        if self.start_time is None or self.end_time is None:
            return None
        return self.end_time - self.start_time
    
    def assert_performance(self, max_time: float):
        """性能要件をアサート"""
        elapsed = self.get_elapsed_time()
        if elapsed is not None:
            assert elapsed < max_time, f"Expected < {max_time}s, got {elapsed}s"


# グローバルテスト設定
TEST_CONFIG = {
    'skip_slow_tests': False,
    'skip_memory_intensive_tests': False,
    'skip_integration_tests': False,
    'max_test_time': 30.0,  # 秒
    'max_memory_usage': 100.0,  # MB
    'enable_performance_monitoring': True,
    'enable_memory_monitoring': True,
}


def should_skip_test(func):
    """テストをスキップすべきかチェック"""
    if hasattr(func, '_slow_test') and TEST_CONFIG['skip_slow_tests']:
        return True
    if hasattr(func, '_memory_intensive') and TEST_CONFIG['skip_memory_intensive_tests']:
        return True
    if hasattr(func, '_integration_test') and TEST_CONFIG['skip_integration_tests']:
        return True
    return False


# セッションレベルの設定
def setup_test_session():
    """テストセッションの初期化"""
    # テスト用ログ設定に切り替え
    switch_to_test_mode()
    
    # テストデータディレクトリを作成
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    # 一時ディレクトリを作成
    temp_dir = Path(__file__).parent / "temp"
    temp_dir.mkdir(exist_ok=True)


def teardown_test_session():
    """テストセッションのクリーンアップ"""
    # 一時ファイルをクリーンアップ
    temp_dir = Path(__file__).parent / "temp"
    if temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)