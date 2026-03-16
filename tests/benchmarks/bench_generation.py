"""
Benchmark: CUPP v2 generation speed.
Run with: python -m pytest tests/benchmarks/ -v -s
"""
import time
import pytest
from cupp.core.profile import Profile, DateInfo
from cupp.config.loader import load_config, merge_config
from cupp.core.engine import Engine

BENCHMARK_PROFILE = Profile(
    name="john",
    surname="doe",
    nickname="johnny",
    birthdate=DateInfo(day=15, month=6, year=1990),
    partner_name="jane",
    pet_name="rex",
    company="acme",
    keywords=["test", "secure"],
)


def _run_engine(use_rust: bool, limit: int = 50_000) -> dict:
    cfg = load_config()
    cfg = merge_config(cfg, {"generation": {"use_rust_engine": use_rust, "max_depth": 3}})
    engine = Engine(config=cfg)

    start = time.perf_counter()
    count = 0
    for _ in engine.generate(BENCHMARK_PROFILE):
        count += 1
        if count >= limit:
            break
    elapsed = time.perf_counter() - start
    return {"count": count, "elapsed": elapsed, "speed": count / elapsed}


def test_python_only_benchmark(capsys):
    result = _run_engine(use_rust=False)
    with capsys.disabled():
        print(
            f"\n[Python only]  {result['count']:,} passwords in "
            f"{result['elapsed']:.3f}s = {result['speed']:,.0f} pass/s"
        )
    assert result["count"] > 0


def test_rust_engine_benchmark(capsys):
    result = _run_engine(use_rust=True)
    with capsys.disabled():
        print(
            f"\n[Python+Rust]  {result['count']:,} passwords in "
            f"{result['elapsed']:.3f}s = {result['speed']:,.0f} pass/s"
        )
    assert result["count"] > 0
