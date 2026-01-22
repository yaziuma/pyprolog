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
