import logging
import os
import sys

import pytest
from pyprolog.runtime.interpreter import Runtime
from pyprolog.core.types import Variable

BENCHMARK_DIR = os.path.dirname(os.path.abspath(__file__))

def get_benchmark_path(filename):
    return os.path.join(BENCHMARK_DIR, filename)

def run_query(runtime, query):
    return list(runtime.query(query))


def _run_benchmark(benchmark, runtime, label, filename, query):
    """共通ベンチマーク実行"""
    message_start = f"[Benchmark] Starting {label}"
    sys.stderr.write(f"\n{message_start}...")
    sys.stderr.flush()
    logging.getLogger("prolog").info(message_start)
    runtime.consult(get_benchmark_path(filename))
    result = benchmark(lambda: run_query(runtime, query))
    assert len(result) >= 1
    message_done = f"[Benchmark] Finished {label}"
    sys.stderr.write(f"\n{message_done}")
    sys.stderr.flush()
    logging.getLogger("prolog").info(message_done)
    return result

@pytest.fixture
def runtime():
    return Runtime()


@pytest.fixture
def runtime_iterative():
    """Runtime with iterative execution enabled."""
    rt = Runtime()
    rt.use_iterative_execution = True
    return rt

# -----------------------
# Heavy benchmarks
# -----------------------

@pytest.mark.info_log
@pytest.mark.bench_heavy
def test_crypt(benchmark, runtime):
    """crypt.pl (SEND+MORE=MONEY)"""
    _run_benchmark(
        benchmark,
        runtime,
        "crypt (SEND+MORE=MONEY)",
        "crypt.pl",
        "solve(S, E, N, D, M, O, R, Y).",
    )


@pytest.mark.info_log
@pytest.mark.bench_heavy
def test_queens_heavy(benchmark, runtime):
    """queens.pl (N-Queens heavy)"""
    _run_benchmark(
        benchmark,
        runtime,
        "queens (12-Queens)",
        "queens.pl",
        "solve_queens(12, Solution).",
    )


@pytest.mark.info_log
@pytest.mark.bench_heavy
def test_tak_heavy(benchmark, runtime):
    """tak.pl (Takeuchi function heavy)"""
    _run_benchmark(
        benchmark,
        runtime,
        "tak (21,12,6)",
        "tak.pl",
        "tak(21, 12, 6, R).",
    )


@pytest.mark.info_log
@pytest.mark.bench_heavy
def test_nrev_heavy(benchmark, runtime):
    """nrev.pl (Naive Reverse heavy)"""
    _run_benchmark(
        benchmark,
        runtime,
        "nrev (list=300)",
        "nrev.pl",
        "benchmark(300).",
    )


@pytest.mark.info_log
@pytest.mark.bench_heavy
def test_primes_heavy(benchmark, runtime):
    """primes.pl (Sieve heavy)"""
    _run_benchmark(
        benchmark,
        runtime,
        "primes (limit=10000)",
        "primes.pl",
        "benchmark(10000).",
    )


# -----------------------
# Medium benchmarks
# -----------------------

@pytest.mark.info_log
@pytest.mark.bench_medium
def test_queens_medium(benchmark, runtime):
    """queens.pl (N-Queens medium)"""
    _run_benchmark(
        benchmark,
        runtime,
        "queens (10-Queens)",
        "queens.pl",
        "solve_queens(10, Solution).",
    )


@pytest.mark.info_log
@pytest.mark.bench_medium
def test_nrev_medium(benchmark, runtime):
    """nrev.pl (Naive Reverse medium)"""
    _run_benchmark(
        benchmark,
        runtime,
        "nrev (list=150)",
        "nrev.pl",
        "benchmark(150).",
    )


@pytest.mark.info_log
@pytest.mark.bench_medium
def test_primes_medium(benchmark, runtime):
    """primes.pl (Sieve medium)"""
    _run_benchmark(
        benchmark,
        runtime,
        "primes (limit=1000)",
        "primes.pl",
        "benchmark(1000).",
    )


@pytest.mark.info_log
@pytest.mark.bench_medium
def test_tak_medium(benchmark, runtime):
    """tak.pl (Takeuchi function medium)"""
    _run_benchmark(
        benchmark,
        runtime,
        "tak (18,12,6)",
        "tak.pl",
        "tak(18, 12, 6, R).",
    )


# -----------------------
# Light benchmarks
# -----------------------

@pytest.mark.info_log
@pytest.mark.bench_light
def test_queens_light(benchmark, runtime):
    """queens.pl (N-Queens light)"""
    _run_benchmark(
        benchmark,
        runtime,
        "queens (8-Queens)",
        "queens.pl",
        "solve_queens(8, Solution).",
    )

@pytest.mark.info_log
@pytest.mark.bench_light
def test_mini_crypt_light(benchmark, runtime):
    """mini_crypt.pl (I + BB = ILL)"""
    _run_benchmark(
        benchmark,
        runtime,
        "mini_crypt (I + BB = ILL)",
        "mini_crypt.pl",
        "solve(I, B, L).",
    )

@pytest.mark.info_log
@pytest.mark.bench_light
def test_nrev_light(benchmark, runtime):
    """nrev.pl (Naive Reverse light)"""
    _run_benchmark(
        benchmark,
        runtime,
        "nrev (list=30)",
        "nrev.pl",
        "benchmark(30).",
    )


@pytest.mark.info_log
@pytest.mark.bench_light
def test_primes_light(benchmark, runtime):
    """primes.pl (Sieve light)"""
    _run_benchmark(
        benchmark,
        runtime,
        "primes (limit=100)",
        "primes.pl",
        "benchmark(100).",
    )

@pytest.mark.info_log
@pytest.mark.bench_light
def test_tak_light(benchmark, runtime):
    """tak.pl (Takeuchi function light)"""
    result = _run_benchmark(
        benchmark,
        runtime,
        "tak (14,12,6)",
        "tak.pl",
        "tak(14, 12, 6, R).",
    )
    assert result[0][Variable("R")].value == 7


@pytest.mark.info_log
@pytest.mark.bench_light
def test_recursion_depth_light(benchmark, runtime):
    """recursion_depth.pl (Simple recursion light)"""
    _run_benchmark(
        benchmark,
        runtime,
        "recursion_depth (N=100)",
        "recursion_depth.pl",
        "benchmark(100).",
    )


# -----------------------
# Recursion depth tests (for iterative execution)
# -----------------------

@pytest.mark.info_log
@pytest.mark.bench_medium
def test_recursion_depth_medium(benchmark, runtime_iterative):
    """recursion_depth.pl (Simple recursion medium) - Uses iterative execution"""
    _run_benchmark(
        benchmark,
        runtime_iterative,
        "recursion_depth (N=500)",
        "recursion_depth.pl",
        "benchmark(500).",
    )


@pytest.mark.info_log
@pytest.mark.bench_heavy
def test_recursion_depth_heavy(benchmark, runtime_iterative):
    """recursion_depth.pl (Simple recursion heavy) - Uses iterative execution"""
    _run_benchmark(
        benchmark,
        runtime_iterative,
        "recursion_depth (N=1000)",
        "recursion_depth.pl",
        "benchmark(1000).",
    )
