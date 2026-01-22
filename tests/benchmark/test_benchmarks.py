import pytest
import os
import sys
from pyprolog.runtime.interpreter import Runtime
from pyprolog.core.types import Variable

BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))

def get_benchmark_path(filename):
    return os.path.join(BENCHMARK_DIR, filename)

def run_query(runtime, query):
    return list(runtime.query(query))

@pytest.fixture
def runtime():
    return Runtime()

# -----------------------
# Heavy benchmarks
# -----------------------

@pytest.mark.info_log
@pytest.mark.bench_heavy
def test_crypt(benchmark, runtime):
    """crypt.pl (SEND+MORE=MONEY)"""
    sys.stderr.write("\n[Benchmark] Starting crypt (SEND+MORE=MONEY)...\n")
    sys.stderr.flush()

    runtime.consult(get_benchmark_path("crypt.pl"))

    def run_crypt():
        return run_query(runtime, "solve(S, E, N, D, M, O, R, Y).")

    result = benchmark(run_crypt)
    assert len(result) >= 1

@pytest.mark.info_log
@pytest.mark.bench_heavy
def test_queens(benchmark, runtime):
    """queens.pl (N-Queens)"""
    sys.stderr.write("\n[Benchmark] Starting queens (8-Queens)...")
    sys.stderr.flush()

    runtime.consult(get_benchmark_path("queens.pl"))

    def run_queens():
        return run_query(runtime, "solve_queens(8, Solution).")

    result = benchmark(run_queens)
    assert len(result) >= 1

@pytest.mark.info_log
@pytest.mark.bench_heavy
def test_tak(benchmark, runtime):
    """tak.pl (Takeuchi function)"""
    sys.stderr.write("\n[Benchmark] Starting tak (Tak function 18,12,6)...")
    sys.stderr.flush()

    runtime.consult(get_benchmark_path("tak.pl"))

    def run_tak():
        return run_query(runtime, "tak(18, 12, 6, R).")

    result = benchmark(run_tak)
    assert len(result) >= 1
    assert result[0][Variable("R")].value == 7

# -----------------------
# Light benchmarks
# -----------------------

@pytest.mark.info_log
@pytest.mark.bench_light
def test_nrev(benchmark, runtime):
    """nrev.pl (Naive Reverse)"""
    sys.stderr.write("\n[Benchmark] Starting nrev (Naive Reverse list=30)...")
    sys.stderr.flush()

    runtime.consult(get_benchmark_path("nrev.pl"))

    def run_nrev():
        return run_query(runtime, "benchmark(30).")

    result = benchmark(run_nrev)
    assert len(result) >= 1

@pytest.mark.info_log
@pytest.mark.bench_light
def test_primes(benchmark, runtime):
    """primes.pl (Sieve)"""
    sys.stderr.write("\n[Benchmark] Starting primes (Sieve limit=100)...")
    sys.stderr.flush()

    runtime.consult(get_benchmark_path("primes.pl"))

    def run_primes():
        return run_query(runtime, "benchmark(100).")

    result = benchmark(run_primes)
    assert len(result) >= 1
