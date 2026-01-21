import pytest
import os
import sys
from pyprolog.runtime.interpreter import Runtime
from pyprolog.core.types import Variable

# ベンチマークファイルのパスを取得
BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))

def get_benchmark_path(filename):
    return os.path.join(BENCHMARK_DIR, filename)

def run_query(runtime, query):
    """クエリを実行し、結果のリストを返すヘルパー関数"""
    return list(runtime.query(query))

@pytest.fixture
def runtime():
    """Runtimeインスタンスを作成するフィクスチャ"""
    return Runtime()

def test_crypt(benchmark, runtime):
    """crypt.pl (SEND+MORE=MONEY) のベンチマーク"""
    sys.stderr.write("\n[Benchmark] Starting crypt (SEND+MORE=MONEY)...\n")
    sys.stderr.flush()
    
    runtime.consult(get_benchmark_path("crypt.pl"))
    
    # solve述語を直接呼び出して計測
    def run_crypt():
        return run_query(runtime, "solve(S, E, N, D, M, O, R, Y).")

    result = benchmark(run_crypt)
    assert len(result) >= 1

def test_nrev(benchmark, runtime):
    """nrev.pl (Naive Reverse) のベンチマーク"""
    sys.stderr.write("\n[Benchmark] Starting nrev (Naive Reverse list=30)...")
    sys.stderr.flush()
    
    runtime.consult(get_benchmark_path("nrev.pl"))
    
    # リスト長 30 で実行
    def run_nrev():
        return run_query(runtime, "benchmark(30).")

    result = benchmark(run_nrev)
    assert len(result) >= 1

def test_primes(benchmark, runtime):
    """primes.pl (素数生成) のベンチマーク"""
    sys.stderr.write("\n[Benchmark] Starting primes (Sieve limit=100)...")
    sys.stderr.flush()
    
    runtime.consult(get_benchmark_path("primes.pl"))
    
    # 100までの素数を生成
    def run_primes():
        return run_query(runtime, "benchmark(100).")

    result = benchmark(run_primes)
    assert len(result) >= 1

def test_queens(benchmark, runtime):
    """queens.pl (N-Queens) のベンチマーク"""
    sys.stderr.write("\n[Benchmark] Starting queens (8-Queens)...")
    sys.stderr.flush()
    
    runtime.consult(get_benchmark_path("queens.pl"))
    
    # 8-Queens問題を解く
    def run_queens():
        # 全解探索ではなく最初の解を見つける
        return run_query(runtime, "solve_queens(8, Solution).")

    result = benchmark(run_queens)
    assert len(result) >= 1

def test_tak(benchmark, runtime):
    """tak.pl (竹内関数) のベンチマーク"""
    sys.stderr.write("\n[Benchmark] Starting tak (Tak function 18,12,6)...")
    sys.stderr.flush()
    
    runtime.consult(get_benchmark_path("tak.pl"))
    
    # tak(18, 12, 6, R) を実行
    def run_tak():
        return run_query(runtime, "tak(18, 12, 6, R).")

    result = benchmark(run_tak)
    assert len(result) >= 1
    # 結果の検証 (tak(18, 12, 6) = 7)
    assert result[0][Variable('R')].value == 7