import tempfile
from pathlib import Path

import pytest

from credweaver.config.loader import load_config, merge_config
from credweaver.core.engine import Engine
from credweaver.core.profile import Profile


@pytest.fixture
def engine_no_rust():
    cfg = load_config()
    cfg = merge_config(
        cfg,
        {
            "generation": {"use_rust_engine": False, "max_depth": 2},
            "mutations": {
                "leet": {"level": 1},
                "case": {"modes": ["lower"]},
                "append": {"numbers_range": [0, 0], "symbols": [], "years": False},
            },
            "filters": {"min_length": 4, "max_length": 12, "dedup": True},
        },
    )
    return Engine(config=cfg)


def test_engine_generates_non_empty(engine_no_rust, sample_profile):
    results = list(engine_no_rust.generate(sample_profile))
    assert len(results) > 0


def test_engine_output_respects_length(engine_no_rust, sample_profile):
    for p in engine_no_rust.generate(sample_profile):
        assert 4 <= len(p) <= 12


def test_engine_dedup(engine_no_rust, sample_profile):
    results = list(engine_no_rust.generate(sample_profile))
    assert len(results) == len(set(results))


def test_engine_generate_to_file(engine_no_rust, sample_profile):
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        out = Path(f.name)
    stats = engine_no_rust.generate_to_file(sample_profile, out)
    assert out.exists()
    assert stats.total_generated > 0
    lines = out.read_text().strip().split("\n")
    assert len(lines) == stats.total_generated
    out.unlink()


def test_engine_empty_profile_generates_common_passwords():
    cfg = load_config()
    cfg = merge_config(
        cfg,
        {
            "generation": {"use_rust_engine": False, "max_depth": 1},
            "mutations": {
                "leet": {"enabled": False},
                "case": {"modes": ["lower"]},
                "append": {"numbers": False, "symbols": [], "years": False},
            },
            "filters": {"dedup": False},
            "strategies": {"enabled": ["common_passwords", "keyboard_patterns"]},
        },
    )
    engine = Engine(config=cfg)
    results = list(engine.generate(Profile()))
    assert len(results) > 0  # keyboard patterns + common passwords


def test_engine_preset_aggressive_generates_more_than_default(sample_profile):
    def count_with_preset(preset_overrides):
        cfg = load_config()
        cfg = merge_config(
            cfg,
            {
                **preset_overrides,
                "generation": {**preset_overrides.get("generation", {}), "use_rust_engine": False},
            },
        )
        engine = Engine(config=cfg)
        return sum(1 for _ in zip(range(10_000), engine.generate(sample_profile)))

    default_count = count_with_preset({})
    aggressive_count = count_with_preset(
        {
            "mutations": {
                "leet": {"level": 3},
                "case": {"modes": ["lower", "upper", "title", "toggle"]},
                "append": {"numbers_range": [0, 999], "symbols": ["!", "@", "123"]},
            }
        }
    )
    assert aggressive_count >= default_count
