import tempfile
from pathlib import Path
from cupp.core.engine import Engine
from cupp.core.profile import Profile, DateInfo
from cupp.config.loader import load_config, merge_config


def test_engine_generate_to_file():
    profile = Profile(name="test", keywords=["demo"])
    cfg = load_config()
    cfg = merge_config(cfg, {
        "generation": {"max_depth": 1, "use_rust_engine": False},
        "mutations": {
            "leet": {"enabled": False},
            "append": {"numbers_range": [0, 0], "symbols": [], "years": False},
        },
        "filters": {"min_length": 4, "max_length": 10, "dedup": False},
    })
    engine = Engine(config=cfg)

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        out = Path(f.name)

    stats = engine.generate_to_file(profile, out)
    assert stats.total_generated > 0
    assert out.exists()
    lines = out.read_text().strip().split("\n")
    assert len(lines) == stats.total_generated
    out.unlink()


def test_engine_rust_availability():
    engine = Engine()
    # Should not raise regardless of whether Rust is compiled
    available = engine.rust_available()
    assert isinstance(available, bool)
